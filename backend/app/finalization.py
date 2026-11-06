"""Immutable, authorized project finalization estimates and private PDF requests."""
import hashlib
import json
import os
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Literal
from uuid import uuid4
from xml.sax.saxutils import escape
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import Response
from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .database import DATA, get_db
from .models import Asset, Seller, Design, now
from .workspace_models import AssetFulfillment, FinalizationBooking, ProjectDesign, MailQueue
from .workspace import current_customer, project_access

router = APIRouter()
PDF_DIR = DATA / 'finalization-pdfs'
TERMS = ('Draft project finalization request and estimate, not a signed purchase agreement. '
         'Prices, stock, delivery coverage and scope must be reconfirmed before acceptance or payment. '
         'No inventory is reserved by this request. Lead times are calendar-day estimates after '
         'written scope acceptance, required measurements and deposit; supplier work runs in parallel, '
         'followed by installation. Structural works, taxes and shipping charges are excluded unless '
         'explicitly priced. The visualization is a design reference, not a guarantee of exact fit or finish. '
         'Final scope, delivery charges, payment milestones, cancellation and warranty terms require written agreement.')

class FulfillmentIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    ready_min_days: int = Field(ge=0, le=365)
    ready_max_days: int = Field(ge=0, le=365)
    delivery_min_days: int = Field(ge=0, le=365)
    delivery_max_days: int = Field(ge=0, le=365)
    @model_validator(mode='after')
    def ordered(self):
        if self.ready_min_days > self.ready_max_days or self.delivery_min_days > self.delivery_max_days:
            raise ValueError('Minimum days cannot exceed maximum days')
        return self

def merchant_asset(db, asset_id, seller_id):
    a = db.get(Asset, asset_id)
    if not a or a.seller_id != seller_id: raise HTTPException(404, 'Listing not found')
    return a

# Imported lazily to avoid app.main circular imports while its routes load.
def seller_session(db=Depends(get_db), key: str | None = Header(default=None, alias='X-Merchant-Key')):
    from .main import merchant
    return merchant(db, key)

@router.get('/api/assets/{asset_id}/fulfillment')
def fulfillment(asset_id: str, seller=Depends(seller_session), db=Depends(get_db)):
    merchant_asset(db, asset_id, seller)
    row = db.get(AssetFulfillment, asset_id)
    return {'asset_id': asset_id, **({k:getattr(row,k) for k in FulfillmentIn.model_fields} if row else {}), 'configured': bool(row)}

@router.put('/api/assets/{asset_id}/fulfillment')
def save_fulfillment(asset_id: str, body: FulfillmentIn, seller=Depends(seller_session), db=Depends(get_db)):
    merchant_asset(db, asset_id, seller)
    row = db.get(AssetFulfillment, asset_id)
    if not row: row = AssetFulfillment(asset_id=asset_id, **body.model_dump()); db.add(row)
    else:
        for k,v in body.model_dump().items(): setattr(row,k,v)
    db.commit()
    return {'asset_id':asset_id, **body.model_dump(), 'configured':True}

class PreviewIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    design_id: str = Field(min_length=1, max_length=36)
class BookingIn(PreviewIn):
    phone: str = Field(min_length=6, max_length=40)
    address: str = Field(min_length=10, max_length=500)
    preferred_date: str = Field(default='', max_length=30)
    consent: Literal[True]
    idempotency_key: str = Field(min_length=8, max_length=80, pattern=r'^[a-zA-Z0-9_-]+$')
    @field_validator('preferred_date')
    @classmethod
    def calendar_date(cls, value):
        if value:
            parsed=date.fromisoformat(value)
            if parsed.isoformat()!=value: raise ValueError('Use YYYY-MM-DD')
        return value

def money(v):
    try:
        d=Decimal(str(v))
        if not d.is_finite() or d<0 or d>Decimal('9999999999.99'): raise ValueError()
        return d.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError): raise HTTPException(422,'Invalid monetary value in saved estimate')

