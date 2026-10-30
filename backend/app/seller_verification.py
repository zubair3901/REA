import hashlib,os,secrets,time
from fastapi import APIRouter,Depends,Header,HTTPException
from pydantic import BaseModel,Field
from .database import get_db
from .accounts import session_seller
from .models import SellerAccount
from .workspace_models import SellerEmailVerification,MailQueue
from .workspace import uid
router=APIRouter(prefix='/api/sellers/verification')
def identity(key:str=Header(alias='X-Merchant-Key'),db=Depends(get_db)):
    seller=session_seller(db,key)
    if not seller:raise HTTPException(401,'Sign in to your seller account')
    return seller
@router.post('/send')
def send(seller=Depends(identity),db=Depends(get_db)):
    if not all(os.getenv(k) for k in ('SMTP_HOST','SMTP_FROM')):raise HTTPException(503,'Verification email is not configured')
    account=db.get(SellerAccount,seller);row=db.get(SellerEmailVerification,seller)
    if row and row.verified_at:return {'verified':True}
    if row and row.expires_at>int(time.time())+3300:raise HTTPException(429,'Wait five minutes before requesting another email')
    token=secrets.token_urlsafe(32)
    if not row:row=SellerEmailVerification(seller_id=seller,token_hash='',expires_at=0);db.add(row)
    row.token_hash=hashlib.sha256(token.encode()).hexdigest();row.expires_at=int(time.time())+3600
    db.add(MailQueue(id=uid(),recipient=account.email,subject='Verify your Roomform seller email',body='Enter this token in the seller verification panel within one hour:\n\n'+token));db.commit();return {'sent':True}
class Token(BaseModel):
    token:str=Field(min_length=30,max_length=200)
@router.post('/confirm')
def confirm(body:Token,seller=Depends(identity),db=Depends(get_db)):
    row=db.get(SellerEmailVerification,seller)
    if not row or row.verified_at or row.expires_at<=time.time() or not secrets.compare_digest(row.token_hash,hashlib.sha256(body.token.encode()).hexdigest()):raise HTTPException(422,'Verification token is invalid or expired')
    row.verified_at=int(time.time());db.commit();return {'verified':True}
