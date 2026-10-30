from fastapi.testclient import TestClient
from app.main import app
from app.database import Session
from app.models import Seller
import uuid

def test_individual_onboarding_approval_and_session():
    with TestClient(app) as c:
        email=f'{uuid.uuid4().hex}@example.com'
        body={'name':'Local seller','email':email,'password':'a-long-test-password','kind':'individual'}
        r=c.post('/api/sellers/register',json=body)
        assert r.status_code==201,r.text
        data=r.json();assert data['status']=='pending'
        assert c.post('/api/sellers/register',json=body).status_code==409
        assert c.post('/api/sellers/login',json={'email':email,'password':'wrong-password-here'}).status_code==401
        login=c.post('/api/sellers/login',json={'email':email,'password':body['password']})
        assert login.status_code==200 and login.json()['status']=='pending'
        key={'X-Merchant-Key':data['access_token']}
        assert c.get('/api/seller/listings',headers=key).status_code==200
        with Session() as db:
            seller=db.get(Seller,data['seller_id']);seller.active=True;db.commit()
        assert c.post('/api/sellers/login',json={'email':email,'password':body['password']}).json()['status']=='approved'
        assert c.post('/api/sellers/logout',headers=key).status_code==204
        assert c.get('/api/seller/listings',headers=key).status_code==401

def test_listing_owner_controls_and_used_item_details():
    from io import BytesIO
    from PIL import Image,ImageDraw
    with TestClient(app) as c:
        body={'name':'Used Furniture Seller','email':f'{uuid.uuid4().hex}@example.com','password':'a-long-test-password','kind':'individual'}
        account=c.post('/api/sellers/register',json=body).json()
        key={'X-Merchant-Key':account['access_token']}
        image=Image.new('RGBA',(200,200));ImageDraw.Draw(image).rectangle((20,20,180,180),fill='brown')
        buffer=BytesIO();image.save(buffer,'PNG')
        upload=c.post('/api/uploads',headers=key,files={'file':('chair.png',buffer.getvalue())})
        assert upload.status_code==201
        listing={'seller_id':account['seller_id'],'name':'Secondhand chair','category':'chair','style':'modern','price':75,'currency':'USD','width_cm':70,'height_cm':85,'depth_cm':65,'image_url':upload.json()['image_url'],'latitude':24.8,'longitude':67,'stock':1,'delivery_days':3,'condition':'good','delivery_location':'Karachi','delivery_radius_km':15}
        assert c.post('/api/assets',headers=key,json=listing).status_code==403
        with Session() as db:
            db.get(Seller,account['seller_id']).active=True;db.commit()
        response=c.post('/api/assets',headers=key,json=listing)
        assert response.status_code==201,response.text
        ident=response.json()['id']
        assert c.patch('/api/assets/'+ident,headers=key,json={'stock':2,'price':80}).status_code==200
        own=c.get('/api/seller/listings',headers=key).json()
        assert own[0]['condition']=='good' and own[0]['delivery_radius_km']==15
        assert c.patch('/api/assets/'+ident,json={'stock':0}).status_code==401
        assert c.patch('/api/assets/'+ident,headers=key,json={'price':None}).status_code==422