def estimate(db, project, design_id):
    link=db.get(ProjectDesign,design_id)
    design=db.get(Design,design_id)
    if not design or not link or link.project_id!=project.id: raise HTTPException(404,'Saved design not found in this project')
    original=design.quote or {}; issues=[]; items=[]; seen=set()
    for line in original.get('items',[]):
        ident=line.get('asset_id'); quantity=line.get('quantity',1)
        if not isinstance(quantity,int) or not 1<=quantity<=100 or ident in seen:raise HTTPException(422,'Invalid saved product quantities')
        seen.add(ident); a=db.get(Asset,ident)
        if not a: issues.append('Product '+str(ident)+' no longer exists'); continue
        seller=db.get(Seller,a.seller_id)
        if not a.active or not seller or not seller.active or a.stock<quantity or a.seller_id=='demo':issues.append(a.name+': stock or seller availability needs confirmation')
        if a.currency!=project.currency: issues.append(a.name+': currency differs from project')
        timing=db.get(AssetFulfillment,a.id)
        if not timing:issues.append(a.name+': seller must set preparation and delivery ranges')
        items.append({'asset_id':a.id,'seller_id':a.seller_id,'name':a.name,'quantity':quantity,'unit_price':str(money(a.price)),'subtotal':str(money(a.price*quantity)),'stock':a.stock,'condition':a.condition,'delivery_location':a.delivery_location,**{k:getattr(timing,k) if timing else None for k in FulfillmentIn.model_fields}})
    if not items:issues.append('This design has no available product lines')
    try:
        fees=json.loads(os.getenv('FINALIZATION_SERVICE_FEES_JSON','{}'))
        configured=fees.get(project.currency)
        fee=money(configured) if configured is not None else None
    except (ValueError,TypeError):raise HTTPException(503,'Finalization service charges are incorrectly configured')
    if fee is None:issues.append('Finalization service charge is not configured for '+project.currency)
    if original.get('currency')!=project.currency:issues.append('Saved design currency differs from project')
    labor=money(original.get('labor',0)); subtotal=sum((money(i['subtotal']) for i in items),Decimal(0)); total=subtotal+labor+(fee or 0)
    if total>project.budget:issues.append('Current items, labor and service charge exceed the project budget')
    installation=original.get('installation_days')
    if not isinstance(installation,int) or not 1<=installation<=365:issues.append('Installation duration needs a valid saved estimate');installation=None
    timed=bool(items) and all(i['ready_min_days'] is not None for i in items) and installation is not None
    return {'project_id':project.id,'project_name':project.name,'design_id':design.id,'image_url':design.image_url,'location':project.location,'currency':project.currency,'budget':str(money(project.budget)),'items':items,'items_subtotal':str(money(subtotal)),'labor':str(labor),'service_charge':str(fee) if fee is not None else None,'total':str(money(total)) if fee is not None else None,'installation_days':installation,'min_days':max(i['ready_min_days']+i['delivery_min_days'] for i in items)+installation if timed else None,'max_days':max(i['ready_max_days']+i['delivery_max_days'] for i in items)+installation if timed else None,'issues':issues,'agreement_status':'draft','inventory_reserved':False,'terms':TERMS,'timeline_basis':'Calendar days after written acceptance, measurements and deposit; parallel procurement plus sequential installation','exclusions':original.get('exclusions',['Taxes','Shipping fees','Structural work'])}

@router.post('/api/workspace/projects/{project_id}/finalizations/preview')
def preview(project_id:str, body:PreviewIn,user=Depends(current_customer),db=Depends(get_db)):
    return estimate(db,project_access(db,project_id,user),body.design_id)

def make_pdf(snapshot, booking_id):
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as PDFImage
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont("Roomform",str(Path(__file__).parent/"fonts"/"manrope-400.ttf")))
    buf=BytesIO(); styles=getSampleStyleSheet(); story=[]
    for style in styles.byName.values():
        style.fontName='Roomform'
        style.wordWrap='CJK'
    def p(text,style='BodyText'):story.append(Paragraph(escape(str(text)),styles[style]));story.append(Spacer(1,8))
    p('Roomform | Project finalization request','Title');p('DRAFT AGREEMENT / ESTIMATE','Heading2');p('Booking '+booking_id);p('Stock and estimate checked at: '+snapshot.get('stock_checked_at',''))
    for key in ('project_name','design_id','customer_name','customer_email','phone','address','preferred_date'):
        p(key.replace('_',' ').title()+': '+str(snapshot.get(key,'')))
    image=snapshot.get('image_url','')
    if image.startswith('/media/') and Path(image).name==image.removeprefix('/media/'):
        image_path=DATA/'media'/Path(image).name
        if image_path.is_file():
            from PIL import Image
            with Image.open(image_path) as im:
                width,height=im.size
            factor=min(480/width,280/height)
            story.append(PDFImage(str(image_path),width=width*factor,height=height*factor))
    p('Selected products','Heading2')
    for i in snapshot['items']:
        p(i['name'],'Heading3');p('Unique item code: '+i['asset_id']+' | Seller: '+i['seller_id']);p(f"Quantity {i['quantity']} | Unit {snapshot['currency']} {i['unit_price']} | Line total {i['subtotal']} | Stock at booking {i['stock']}")
        p(f"Preparation {i['ready_min_days']}-{i['ready_max_days']} days; delivery {i['delivery_min_days']}-{i['delivery_max_days']} days")
    p('Project summary','Heading2')
    for key in ('budget','items_subtotal','labor','service_charge','total'):p(key.replace('_',' ').title()+': '+snapshot['currency']+' '+str(snapshot[key]))
    p(f"Expected project completion: {snapshot['min_days']}-{snapshot['max_days']} calendar days (including {snapshot['installation_days']} installation days)")
    p(snapshot['timeline_basis']);p('Excluded: '+', '.join(snapshot['exclusions']));p('Agreement terms','Heading2');p(snapshot['terms']);p('Customer requested finalization and consented to share the above details. This is not a signed contract.');p('Customer signature: __________________  Date: __________');p('Roomform representative: ______________  Date: __________')
    SimpleDocTemplate(buf,pagesize=A4,rightMargin=45,leftMargin=45,topMargin=45,bottomMargin=45).build(story)
    return buf.getvalue()

