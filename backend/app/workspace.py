"""Customer accounts and project workspaces. No AI calls or payment simulations."""
import hashlib
import hmac
import os
import secrets
import time
from uuid import uuid4
from decimal import Decimal
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import select, or_, and_
from sqlalchemy.exc import IntegrityError
from .database import get_db
from .accounts import Login, password_hash
from .models import Design
from .workspace_models import Customer, CustomerSession, Organization, Membership, Project, ProjectDesign, PaymentRequest, AuditEvent

router = APIRouter(prefix='/api/workspace')
COOKIE = 'roomform_session'
def uid(): return str(uuid4())
def record(row): return {c.name: getattr(row,c.name) for c in row.__table__.columns}
def audit(db, actor, action, target, details=None):
    db.add(AuditEvent(id=uid(),actor=actor,action=action,target_id=target,details=details or {}))

def current_customer(request: Request, db=Depends(get_db)):
    token=request.cookies.get(COOKIE,'')
    session=db.get(CustomerSession,hashlib.sha256(token.encode()).hexdigest()) if token else None
    if not session or session.expires_at<=time.time(): raise HTTPException(401,'Sign in to your Roomform account')
    if request.method not in ('GET','HEAD','OPTIONS'):
        origin=request.headers.get('origin')
        allowed=os.getenv('CORS_ORIGINS','http://localhost:5173').split(',')
        if origin and origin not in allowed and origin!=str(request.base_url).rstrip('/'):
            raise HTTPException(403,'Request origin is not allowed')
    user=db.get(Customer,session.customer_id)
    if os.getenv('REQUIRE_VERIFIED_EMAIL','false')=='true' and request.method not in ('GET','HEAD','OPTIONS') and request.url.path not in ('/api/workspace/verification/send','/api/workspace/verification/confirm','/api/workspace/logout'):
        from .workspace_models import EmailVerification
        verification=db.get(EmailVerification,user.id)
        if not verification or not verification.verified_at:raise HTTPException(403,'Verify your email before making changes or sending requests')
    return user

def project_access(db, project_id, user):
    project=db.get(Project,project_id)
    if not project: raise HTTPException(404,'Project not found')
    member=project.organization_id and db.scalar(select(Membership).where(Membership.organization_id==project.organization_id,Membership.customer_id==user.id))
    if (project.organization_id and not member) or (not project.organization_id and project.customer_id!=user.id): raise HTTPException(404,'Project not found')
    if project.organization_id:
        organization=db.get(Organization,project.organization_id)
        if not organization or organization.expires_at<=time.time():
            raise HTTPException(403,'Team access has expired. Ask the owner to renew the plan.')
    return project

def start_session(db, user, response):
    token=secrets.token_urlsafe(32)
    db.add(CustomerSession(token_hash=hashlib.sha256(token.encode()).hexdigest(),customer_id=user.id,expires_at=int(time.time())+604800))
    db.commit()
    response.set_cookie(COOKIE,token,httponly=True,secure=os.getenv('COOKIE_SECURE','false')=='true',samesite='strict',max_age=604800,path='/')
    return {'id':user.id,'name':user.name,'email':user.email}

class Registration(Login):
    name: str=Field(min_length=2,max_length=160)

@router.post('/register',status_code=201)
def register(body:Registration,response:Response,db=Depends(get_db)):
    user=Customer(id=uid(),name=body.name.strip(),email=body.email.strip().lower(),password_hash=password_hash(body.password))
    db.add(user)
    try: return start_session(db,user,response)
    except IntegrityError:
        db.rollback();raise HTTPException(409,'Email already registered. Sign in instead.')

@router.post('/login')
def login(body:Login,response:Response,db=Depends(get_db)):
    user=db.scalar(select(Customer).where(Customer.email==body.email.strip().lower()))
    computed=password_hash(body.password,user.password_hash.split(':')[0] if user else '00'*16)
    if not user or not hmac.compare_digest(computed,user.password_hash):raise HTTPException(401,'Invalid email or password')
    return start_session(db,user,response)

@router.get('/me')
def me(user=Depends(current_customer)):
    return {'id':user.id,'name':user.name,'email':user.email}

