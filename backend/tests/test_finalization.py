from decimal import Decimal
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.database import Session
from app.models import Asset,Seller,Design
from app.workspace_models import AssetFulfillment,ProjectDesign,FinalizationBooking,MailQueue
from test_workspace import register,project

def fixture(c):
    register(c);p=project(c)
    with Session() as db:
        db.add(Seller(id='real',name='Actual shop'));db.flush()
        db.add(Asset(id='sku-real',seller_id='real',name='Chair <actual> '+('Long ' * 30),category='chair',style='modern',price=Decimal('100'),currency='USD',width_cm=60,height_cm=80,depth_cm=60,image_url='/media/missing.png',latitude=24.86,longitude=67,stock=2,delivery_days=5));db.flush()
        db.add(Design(id='design-real',style='modern',image_url='/media/missing.png',render_mode='composite',placements=[],quote={'items':[{'asset_id':'sku-real','quantity':2}],'currency':'USD','labor':30,'installation_days':2,'exclusions':['Taxes','Shipping fees']}));db.flush();db.add(ProjectDesign(design_id='design-real',project_id=p['id']));db.commit()
    return p

def test_booking_snapshot_pdf_idempotency_privacy_and_email(monkeypatch):
    monkeypatch.setenv('FINALIZATION_SERVICE_FEES_JSON','{"USD":25}');monkeypatch.setenv('FINALIZATION_EMAIL','ops@example.com')
    with TestClient(app) as c:
        p=fixture(c);url='/api/workspace/projects/'+p['id']+'/finalizations'
        missing=c.post(url+'/preview',json={'design_id':'design-real'}).json();assert missing['issues'] and missing['min_days'] is None
        headers={'X-Merchant-Key':'real-key'};monkeypatch.setenv('MERCHANT_KEYS_JSON','{"real":"real-key"}')
        timing={'ready_min_days':3,'ready_max_days':6,'delivery_min_days':2,'delivery_max_days':4}
        assert c.put('/api/assets/sku-real/fulfillment',json=timing,headers=headers).status_code==200
        assert c.put('/api/assets/sku-real/fulfillment',json={**timing,'ready_min_days':7},headers=headers).status_code==422
        estimate=c.post(url+'/preview',json={'design_id':'design-real'}).json();assert estimate['min_days']==7 and estimate['max_days']==12 and estimate['total']=='255.00'
        body={'design_id':'design-real','phone':'+923001234567','address':'House 12 Clifton Karachi','consent':True,'idempotency_key':'test-booking-0001'}
        response=c.post(url,json=body);assert response.status_code==201,response.text
        booking=response.json();assert booking['email_status']=='pending'
        assert c.post(url,json=body).json()['id']==booking['id']
        assert c.post(url,json={**body,'phone':'+923001234568'}).status_code==409
        pdf=c.get(booking['pdf_url']);assert pdf.status_code==200 and pdf.content.startswith(b'%PDF-') and 'no-store' in pdf.headers['cache-control']
        with Session() as db:
            assert len(db.query(FinalizationBooking).all())==1 and len(db.query(MailQueue).all())==1
            db.get(Asset,'sku-real').price=999;db.commit()
        saved=c.get(url).json()[0];assert saved['snapshot']['total']=='255.00'
        with TestClient(app) as stranger:
            assert stranger.get(booking['pdf_url']).status_code==401
            register(stranger,'outsider@example.com');assert stranger.get(booking['pdf_url']).status_code==404
        monkeypatch.setenv('SMTP_HOST','smtp.example.com');monkeypatch.setenv('SMTP_FROM','from@example.com')
        from app.mail_worker import run
        with patch('smtplib.SMTP') as smtp:
            run();message=smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
            assert list(message.iter_attachments())[0].get_content_type()=='application/pdf'

def test_booking_rejects_missing_fee_stock_and_foreign_design(monkeypatch):
    monkeypatch.delenv('FINALIZATION_SERVICE_FEES_JSON',raising=False)
    with TestClient(app) as c:
        p=fixture(c);url='/api/workspace/projects/'+p['id']+'/finalizations'
        preview=c.post(url+'/preview',json={'design_id':'design-real'}).json();assert preview['service_charge'] is None
        body={'design_id':'design-real','phone':'123456789','address':'A sufficiently long address','consent':True,'idempotency_key':'test-denied-001'}
        assert c.post(url,json=body).status_code==409
        other=project(c);assert c.post('/api/workspace/projects/'+other['id']+'/finalizations/preview',json={'design_id':'design-real'}).status_code==404
        monkeypatch.setenv('FINALIZATION_SERVICE_FEES_JSON','{"USD":0}')
        with Session() as db:
            db.get(Asset,'sku-real').stock=0;db.commit()
        assert any('availability' in i for i in c.post(url+'/preview',json={'design_id':'design-real'}).json()['issues'])