def result(row,db):
    mail=db.get(MailQueue,row.mail_id) if row.mail_id else None
    return {'id':row.id,'project_id':row.project_id,'design_id':row.design_id,'snapshot':row.snapshot,'pdf_url':'/api/workspace/finalizations/'+row.id+'/pdf','email_status':mail.status if mail else 'not_configured'}

@router.post('/api/workspace/projects/{project_id}/finalizations',status_code=201)
def book(project_id:str,body:BookingIn,user=Depends(current_customer),db=Depends(get_db)):
    project=project_access(db,project_id,user)
    fingerprint=hashlib.sha256(json.dumps({'project_id':project_id,**body.model_dump()},sort_keys=True).encode()).hexdigest()
    existing=db.scalar(select(FinalizationBooking).where(FinalizationBooking.customer_id==user.id,FinalizationBooking.idempotency_key==body.idempotency_key))
    if existing:
        if existing.request_hash!=fingerprint:raise HTTPException(409,'Booking key was already used for different details')
        return result(existing,db)
    snapshot=estimate(db,project,body.design_id)
    if snapshot['issues']:raise HTTPException(409,{'message':'Resolve estimate details before booking','issues':snapshot['issues']})
    ident=str(uuid4());snapshot.update(stock_checked_at=now().isoformat(),customer_name=user.name,customer_email=user.email,phone=body.phone,address=body.address,preferred_date=body.preferred_date)
    PDF_DIR.mkdir(parents=True,exist_ok=True,mode=0o700);os.chmod(PDF_DIR,0o700)
    path=PDF_DIR/(ident+'.pdf');path.write_bytes(make_pdf(snapshot,ident));os.chmod(path,0o600)
    recipient=os.getenv('FINALIZATION_EMAIL','').strip();mail=None
    if recipient:
        if '\n' in recipient or '\r' in recipient or '@' not in recipient:
            path.unlink(missing_ok=True);raise HTTPException(503,'Finalization email address is incorrectly configured')
        mail=MailQueue(id=str(uuid4()),recipient=recipient,subject='Roomform finalization '+ident,body='A customer requested project finalization. See the attached draft estimate and item codes.');db.add(mail);db.flush()
    row=FinalizationBooking(id=ident,project_id=project.id,customer_id=user.id,design_id=body.design_id,idempotency_key=body.idempotency_key,request_hash=fingerprint,snapshot=snapshot,pdf=ident+'.pdf',mail_id=mail.id if mail else None);db.add(row)
    try:db.commit()
    except IntegrityError:
        db.rollback();path.unlink(missing_ok=True)
        existing=db.scalar(select(FinalizationBooking).where(FinalizationBooking.customer_id==user.id,FinalizationBooking.idempotency_key==body.idempotency_key))
        if not existing or existing.request_hash!=fingerprint:raise HTTPException(409,'Booking key conflict')
        return result(existing,db)
    return result(row,db)

@router.get('/api/workspace/projects/{project_id}/finalizations')
def bookings(project_id:str,user=Depends(current_customer),db=Depends(get_db)):
    project_access(db,project_id,user)
    return [result(row,db) for row in db.scalars(select(FinalizationBooking).where(FinalizationBooking.project_id==project_id).order_by(FinalizationBooking.created_at.desc()))]

@router.get('/api/workspace/finalizations/{booking_id}/pdf')
def download(booking_id:str,user=Depends(current_customer),db=Depends(get_db)):
    row=db.get(FinalizationBooking,booking_id)
    if not row:raise HTTPException(404,'Booking not found')
    project_access(db,row.project_id,user)
    path=PDF_DIR/row.pdf
    if not path.is_file():raise HTTPException(404,'Document unavailable')
    return Response(path.read_bytes(),media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="roomform-finalization-{row.id}.pdf"','Cache-Control':'private, no-store'})
