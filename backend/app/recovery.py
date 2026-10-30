"""Single-use account recovery. Mail is delivered by the configured worker."""
import os, secrets, hashlib, time
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select,delete
from .database import get_db
from .workspace_models import Customer,CustomerSession,PasswordReset,MailQueue
from .workspace import uid,audit
from .accounts import password_hash
router=APIRouter(prefix='/api/workspace')
class Forgot(BaseModel):
    email:str=Field(max_length=254,pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
class Reset(BaseModel):
    token:str=Field(min_length=30,max_length=200)
    password:str=Field(min_length=12,max_length=128)
@router.post('/forgot-password')
def forgot(body:Forgot,db=Depends(get_db)):
    if not os.getenv('SMTP_HOST') or not os.getenv('SMTP_FROM') or not os.getenv('APP_URL'):
        raise HTTPException(503,'Account recovery email is not configured yet. Contact the platform operator for help.')
    user=db.scalar(select(Customer).where(Customer.email==body.email.strip().lower()))
    if user:
        token=secrets.token_urlsafe(32)
        db.execute(delete(PasswordReset).where(PasswordReset.customer_id==user.id))
        db.add(PasswordReset(token_hash=hashlib.sha256(token.encode()).hexdigest(),customer_id=user.id,expires_at=int(time.time())+1800))
        url=os.environ['APP_URL'].rstrip('/')+'/?reset='+token
        db.add(MailQueue(id=uid(),recipient=user.email,subject='Reset your Roomform password',body='Open this link within 30 minutes to reset your password:\n\n'+url+'\n\nIf you did not request this, ignore this email.'))
        db.commit()
    return {'message':'If this email has an account, a recovery link will be sent shortly.'}
@router.post('/reset-password')
def reset(body:Reset,db=Depends(get_db)):
    hashed=hashlib.sha256(body.token.encode()).hexdigest()
    row=db.scalar(select(PasswordReset).where(PasswordReset.token_hash==hashed).with_for_update())
    if not row or row.expires_at<=time.time():raise HTTPException(422,'This reset link is invalid or expired')
    deleted=db.execute(delete(PasswordReset).where(PasswordReset.token_hash==hashed))
    if deleted.rowcount!=1:raise HTTPException(409,'This link has already been used')
    user=db.get(Customer,row.customer_id);user.password_hash=password_hash(body.password)
    db.execute(delete(CustomerSession).where(CustomerSession.customer_id==user.id))
    audit(db,user.id,'password.reset',user.id);db.commit();return {'message':'Password changed. Sign in with your new password.'}
