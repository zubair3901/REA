"""Operator reconciliation, professional review and team contracts."""
import time
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, update, func
from .database import get_db
from .operations import operator
from .workspace_models import PaymentRequest, Project, Professional, ServiceRequest, Organization, Membership, AuditEvent, Customer, Order, OrderCommission
from .workspace import record, audit
router=APIRouter(prefix='/api/operator/platform',dependencies=[Depends(operator)])

@router.get('')
def overview(db=Depends(get_db)):
    tables={'payments':PaymentRequest,'professionals':Professional,'services':ServiceRequest,'organizations':Organization,'orders':Order,'commissions':OrderCommission}
    result={key:[record(row) for row in db.scalars(select(model).limit(500))] for key,model in tables.items()}
    for request in result['services']:
        project=db.get(Project,request['project_id'])
        request.update(project_name=project.name,location=project.location,budget=str(project.budget),budget_currency=project.currency)
    for o in result['organizations']:o['owner_email']=db.get(Customer,o['owner_id']).email
    result['audit']=[record(e) for e in db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(50))]
    return result

class PaymentDecision(BaseModel):
    status:Literal['approved','rejected']
    note:str=Field(min_length=5,max_length=500)
@router.patch('/payments/{payment_id}')
def reconcile(request:Request,payment_id:str,body:PaymentDecision,db=Depends(get_db)):
    p=db.get(PaymentRequest,payment_id)
    if not p:raise HTTPException(404,'Payment request not found')
    changed=db.execute(update(PaymentRequest).where(PaymentRequest.id==payment_id,PaymentRequest.status=='submitted').values(status=body.status))
    if changed.rowcount!=1:raise HTTPException(409,'Only a submitted, unreviewed payment can be reconciled')
    if body.status=='approved':db.execute(update(Project).where(Project.id==p.project_id).values(credits=Project.credits+p.credits))
    audit(db,getattr(request.state,'administrator_id','legacy-operator'),'payment.'+body.status,p.id,{'note':body.note,'amount':str(p.amount),'reference':p.reference})
    db.commit();return {'id':p.id,'status':body.status}

class ProfessionalDecision(BaseModel):
    status:Literal['approved','rejected','suspended']
@router.patch('/professionals/{professional_id}')
def review_professional(request:Request,professional_id:str,body:ProfessionalDecision,db=Depends(get_db)):
    p=db.get(Professional,professional_id)
    if not p:raise HTTPException(404,'Professional not found')
    p.status=body.status;audit(db,getattr(request.state,'administrator_id','legacy-operator'),'professional.'+body.status,p.id);db.commit();return record(p)

class TeamActivation(BaseModel):
    plan:Literal['basic','ultra','enterprise']
    seats:int=Field(ge=1,le=1000)
    days:int=Field(ge=1,le=366)
    reference:str=Field(min_length=5,max_length=200)
@router.patch('/organizations/{organization_id}')
def activate(request:Request,organization_id:str,body:TeamActivation,db=Depends(get_db)):
    org=db.scalar(select(Organization).where(Organization.id==organization_id).with_for_update())
    if not org:raise HTTPException(404,'Organization not found')
    seats={'basic':1,'ultra':3}.get(body.plan,body.seats)
    count=db.scalar(select(func.count()).select_from(Membership).where(Membership.organization_id==org.id))
    if count>seats:raise HTTPException(409,'Remove extra members before reducing the seat allowance')
    org.plan=body.plan;org.seats=seats;org.expires_at=int(time.time())+body.days*86400
    audit(db,getattr(request.state,'administrator_id','legacy-operator'),'organization.activated',org.id,body.model_dump());db.commit();return record(org)

class ConsultationUpdate(BaseModel):
    status:Literal['contacted','scheduled','completed','cancelled']
    response:str=Field(min_length=5,max_length=2000)
@router.patch('/services/{service_id}')
def consultation(request:Request,service_id:str,body:ConsultationUpdate,db=Depends(get_db)):
    row=db.scalar(select(ServiceRequest).where(ServiceRequest.id==service_id).with_for_update())
    if not row or row.kind!='consultation':raise HTTPException(404,'Consultation not found')
    transitions={'requested':['contacted','scheduled','cancelled'],'contacted':['scheduled','cancelled'],'scheduled':['completed','cancelled']}
    if body.status not in transitions.get(row.status,[]):raise HTTPException(409,'This status transition is not available')
    row.status=body.status;row.response=body.response;audit(db,getattr(request.state,'administrator_id','legacy-operator'),'consultation.'+body.status,row.id);db.commit();return record(row)