@router.post('/logout')
def logout(request:Request,response:Response,user=Depends(current_customer),db=Depends(get_db)):
    session=db.get(CustomerSession,hashlib.sha256(request.cookies[COOKIE].encode()).hexdigest())
    db.delete(session);db.commit();response.delete_cookie(COOKIE,path='/')
    return {'signed_out':True}

class ProjectIn(BaseModel):
    name: str=Field(min_length=2,max_length=160)
    location: str=Field(min_length=2,max_length=200)
    budget: Decimal=Field(gt=0,le=10000000,max_digits=12,decimal_places=2)
    currency: Literal['USD','PKR','GBP','EUR']='PKR'
    preference: Literal['new','used','either']='either'
    organization_id: str|None=None

@router.post('/projects',status_code=201)
def create_project(body:ProjectIn,user=Depends(current_customer),db=Depends(get_db)):
    if body.organization_id:
        org=db.get(Organization,body.organization_id)
        member=db.scalar(select(Membership).where(Membership.organization_id==body.organization_id,Membership.customer_id==user.id))
        if not org or not member:raise HTTPException(403,'Organization membership required')
        if org.expires_at<=time.time():raise HTTPException(403,'This team plan requires activation or renewal')
    row=Project(id=uid(),customer_id=user.id,**body.model_dump());db.add(row);db.commit();return record(row)

@router.get('/projects')
def projects(user=Depends(current_customer),db=Depends(get_db)):
    orgs=select(Membership.organization_id).where(Membership.customer_id==user.id)
    return [record(p) for p in db.scalars(select(Project).where(or_(and_(Project.customer_id==user.id,Project.organization_id.is_(None)),Project.organization_id.in_(orgs))).order_by(Project.created_at.desc()))]

@router.get('/projects/{project_id}')
def project_detail(project_id:str,user=Depends(current_customer),db=Depends(get_db)):
    p=project_access(db,project_id,user)
    designs=db.scalars(select(Design).join(ProjectDesign,ProjectDesign.design_id==Design.id).where(ProjectDesign.project_id==p.id).order_by(Design.created_at.desc())).all()
    return {**record(p),'designs':[record(d) for d in designs]}

class ProjectStatus(BaseModel):
    status: Literal['planning','sourcing','in_progress','completed','archived']
@router.patch('/projects/{project_id}')
def update_project(project_id:str,body:ProjectStatus,user=Depends(current_customer),db=Depends(get_db)):
    p=project_access(db,project_id,user);p.status=body.status;db.commit();return record(p)

PACKAGES={'starter':{'name':'Room refresh','amount':3,'credits':3},'complete':{'name':'Room transformation','amount':5,'credits':6}}
@router.get('/packages')
def packages():
    return {'packages':[{'id':k,**v,'currency':'USD'} for k,v in PACKAGES.items()],
            'payment_instructions':os.getenv('PAYMENT_INSTRUCTIONS',''),
            'payments_enabled':bool(os.getenv('PAYMENT_INSTRUCTIONS')),
            'sales_enabled':os.getenv('ENABLE_PROJECT_SALES','false')=='true' and bool(os.getenv('PAYMENT_INSTRUCTIONS')),'ai_enabled':False,'business_plans':[{'id':'basic','seats':1},{'id':'ultra','seats':3},{'id':'enterprise','seats':'custom'}]}

class PackageIn(BaseModel):
    package: Literal['starter','complete']
@router.post('/projects/{project_id}/checkout',status_code=201)
def checkout(project_id:str,body:PackageIn,user=Depends(current_customer),db=Depends(get_db)):
    project_access(db,project_id,user)
    if os.getenv('ENABLE_PROJECT_SALES','false')!='true':raise HTTPException(503,'Project package sales open when AI generation is ready. Free local previews are available now.')
    if not os.getenv('PAYMENT_INSTRUCTIONS'):raise HTTPException(503,'Payment collection has not been configured')
    existing=db.scalar(select(PaymentRequest).where(PaymentRequest.project_id==project_id,PaymentRequest.status.in_(['awaiting_payment','submitted'])))
    if existing:return record(existing)
    package=PACKAGES[body.package]
    row=PaymentRequest(id=uid(),project_id=project_id,customer_id=user.id,package=body.package,amount=package['amount'],credits=package['credits'])
    db.add(row);db.commit();return record(row)

