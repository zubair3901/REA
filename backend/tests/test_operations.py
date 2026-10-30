from fastapi.testclient import TestClient
from app.main import app
from app.seed import seed

def test_operator_auth_approval_and_inbox(monkeypatch):
    seed()
    monkeypatch.delenv('ROOM_OPERATOR_KEY',raising=False)
    with TestClient(app) as c:
        assert c.get('/api/operator/sellers').status_code==401
        monkeypatch.setenv('ROOM_OPERATOR_KEY','test-operator-only')
        assert c.get('/api/operator/leads').status_code==401
        h={'X-Operator-Key':'test-operator-only'}
        rows=c.get('/api/operator/sellers',headers=h).json()
        assert any(s['id']=='demo' for s in rows)
        assert all('password_hash' not in s for s in rows)
        assert c.patch('/api/operator/sellers/demo',headers=h,json={'active':False}).status_code==200
        assert all(a['seller_id']!='demo' for a in c.get('/api/assets').json())
        assert c.patch('/api/operator/sellers/demo',headers=h,json={'active':True}).status_code==200
        assert c.get('/api/operator/leads',headers=h).status_code==200

def test_bulk_listing_auth_and_validation():
    with TestClient(app) as c:
        assert c.post('/api/seller/listings/bulk',json={'assets':[]}).status_code==401
        assert c.post('/api/seller/listings/bulk',headers={'X-Merchant-Key':'test-key'},json={'assets':[]}).status_code==422

def test_bulk_publish_is_all_or_nothing():
    from io import BytesIO
    from PIL import Image,ImageDraw
    seed()
    with TestClient(app) as c:
        key={'X-Merchant-Key':'test-key'}
        im=Image.new('RGBA',(100,100));ImageDraw.Draw(im).rectangle((10,10,90,90),fill='brown')
        buf=BytesIO();im.save(buf,'PNG')
        upload=c.post('/api/uploads',headers=key,files={'file':('stock.png',buf.getvalue())}).json()
        item={'seller_id':'demo','name':'Supplier lamp','category':'lamp','style':'modern','price':40,'currency':'USD','width_cm':20,'height_cm':50,'depth_cm':20,'image_url':upload['image_url'],'latitude':24,'longitude':67,'stock':7,'delivery_days':2}
        before=len(c.get('/api/assets').json())
        r=c.post('/api/seller/listings/bulk',headers=key,json={'assets':[item,{**item,'seller_id':'not-owner'}]})
        assert r.status_code==403
        assert len(c.get('/api/assets').json())==before
        r=c.post('/api/seller/listings/bulk',headers=key,json={'assets':[item,{**item,'name':'Supplier second lamp'}]})
        assert r.status_code==201 and r.json()['created']==2
        assert len(c.get('/api/assets').json())==before+2
