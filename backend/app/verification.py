import os,secrets,hashlib,time
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select
from .database import get_db
from .workspace_models import EmailVerification,MailQueue
from .workspace import current_customer,uid
router=APIRouter(prefix='/api/workspace')
@router.post('/verification/send')
def send(user=Depends(current_customer),db=Depends(get_db)):
    if not all(os.getenv(k) for k in ('SMTP_HOST','SMTP_FROM','APP_URL')):raise HTTPException(503,'Verification email service is not configured')
    token=secrets.token_urlsafe(32)
    row=db.get(EmailVerification,user.id)
    if row and row.verified_at:return {'verified':True}
    if row and row.expires_at>int(time.time())+3300:raise HTTPException(429,'Wait five minutes before requesting another verification email')
    if not row:row=EmailVerification(customer_id=user.id,token_hash='',expires_at=0);db.add(row)
    row.token_hash=hashlib.sha256(token.encode()).hexdigest();row.expires_at=int(time.time())+3600
    db.add(MailQueue(id=uid(),recipient=user.email,subject='Verify your Roomform email',body='Your verification token (valid for one hour):\n\n'+token+'\n\nEnter it in your Roomform account verification panel.'));db.commit();return {'sent':True}
class Verify(BaseModel):
    token:str=Field(min_length=30,max_length=200)
@router.post('/verification/confirm')
def confirm(body:Verify,user=Depends(current_customer),db=Depends(get_db)):
    row=db.scalar(select(EmailVerification).where(EmailVerification.customer_id==user.id,EmailVerification.token_hash==hashlib.sha256(body.token.encode()).hexdigest()).with_for_update())
    if not row or row.expires_at<=time.time() or row.verified_at:raise HTTPException(422,'Verification token is invalid or expired')
    row.verified_at=int(time.time());db.commit();return {'verified':True}
