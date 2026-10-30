"""Named administrator authentication with mandatory TOTP and short sessions."""
import hashlib,hmac,secrets,time,os
import pyotp
from fastapi import APIRouter,Depends,HTTPException,Request,Response
from pydantic import BaseModel,Field
from sqlalchemy import select,update
from .database import get_db
from .accounts import password_hash
from .workspace_models import Administrator,AdministratorSession
router=APIRouter(prefix='/api/admin')
class AdminLogin(BaseModel):
    email:str=Field(max_length=254)
    password:str=Field(min_length=12,max_length=128)
    code:str=Field(pattern=r'^\d{6}$')
@router.post('/login')
def login(body:AdminLogin,response:Response,db=Depends(get_db)):
    row=db.scalar(select(Administrator).where(Administrator.email==body.email.strip().lower()))
    calculated=password_hash(body.password,row.password_hash.split(':')[0] if row else '00'*16)
    if not row or not hmac.compare_digest(calculated,row.password_hash):raise HTTPException(401,'Invalid administrator credentials')
    counter=int(time.time())//30
    if not pyotp.TOTP(row.totp_secret).verify(body.code):raise HTTPException(401,'Invalid administrator credentials')
    changed=db.execute(update(Administrator).where(Administrator.id==row.id,Administrator.last_counter<counter).values(last_counter=counter))
    if changed.rowcount!=1:raise HTTPException(401,'This authenticator code has already been used')
    token=secrets.token_urlsafe(32)
    db.add(AdministratorSession(token_hash=hashlib.sha256(token.encode()).hexdigest(),administrator_id=row.id,expires_at=int(time.time())+1800));db.commit()
    response.set_cookie('roomform_admin',token,httponly=True,secure=os.getenv('COOKIE_SECURE','false')=='true',samesite='strict',max_age=1800)
    return {'email':row.email}
@router.post('/logout')
def logout(request:Request,response:Response,db=Depends(get_db)):
    token=request.cookies.get('roomform_admin','')
    session=db.get(AdministratorSession,hashlib.sha256(token.encode()).hexdigest())
    if session:db.delete(session);db.commit()
    response.delete_cookie('roomform_admin');return {'signed_out':True}
