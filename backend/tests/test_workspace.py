import time
from io import BytesIO
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.database import Session
from app.models import Asset, Seller
from app.workspace_models import CustomerSession, Project, Professional, PaymentRequest, Organization, Order
from app.seed import seed

OP={'X-Operator-Key':'workspace-operator-test'}
def register(c,email='home@example.com'):
    response=c.post('/api/workspace/register',json={'name':'Home Owner','email':email,'password':'secure-test-password'})
    assert response.status_code==201,response.text
    return response.json()
def project(c,**overrides):
    r=c.post('/api/workspace/projects',json={'name':'Karachi living room','location':'Clifton, Karachi','budget':2500,'currency':'USD','preference':'either',**overrides})
    assert r.status_code==201,r.text
    return r.json()
def photo():
    b=BytesIO();Image.new('RGB',(800,600),'beige').save(b,'PNG');return b.getvalue()
def auth_reset():
    middleware=app.middleware_stack
    while middleware:
        if hasattr(middleware,'attempts'):middleware.attempts.clear()
        middleware=getattr(middleware,'app',None)

def test_customer_persistence_privacy_and_csrf(monkeypatch):
    auth_reset();seed();monkeypatch.setenv('ALLOW_GUEST_PREVIEWS','false')
    with TestClient(app) as owner, TestClient(app) as other:
        register(owner);p=project(owner)
        assert 'HttpOnly' in owner.post('/api/workspace/login',json={'email':'home@example.com','password':'secure-test-password'}).headers['set-cookie']
        assert owner.post('/api/workspace/projects',json={},headers={'Origin':'https://evil.example'}).status_code==403
        response=owner.post('/api/designs',data={'project_id':p['id'],'style':'modern','asset_ids':'["sofa"]','room_area':20,'room_category':'living'},files={'room':('room.png',photo(),'image/png')})
        assert response.status_code==201,response.text
        design=response.json()
        assert owner.get(design['image_url']).status_code==200
        assert other.get(design['image_url']).status_code==401
        register(other,'other@example.com')
        assert other.get('/api/workspace/projects/'+p['id']).status_code==404
        assert other.get(design['image_url']).status_code==404
        assert other.post('/api/leads',json={'design_id':design['id'],'name':'No Access','email':'test@example.com','consent':True}).status_code==404
        assert len(owner.get('/api/workspace/projects/'+p['id']).json()['designs'])==1
        old_cookie=owner.cookies.get('roomform_session')
        assert owner.post('/api/workspace/logout').status_code==200
        owner.cookies.set('roomform_session',old_cookie)
        assert owner.get('/api/workspace/me').status_code==401

def test_packages_reconciliation_exactly_once(monkeypatch):
    auth_reset();monkeypatch.setenv('ROOM_OPERATOR_KEY','workspace-operator-test')
    monkeypatch.setenv('PAYMENT_INSTRUCTIONS','Use the bank details on your invoice.');monkeypatch.setenv('ENABLE_PROJECT_SALES','false')
    with TestClient(app) as c:
        register(c);p=project(c)
        path='/api/workspace/projects/'+p['id']+'/checkout'
        assert c.post(path,json={'package':'starter'}).status_code==503
        monkeypatch.setenv('ENABLE_PROJECT_SALES','true')
        pay=c.post(path,json={'package':'starter'}).json()
        assert float(pay['amount'])==3 and pay['credits']==3
        assert c.post(path,json={'package':'starter'}).json()['id']==pay['id']
        decision={'status':'approved','note':'Bank transaction independently verified'}
        assert c.patch('/api/operator/platform/payments/'+pay['id'],json=decision,headers=OP).status_code==409
        assert c.post('/api/workspace/payments/'+pay['id']+'/reference',json={'reference':'BANK-REF-123'}).status_code==200
        assert c.patch('/api/operator/platform/payments/'+pay['id'],json=decision).status_code==401
        assert c.patch('/api/operator/platform/payments/'+pay['id'],json=decision,headers=OP).status_code==200
        assert c.patch('/api/operator/platform/payments/'+pay['id'],json=decision,headers=OP).status_code==409
        assert c.get('/api/workspace/projects/'+p['id']).json()['credits']==3

def test_team_seats_and_removed_member_access(monkeypatch):
    auth_reset();monkeypatch.setenv('ROOM_OPERATOR_KEY','workspace-operator-test')
    with TestClient(app) as owner,TestClient(app) as teammate,TestClient(app) as third,TestClient(app) as fourth:
        register(owner);member=register(teammate,'colleague@example.com');register(third,'third@example.com');register(fourth,'fourth@example.com')
        org=owner.post('/api/workspace/organizations',json={'name':'Karachi Studio','plan':'ultra'}).json()
        path='/api/workspace/organizations/'+org['id']+'/members'
        assert owner.post(path,json={'email':'colleague@example.com'}).status_code==403
        assert owner.patch('/api/operator/platform/organizations/'+org['id'],json={'plan':'ultra','seats':999,'days':30,'reference':'Contract signed 123'},headers=OP).json()['seats']==3
        assert owner.post(path,json={'email':'colleague@example.com'}).status_code==200
        assert owner.post(path,json={'email':'third@example.com'}).status_code==200
        assert owner.post(path,json={'email':'fourth@example.com'}).status_code==409
        assert teammate.post(path,json={'email':'fourth@example.com'}).status_code==403
        p=project(teammate,organization_id=org['id'])
        assert owner.get('/api/workspace/projects/'+p['id']).status_code==200
        assert owner.delete(path+'/'+member['id']).status_code==200
        assert teammate.get('/api/workspace/projects/'+p['id']).status_code==404
        assert teammate.get('/api/workspace/projects').json()==[]

