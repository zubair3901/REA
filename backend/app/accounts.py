import hashlib
import hmac
import secrets
import time
from uuid import uuid4
from typing import Literal
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .database import get_db
from .models import Seller, SellerAccount, SellerSession

router=APIRouter(prefix='/api/sellers')
class Login(BaseModel):
    email: str=Field(max_length=254,pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    password: str=Field(min_length=12,max_length=128)
class Register(Login):
    name: str=Field(min_length=2,max_length=160)
    kind: Literal['merchant','individual']

def password_hash(password,salt=None):
    salt=salt or secrets.token_hex(16)
    return salt+':'+hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()
def token_response(db,seller):
    token=secrets.token_urlsafe(32)
    db.add(SellerSession(token_hash=hashlib.sha256(token.encode()).hexdigest(),seller_id=seller.id,expires_at=int(time.time())+86400))
    db.commit()
    return {'seller_id':seller.id,'access_token':token,'status':'approved' if seller.active else 'pending','expires_in':86400}
def session_seller(db,key):
    if not key or len(key)>256: return None
    session=db.get(SellerSession,hashlib.sha256(key.encode()).hexdigest())
    return session.seller_id if session and session.expires_at>time.time() else None

@router.post('/register',status_code=201)
def register(body:Register,db=Depends(get_db)):
    email=body.email.strip().lower()
    if db.scalar(select(SellerAccount).where(SellerAccount.email==email)): raise HTTPException(409,'This email is already registered')
    seller=Seller(id=str(uuid4()),name=body.name,active=False)
    db.add(seller);db.flush()
    db.add(SellerAccount(seller_id=seller.id,email=email,password_hash=password_hash(body.password),kind=body.kind))
    try:return token_response(db,seller)
    except IntegrityError:
        db.rollback();raise HTTPException(409,'This email is already registered')
@router.post('/login')
def login(body:Login,db=Depends(get_db)):
    account=db.scalar(select(SellerAccount).where(SellerAccount.email==body.email.strip().lower()))
    salt=account.password_hash.split(':')[0] if account else '00'*16
    computed=password_hash(body.password,salt)
    if not account or not hmac.compare_digest(computed,account.password_hash): raise HTTPException(401,'Invalid email or password')
    return token_response(db,db.get(Seller,account.seller_id))
@router.post('/logout',status_code=204)
def logout(key:str=Header(alias='X-Merchant-Key'),db=Depends(get_db)):
    session=db.get(SellerSession,hashlib.sha256(key.encode()).hexdigest())
    if session: db.delete(session);db.commit()
