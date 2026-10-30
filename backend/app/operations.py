"""Operator-only onboarding and consultation inbox; key never returned to clients."""
import hmac,os
from typing import Annotated,Literal
from fastapi import APIRouter,Depends,Header,HTTPException,Request
from pydantic import BaseModel
from sqlalchemy import select
from .database import get_db
from .models import Seller,SellerAccount,Lead,Design
def operator(request:Request, key:Annotated[str|None,Header(alias='X-Operator-Key')]=None,db=Depends(get_db)):
    import hashlib,time
    from .workspace_models import AdministratorSession,Administrator
    token=request.cookies.get('roomform_admin','')
    session=db.get(AdministratorSession,hashlib.sha256(token.encode()).hexdigest()) if token else None
    if session and session.expires_at>time.time() and db.get(Administrator,session.administrator_id):
        request.state.administrator_id=session.administrator_id
        return session.administrator_id
    if os.getenv('ALLOW_LEGACY_OPERATOR_KEY','false')=='true':
        expected=os.getenv('ROOM_OPERATOR_KEY','')
        if expected and key and hmac.compare_digest(key,expected):return 'legacy-operator'
    raise HTTPException(401,'Sign in with your named administrator account and authenticator code')

router=APIRouter(prefix='/api/operator',dependencies=[Depends(operator)])
class Approval(BaseModel):
    active:bool
class LeadStatus(BaseModel):
    status:Literal['pending_consultation','contacted','consultation_booked','closed']
@router.get('/sellers')
def sellers(db=Depends(get_db)):
    rows=db.execute(select(Seller,SellerAccount).outerjoin(SellerAccount)).all()
    return [{'id':s.id,'name':s.name,'active':s.active,'kind':a.kind if a else 'merchant','email':a.email if a else None} for s,a in rows]
@router.patch('/sellers/{seller_id}')
def approval(seller_id:str,body:Approval,db=Depends(get_db)):
    seller=db.get(Seller,seller_id)
    if not seller:raise HTTPException(404,'Seller not found')
    seller.active=body.active;db.commit()
    return {'id':seller.id,'active':seller.active}
@router.get('/leads')
def leads(db=Depends(get_db)):
    rows=db.scalars(select(Lead).order_by(Lead.created_at.desc()).limit(200)).all()
    result=[]
    for lead in rows:
        design=db.get(Design,lead.design_id)
        result.append({'id':lead.id,'name':lead.name,'email':lead.email,'phone':lead.phone,'status':lead.status,'design_id':lead.design_id,'created_at':lead.created_at,'image_url':design.image_url if design else None,'quote':design.quote if design else None})
    return result
@router.patch('/leads/{lead_id}')
def status(lead_id:str,body:LeadStatus,db=Depends(get_db)):
    lead=db.get(Lead,lead_id)
    if not lead:raise HTTPException(404,'Lead not found')
    lead.status=body.status;db.commit()
    return {'id':lead.id,'status':lead.status}