def test_professional_quote_and_consultation_lifecycle(monkeypatch):
    auth_reset();monkeypatch.setenv('ROOM_OPERATOR_KEY','workspace-operator-test')
    with TestClient(app) as buyer,TestClient(app) as pro:
        register(buyer);register(pro,'painter@example.com');p=project(buyer)
        profile=pro.post('/api/workspace/professional/profile',json={'name':'Karachi Paint Studio','trade':'painter','location':'Karachi','description':'Interior painting and wall repairs with careful preparation.','phone':'+923001234567','daily_rate':5000,'currency':'PKR'}).json()
        assert buyer.get('/api/workspace/professionals').json()==[]
        body={'project_id':p['id'],'professional_id':profile['id'],'brief':'Paint my living room and repair the plaster.','phone':'+923001234567','consent':True}
        assert buyer.post('/api/workspace/services',json=body).status_code==409
        assert buyer.patch('/api/operator/platform/professionals/'+profile['id'],headers=OP,json={'status':'approved'}).status_code==200
        public=buyer.get('/api/workspace/professionals?location=Karachi&trade=painter').json()
        assert len(public)==1 and 'phone' not in public[0]
        job=buyer.post('/api/workspace/services',json=body).json()
        quote={'amount':15000,'response':'Three days including wall preparation; paint purchased separately.'}
        assert buyer.post('/api/workspace/services/'+job['id']+'/quote',json=quote).status_code==403
        assert pro.post('/api/workspace/services/'+job['id']+'/quote',json=quote).status_code==200
        assert buyer.patch('/api/workspace/services/'+job['id'],json={'status':'accepted'}).status_code==200
        assert pro.post('/api/workspace/services/'+job['id']+'/quote',json=quote).status_code==409
        assert pro.patch('/api/workspace/services/'+job['id'],json={'status':'scheduled'}).status_code==200
        assert pro.patch('/api/workspace/services/'+job['id'],json={'status':'completed'}).status_code==200
        consultation=buyer.post('/api/workspace/services',json={**body,'professional_id':None}).json()
        assert buyer.patch('/api/operator/platform/services/'+consultation['id'],headers=OP,json={'status':'scheduled','response':'Confirmed consultation Tuesday at 10 AM, no fee.'}).status_code==200
        assert len(buyer.get('/api/workspace/projects/'+p['id']+'/activity').json()['services'])==2

def real_inventory():
    seed()
    with Session() as db:
        db.add(Seller(id='real',name='Real Furniture'));db.flush()
        source=db.get(Asset,'chair')
        fields={c.name:getattr(source,c.name) for c in Asset.__table__.columns if c.name not in ('id','seller_id')}
        fields['stock']=2
        db.add(Asset(id='actual-chair',seller_id='real',**fields));db.commit()

def test_orders_stock_reservation_cancellation_and_transitions(monkeypatch):
    auth_reset();real_inventory();monkeypatch.setenv('MERCHANT_KEYS_JSON','{"real":"seller-secret","demo":"test-key"}')
    headers={'X-Merchant-Key':'seller-secret'}
    with TestClient(app) as c:
        register(c);p=project(c)
        body={'project_id':p['id'],'items':[{'asset_id':'actual-chair','quantity':2}],'address':'12 Main Road, Clifton, Karachi','phone':'+923001234567','consent':True}
        assert c.post('/api/workspace/orders',json={**body,'items':[{'asset_id':'chair','quantity':1}]}).status_code==422
        first=c.post('/api/workspace/orders',json=body).json()['orders'][0]
        second=c.post('/api/workspace/orders',json=body).json()['orders'][0]
        path='/api/seller/orders/'+first['id']
        assert c.patch(path,headers={'X-Merchant-Key':'test-key'},json={'status':'confirmed'}).status_code==404
        assert c.patch(path,headers=headers,json={'status':'delivered'}).status_code==409
        assert c.patch(path,headers=headers,json={'status':'confirmed'}).status_code==200
        assert c.patch('/api/seller/orders/'+second['id'],headers=headers,json={'status':'confirmed'}).status_code==409
        with Session() as db:assert db.get(Asset,'actual-chair').stock==0
        assert c.post('/api/workspace/orders/'+first['id']+'/cancel').status_code==200
        assert c.post('/api/workspace/orders/'+first['id']+'/cancel').status_code==409
        with Session() as db:assert db.get(Asset,'actual-chair').stock==2
        assert c.patch('/api/seller/orders/'+second['id'],headers=headers,json={'status':'confirmed'}).status_code==200
        assert c.patch('/api/seller/orders/'+second['id'],headers=headers,json={'status':'dispatched'}).status_code==200
        assert c.post('/api/workspace/orders/'+second['id']+'/cancel').status_code==409
        assert c.patch('/api/seller/orders/'+second['id'],headers=headers,json={'status':'delivered'}).status_code==200
