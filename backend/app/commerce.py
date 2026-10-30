"""Real inventory order requests and approved professional services."""
from collections import defaultdict
import os
from decimal import InvalidOperation,ROUND_HALF_UP
from decimal import Decimal
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from .database import get_db
from .models import Asset, Seller
from .workspace_models import Professional, ServiceRequest, Order, Project, OrderCommission
from .workspace import current_customer, project_access, record, uid, audit

router=APIRouter(prefix='/api/workspace')
class ProfessionalIn(BaseModel):
    name:str=Field(min_length=2,max_length=160)
    trade:Literal['painter','carpenter','electrician','plumber','installer','interior_designer','contractor']
    location:str=Field(min_length=2,max_length=200)
    description:str=Field(min_length=20,max_length=2000)
    phone:str=Field(min_length=6,max_length=40)
    daily_rate:Decimal=Field(gt=0,le=10000000,max_digits=12,decimal_places=2)
    currency:Literal['PKR','USD','GBP','EUR']='PKR'

@router.get('/professionals')
def professionals(location:str='',trade:str='',db=Depends(get_db)):
    query=select(Professional).where(Professional.status=='approved')
    if location:query=query.where(Professional.location.ilike('%'+location[:200]+'%'))
    if trade:query=query.where(Professional.trade==trade)
    return [{k:v for k,v in record(p).items() if k not in ('phone','customer_id')} for p in db.scalars(query.limit(500))]

@router.get('/professional/profile')
def profile(user=Depends(current_customer),db=Depends(get_db)):
    p=db.scalar(select(Professional).where(Professional.customer_id==user.id));return record(p) if p else None

@router.post('/professional/profile')
def apply(body:ProfessionalIn,user=Depends(current_customer),db=Depends(get_db)):
    row=db.scalar(select(Professional).where(Professional.customer_id==user.id))
    if row:
        for key,value in body.model_dump().items():setattr(row,key,value)
        row.status='pending'
    else:row=Professional(id=uid(),customer_id=user.id,**body.model_dump());db.add(row)
    db.commit();return record(row)

class ServiceIn(BaseModel):
    project_id:str
    professional_id:str|None=None
    brief:str=Field(min_length=10,max_length=2000)
    phone:str=Field(min_length=6,max_length=40)
    preferred_date:str=Field(default='',max_length=30)
    consent:Literal[True]
@router.post('/services',status_code=201)
def service_request(body:ServiceIn,user=Depends(current_customer),db=Depends(get_db)):
    project=project_access(db,body.project_id,user)
    professional=db.get(Professional,body.professional_id) if body.professional_id else None
    if body.professional_id and (not professional or professional.status!='approved'):raise HTTPException(409,'Professional is not available')
    if professional and professional.customer_id==user.id:raise HTTPException(422,'You cannot request your own service')
    row=ServiceRequest(id=uid(),project_id=project.id,professional_id=body.professional_id,kind='trade' if professional else 'consultation',brief=body.brief,phone=body.phone,preferred_date=body.preferred_date,currency=professional.currency if professional else project.currency)
    db.add(row);db.commit();return record(row)

@router.get('/projects/{project_id}/activity')
def activity(project_id:str,user=Depends(current_customer),db=Depends(get_db)):
    project_access(db,project_id,user)
    return {'services':[record(s) for s in db.scalars(select(ServiceRequest).where(ServiceRequest.project_id==project_id).order_by(ServiceRequest.created_at.desc()))],
            'orders':[record(o) for o in db.scalars(select(Order).where(Order.project_id==project_id).order_by(Order.created_at.desc()))]}

@router.get('/professional/jobs')
def jobs(user=Depends(current_customer),db=Depends(get_db)):
    p=db.scalar(select(Professional).where(Professional.customer_id==user.id))
    if not p:return []
    return [{**record(j),'project_name':db.get(Project,j.project_id).name,'location':db.get(Project,j.project_id).location} for j in db.scalars(select(ServiceRequest).where(ServiceRequest.professional_id==p.id).order_by(ServiceRequest.created_at.desc()))]

class QuoteIn(BaseModel):
    amount:Decimal=Field(gt=0,le=10000000,max_digits=12,decimal_places=2)
    response:str=Field(min_length=10,max_length=2000)
@router.post('/services/{service_id}/quote')
def send_quote(service_id:str,body:QuoteIn,user=Depends(current_customer),db=Depends(get_db)):
    job=db.scalar(select(ServiceRequest).where(ServiceRequest.id==service_id).with_for_update())
    professional=db.get(Professional,job.professional_id) if job and job.professional_id else None
    if not professional or professional.customer_id!=user.id or professional.status!='approved':raise HTTPException(403,'Approved assigned professional required')
    if job.status not in ('requested','quoted'):raise HTTPException(409,'Quote is already decided')
    job.quoted_amount=body.amount;job.response=body.response;job.status='quoted';db.commit();return record(job)

class ServiceDecision(BaseModel):
    status:Literal['accepted','declined','scheduled','completed','cancelled']
