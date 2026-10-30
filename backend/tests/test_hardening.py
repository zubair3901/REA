import hashlib,time
import pyotp
from fastapi.testclient import TestClient
from app.main import app
from app.database import Session
from app.accounts import password_hash
from app.workspace_models import Administrator,Organization
from test_workspace import register,project,auth_reset

def test_admin_requires_totp_and_rejects_replay(monkeypatch):
    auth_reset();monkeypatch.setenv('ALLOW_LEGACY_OPERATOR_KEY','false')
    secret=pyotp.random_base32()
    with Session() as db:
        db.add(Administrator(id='admin-test',email='admin@example.com',password_hash=password_hash('strong-admin-password'),totp_secret=secret));db.commit()
    with TestClient(app) as c:
        assert c.get('/api/operator/sellers',headers={'X-Operator-Key':'anything'}).status_code==401
        body={'email':'admin@example.com','password':'strong-admin-password','code':'bad'}
        assert c.post('/api/admin/login',json=body).status_code==422
        body['code']=pyotp.TOTP(secret).now()
        response=c.post('/api/admin/login',json=body)
        assert response.status_code==200,response.text
        assert 'HttpOnly' in response.headers['set-cookie']
        assert c.get('/api/operator/sellers').status_code==200
        assert c.post('/api/admin/login',json=body).status_code==401
        assert c.post('/api/admin/logout').status_code==200
        assert c.get('/api/operator/sellers').status_code==401

def test_expired_organization_blocks_existing_projects(monkeypatch):
    auth_reset()
    with TestClient(app) as c:
        register(c)
        org=c.post('/api/workspace/organizations',json={'name':'Studio','plan':'basic'}).json()
        with Session() as db:db.get(Organization,org['id']).expires_at=int(time.time())+3600;db.commit()
        p=project(c,organization_id=org['id'])
        with Session() as db:db.get(Organization,org['id']).expires_at=1;db.commit()
        assert c.get('/api/workspace/projects/'+p['id']).status_code==403
        assert c.patch('/api/workspace/projects/'+p['id'],json={'status':'completed'}).status_code==403

def test_email_verification_gate_and_one_time_confirmation(monkeypatch):
    auth_reset();monkeypatch.setenv('REQUIRE_VERIFIED_EMAIL','true')
    monkeypatch.setenv('SMTP_HOST','mail.test');monkeypatch.setenv('SMTP_FROM','roomform@example.com');monkeypatch.setenv('APP_URL','https://staging.example.com')
    from app.workspace_models import MailQueue
    from sqlalchemy import select
    with TestClient(app) as c:
        register(c)
        assert c.post('/api/workspace/projects',json={'name':'Test home','location':'Karachi','budget':2000}).status_code==403
        assert c.post('/api/workspace/verification/send').status_code==200
        with Session() as db:token=db.scalar(select(MailQueue)).body.split('\n\n')[1]
        assert c.post('/api/workspace/verification/confirm',json={'token':token}).status_code==200
        assert c.post('/api/workspace/verification/confirm',json={'token':token}).status_code==422
        project(c)

def test_signed_payment_webhook_amount_and_replay(monkeypatch):
    import json,hmac
    from app.workspace_models import PaymentRequest
    auth_reset();monkeypatch.setenv('STRIPE_WEBHOOK_SECRET','webhook-test-secret')
    with TestClient(app) as c:
        user=register(c);p=project(c)
        with Session() as db:
            db.add(PaymentRequest(id='payment-test',project_id=p['id'],customer_id=user['id'],package='starter',amount=3,credits=3,status='awaiting_payment'));db.commit()
        event={'id':'evt_test','type':'checkout.session.completed','livemode':False,'data':{'object':{'metadata':{'payment_id':'payment-test'},'payment_status':'paid','currency':'usd','amount_total':300}}}
        raw=json.dumps(event).encode();timestamp=str(int(time.time()))
        signature=hmac.new(b'webhook-test-secret',timestamp.encode()+b'.'+raw,hashlib.sha256).hexdigest()
        headers={'stripe-signature':'t='+timestamp+',v1='+signature,'Content-Type':'application/json'}
        assert c.post('/api/payments/stripe/webhook',content=raw).status_code==400
        assert c.post('/api/payments/stripe/webhook',content=raw,headers=headers).status_code==200
        assert c.post('/api/payments/stripe/webhook',content=raw,headers=headers).status_code==200
        assert c.get('/api/workspace/projects/'+p['id']).json()['credits']==3

def test_seller_email_verification_before_inventory(monkeypatch):
    from sqlalchemy import select
    from app.workspace_models import MailQueue
    from app.models import Seller
    auth_reset();monkeypatch.setenv('REQUIRE_VERIFIED_EMAIL','true');monkeypatch.setenv('SMTP_HOST','mail.test');monkeypatch.setenv('SMTP_FROM','roomform@example.com')
    with TestClient(app) as c:
        response=c.post('/api/sellers/register',json={'name':'Karachi Furniture','email':'seller@example.com','password':'seller-test-password','kind':'merchant'})
        assert response.status_code==201,response.text
        seller=response.json();headers={'X-Merchant-Key':seller['access_token']}
        with Session() as db:db.get(Seller,seller['seller_id']).active=True;db.commit()
        assert c.get('/api/seller/listings',headers=headers).status_code==403
        assert c.post('/api/sellers/verification/send',headers=headers).status_code==200
        with Session() as db:token=db.scalar(select(MailQueue)).body.split('\n\n')[1]
        assert c.post('/api/sellers/verification/confirm',headers=headers,json={'token':token}).status_code==200
        assert c.get('/api/seller/listings',headers=headers).status_code==200