class ReferenceIn(BaseModel):
    reference:str=Field(min_length=4,max_length=200)
@router.post('/payments/{payment_id}/reference')
def payment_reference(payment_id:str,body:ReferenceIn,user=Depends(current_customer),db=Depends(get_db)):
    row=db.scalar(select(PaymentRequest).where(PaymentRequest.id==payment_id).with_for_update())
    if not row or row.customer_id!=user.id:raise HTTPException(404,'Payment not found')
    if row.status not in ('awaiting_payment','submitted'):raise HTTPException(409,'Payment already reviewed')
    row.reference=body.reference.strip();row.status='submitted';db.commit();return record(row)

@router.get('/payments')
def payments(user=Depends(current_customer),db=Depends(get_db)):
    return [record(p) for p in db.scalars(select(PaymentRequest).where(PaymentRequest.customer_id==user.id).order_by(PaymentRequest.created_at.desc()))]

class OrganizationIn(BaseModel):
    name:str=Field(min_length=2,max_length=160)
    plan:Literal['basic','ultra','enterprise']='basic'
@router.post('/organizations',status_code=201)
def organization(body:OrganizationIn,user=Depends(current_customer),db=Depends(get_db)):
    org=Organization(id=uid(),owner_id=user.id,name=body.name,plan=body.plan,seats=1)
    db.add(org);db.flush();db.add(Membership(id=uid(),organization_id=org.id,customer_id=user.id));db.commit();return record(org)

@router.get('/organizations')
def organizations(user=Depends(current_customer),db=Depends(get_db)):
    ids=select(Membership.organization_id).where(Membership.customer_id==user.id)
    rows=db.scalars(select(Organization).where(Organization.id.in_(ids))).all()
    return [{**record(o),'members':[{'id':c.id,'name':c.name,'email':c.email} for c in db.scalars(select(Customer).join(Membership,Membership.customer_id==Customer.id).where(Membership.organization_id==o.id))]} for o in rows]

class MemberIn(BaseModel):
    email:str=Field(max_length=254,pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
@router.post('/organizations/{organization_id}/members')
def add_member(organization_id:str,body:MemberIn,user=Depends(current_customer),db=Depends(get_db)):
    org=db.scalar(select(Organization).where(Organization.id==organization_id).with_for_update())
    if not org or org.owner_id!=user.id:raise HTTPException(403,'Only the team owner can manage access')
    if org.expires_at<=time.time():raise HTTPException(403,'Activate or renew the team plan first')
    members=db.scalars(select(Membership).where(Membership.organization_id==org.id)).all()
    target=db.scalar(select(Customer).where(Customer.email==body.email.strip().lower()))
    if not target:raise HTTPException(422,'Ask your colleague to register a Roomform account first')
    if any(m.customer_id==target.id for m in members):raise HTTPException(409,'Already a team member')
    if len(members)>=org.seats:raise HTTPException(409,'All named seats are occupied')
    db.add(Membership(id=uid(),organization_id=org.id,customer_id=target.id));audit(db,user.id,'member.added',org.id,{'customer_id':target.id});db.commit();return {'added':True}

@router.delete('/organizations/{organization_id}/members/{customer_id}')
def remove_member(organization_id:str,customer_id:str,user=Depends(current_customer),db=Depends(get_db)):
    org=db.scalar(select(Organization).where(Organization.id==organization_id).with_for_update())
    if not org or org.owner_id!=user.id:raise HTTPException(403,'Only the team owner can manage access')
    if customer_id==user.id:raise HTTPException(409,'The owner seat cannot be removed')
    member=db.scalar(select(Membership).where(Membership.organization_id==org.id,Membership.customer_id==customer_id))
    if member:db.delete(member);audit(db,user.id,'member.removed',org.id,{'customer_id':customer_id});db.commit()
    return {'removed':True}
