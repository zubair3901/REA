"""Optional hosted Stripe checkout. Never handles card numbers.
Availability of Google Pay and local methods depends on the approved merchant account.
"""
import hashlib,hmac,json,os,time
import httpx
from fastapi import APIRouter,Depends,HTTPException,Request
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from .database import get_db
from .workspace import current_customer,project_access,audit
from .workspace_models import PaymentRequest,Project,GatewayEvent
router=APIRouter(prefix='/api/payments')
@router.get('/methods')
def methods():
    return {'card_configured':bool(os.getenv('STRIPE_SECRET_KEY')),'bank_transfer_configured':bool(os.getenv('PAYMENT_INSTRUCTIONS')),'google_pay':'Available only through a supported, approved merchant account and compatible device; not guaranteed','local_wallets':'Requires a local merchant provider integration; not connected'}
@router.post('/{payment_id}/card')
async def checkout(payment_id:str,user=Depends(current_customer),db=Depends(get_db)):
    payment=db.get(PaymentRequest,payment_id)
    if not payment or payment.customer_id!=user.id:raise HTTPException(404,'Payment request not found')
    project_access(db,payment.project_id,user)
    if payment.status not in ('awaiting_payment','submitted'):raise HTTPException(409,'Payment already decided')
    secret=os.getenv('STRIPE_SECRET_KEY','');base=os.getenv('APP_URL','')
    if not secret or not base.startswith('https://'):raise HTTPException(503,'Hosted card payment is not configured')
    if os.getenv('APP_ENV','development')!='production' and not secret.startswith('sk_test_'):raise HTTPException(503,'Only payment test credentials are allowed on staging')
    fields={'mode':'payment','success_url':base+'/?payment=returned','cancel_url':base+'/?payment=cancelled','client_reference_id':payment.id,'metadata[payment_id]':payment.id,'line_items[0][price_data][currency]':'usd','line_items[0][price_data][unit_amount]':str(int(payment.amount*100)),'line_items[0][price_data][product_data][name]':'Roomform '+payment.package+' project package','line_items[0][quantity]':'1','payment_method_types[0]':'card'}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response=await client.post('https://api.stripe.com/v1/checkout/sessions',data=fields,headers={'Authorization':'Bearer '+secret,'Idempotency-Key':'roomform-'+payment.id})
        response.raise_for_status();data=response.json()
        if not data.get('url','').startswith('https://checkout.stripe.com/'):raise ValueError()
    except (httpx.HTTPError,ValueError):raise HTTPException(502,'Could not open payment checkout. No payment has been confirmed.')
    return {'url':data['url'],'payment_confirmed':False}
@router.post('/stripe/webhook')
async def webhook(request:Request,db=Depends(get_db)):
    raw=await request.body()
    if len(raw)>1024*1024:raise HTTPException(413,'Event too large')
    secret=os.getenv('STRIPE_WEBHOOK_SECRET','')
    if not secret:raise HTTPException(503,'Webhook verification is not configured')
    parts=request.headers.get('stripe-signature','').split(',');values={}
    for part in parts:
        key,sep,value=part.partition('=')
        if sep:values.setdefault(key,[]).append(value)
    try:timestamp=int(values['t'][0])
    except (KeyError,ValueError):raise HTTPException(400,'Invalid signature')
    expected=hmac.new(secret.encode(),str(timestamp).encode()+b'.'+raw,hashlib.sha256).hexdigest()
    if abs(time.time()-timestamp)>300 or not any(hmac.compare_digest(expected,v) for v in values.get('v1',[])):raise HTTPException(400,'Invalid signature')
    try:event=json.loads(raw)
    except ValueError:raise HTTPException(400,'Invalid event')
    if event.get('type')!='checkout.session.completed':return {'received':True}
    obj=event.get('data',{}).get('object',{});payment_id=obj.get('metadata',{}).get('payment_id');payment=db.get(PaymentRequest,payment_id) if payment_id else None
    if not payment or obj.get('payment_status')!='paid' or obj.get('currency')!='usd' or obj.get('amount_total')!=int(payment.amount*100):raise HTTPException(400,'Payment does not match the recorded amount and currency')
    if os.getenv('APP_ENV','development')!='production' and event.get('livemode'):raise HTTPException(400,'Live payments are not accepted on staging')
    event_id=event.get('id')
    if not isinstance(event_id,str) or len(event_id)>200:raise HTTPException(400,'Invalid event ID')
    if db.get(GatewayEvent,event_id):return {'received':True}
    db.add(GatewayEvent(id=event_id,payment_id=payment.id))
    try:
        db.flush()
        changed=db.execute(update(PaymentRequest).where(PaymentRequest.id==payment.id,PaymentRequest.status.in_(['awaiting_payment','submitted'])).values(status='approved'))
        if changed.rowcount==1:
            db.execute(update(Project).where(Project.id==payment.project_id).values(credits=Project.credits+payment.credits))
            audit(db,'stripe','payment.approved',payment.id,{'event_id':event_id})
        db.commit()
    except IntegrityError:db.rollback()
    return {'received':True}