@router.patch('/services/{service_id}')
def service_decision(service_id:str,body:ServiceDecision,user=Depends(current_customer),db=Depends(get_db)):
    job=db.scalar(select(ServiceRequest).where(ServiceRequest.id==service_id).with_for_update())
    if not job:raise HTTPException(404,'Request not found')
    pro=db.get(Professional,job.professional_id) if job.professional_id else None
    if pro and pro.customer_id==user.id:
        if pro.status!='approved':raise HTTPException(403,'Professional approval required')
        transitions={'accepted':['scheduled'],'scheduled':['completed']}
    else:
        project_access(db,job.project_id,user)
        transitions={'requested':['cancelled'],'quoted':['accepted','declined'],'accepted':['cancelled']}
    if body.status not in transitions.get(job.status,[]):raise HTTPException(409,'This status transition is not available')
    job.status=body.status;audit(db,user.id,'service.'+body.status,job.id);db.commit();return record(job)

class OrderLine(BaseModel):
    asset_id:str
    quantity:int=Field(ge=1,le=100)
class OrderIn(BaseModel):
    project_id:str
    items:list[OrderLine]=Field(min_length=1,max_length=30)
    address:str=Field(min_length=10,max_length=500)
    phone:str=Field(min_length=6,max_length=40)
    consent:Literal[True]
@router.post('/orders',status_code=201)
def place_order(body:OrderIn,user=Depends(current_customer),db=Depends(get_db)):
    project_access(db,body.project_id,user)
    if len({i.asset_id for i in body.items})!=len(body.items):raise HTTPException(422,'Combine duplicate product lines')
    groups=defaultdict(list)
    for line in body.items:
        a=db.get(Asset,line.asset_id)
        if not a or not a.active or a.stock<line.quantity or not db.get(Seller,a.seller_id).active:raise HTTPException(409,'Product is no longer available in the requested quantity')
        if a.seller_id=='demo':raise HTTPException(422,'Demo illustrations cannot be purchased. Choose a real seller listing.')
        groups[a.seller_id].append((a,line.quantity))
    commission_rate=None
    if os.getenv('MARKETPLACE_COMMISSION_PERCENT'):
        try:commission_rate=Decimal(os.environ['MARKETPLACE_COMMISSION_PERCENT'])
        except InvalidOperation:raise HTTPException(503,'Marketplace commission configuration is invalid')
        if not commission_rate.is_finite() or not 0<=commission_rate<=40:raise HTTPException(503,'Marketplace commission configuration is invalid')
    if commission_rate is not None:commission_rate=commission_rate.quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
    result=[]
    for seller,items in groups.items():
        if sum((a.price*q for a,q in items),Decimal(0))>Decimal('9999999999.99'):raise HTTPException(422,'Order value exceeds the supported limit')
        if len({a.currency for a,q in items})!=1:raise HTTPException(422,'Each seller order must use one currency')
        snapshots=[{'asset_id':a.id,'name':a.name,'quantity':q,'unit_price':str(a.price),'subtotal':str(a.price*q),'delivery_days':a.delivery_days} for a,q in items]
        order=Order(id=uid(),project_id=body.project_id,customer_id=user.id,seller_id=seller,items=snapshots,total=sum((a.price*q for a,q in items),Decimal(0)),currency=items[0][0].currency,address=body.address,phone=body.phone)
        db.add(order);db.flush();result.append(order)
        if commission_rate is not None:
            fee=(order.total*commission_rate/100).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
            db.add(OrderCommission(order_id=order.id,rate_percent=commission_rate,amount=fee,seller_net=order.total-fee,currency=order.currency))
    db.commit();return {'orders':[record(o) for o in result],'notice':'Seller confirmation required. No payment collected. Delivery and taxes must be agreed separately.'}

@router.post('/orders/{order_id}/cancel')
def cancel_order(order_id:str,user=Depends(current_customer),db=Depends(get_db)):
    row=db.scalar(select(Order).where(Order.id==order_id).with_for_update())
    if not row:raise HTTPException(404,'Order not found')
    project_access(db,row.project_id,user)
    if row.status not in ('requested','confirmed'):raise HTTPException(409,'Contact your seller for cancellations after dispatch')
    if row.status=='confirmed':restore_stock(db,row)
    commission=db.get(OrderCommission,row.id)
    if commission:commission.status='void'
    row.status='cancelled';audit(db,user.id,'order.cancelled',row.id);db.commit();return record(row)

def restore_stock(db,order):
    for item in order.items:db.execute(update(Asset).where(Asset.id==item['asset_id']).values(stock=Asset.stock+item['quantity']))

def seller_order_update(db,order_id,seller,status):
    row=db.scalar(select(Order).where(Order.id==order_id).with_for_update())
    if not row or row.seller_id!=seller:raise HTTPException(404,'Order not found')
    if not db.get(Seller,seller).active:raise HTTPException(403,'Seller approval required')
    transitions={'requested':['confirmed','cancelled'],'confirmed':['dispatched','cancelled'],'dispatched':['delivered']}
    if status not in transitions.get(row.status,[]):raise HTTPException(409,'This order transition is not available')
    if status=='confirmed':
        for item in row.items:
            changed=db.execute(update(Asset).where(Asset.id==item['asset_id'],Asset.active==True,Asset.stock>=item['quantity']).values(stock=Asset.stock-item['quantity']))
            if changed.rowcount!=1:
                db.rollback();raise HTTPException(409,'Insufficient stock; order has not been confirmed')
    if status=='cancelled' and row.status=='confirmed':restore_stock(db,row)
    if status=='cancelled':
        commission=db.get(OrderCommission,row.id)
        if commission:commission.status='void'
    row.status=status;audit(db,'seller:'+seller,'order.'+status,row.id);db.commit();return record(row)
