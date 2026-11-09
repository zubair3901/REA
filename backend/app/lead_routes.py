"""Lead routes: HTTP adapters for a single application concern."""
import os
from uuid import uuid4
from fastapi import HTTPException
from fastapi import Request
from .models import Design, Lead, Outbox
from .workspace import current_customer, project_access
from .workspace_models import ProjectDesign
from fastapi import APIRouter
from .dependencies import DB
from .schemas import LeadIn

router = APIRouter()

@router.post('/api/leads',status_code=201)
def create_lead(body: LeadIn,request:Request,db: DB):
    link=db.get(ProjectDesign,body.design_id)
    if link:project_access(db,link.project_id,current_customer(request,db))
    if not db.get(Design,body.design_id): raise HTTPException(404,'Design not found')
    lead=Lead(id=str(uuid4()),**body.model_dump());db.add(lead);db.flush()
    db.add(Outbox(id=str(uuid4()),lead_id=lead.id,payload={'event':'consultation.requested','lead_id':lead.id,**body.model_dump()}));db.commit()
    return {'id':lead.id,'status':lead.status,'consultation_url':os.getenv('CONSULTATION_URL') or None,'payment_collected':False}
