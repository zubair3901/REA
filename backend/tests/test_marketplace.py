import os
import tempfile
from io import BytesIO
from PIL import Image
os.environ['MERCHANT_KEYS_JSON']='{"demo":"test-key"}'
from fastapi.testclient import TestClient
from app.main import app
from app.seed import seed
from app.database import Session
from app.models import Asset, Lead, Outbox

def photo(transparent=False):
    b=BytesIO();im=Image.new('RGBA',(800,600),(180,180,175,0 if transparent else 255))
    if transparent:
        from PIL import ImageDraw
        ImageDraw.Draw(im).rectangle((100,100,400,400),fill='red')
    im.save(b,format='PNG');return b.getvalue()

def design(c,ids='["sofa","lamp"]',room=None):
    return c.post('/api/designs',data={'style':'Organic','asset_ids':ids,'room_area':25,'room_category':'living'},files={'room':('room.png',room if room is not None else photo(),'image/png')})

def test_render_quote_and_lead_outbox():
    seed()
    with TestClient(app) as c:
        r=design(c);assert r.status_code==201,r.text
        d=r.json();q=d['quote']
        assert q['items_subtotal']==1035 and q['labor']==200 and q['total']==1235
        assert q['timeline_days']==6
        assert {p['asset_id'] for p in d['placements']}=={'sofa','lamp'}
        assert d['render_mode']=='asset_composite'
        assert c.get(d['image_url']).headers['content-type']=='image/jpeg'
        lead=c.post('/api/leads',json={'design_id':d['id'],'name':'Test Buyer','email':'buyer@example.com','consent':True})
        assert lead.status_code==201
        with Session() as db:
            assert db.get(Lead,lead.json()['id']) is not None
            assert db.query(Outbox).filter_by(lead_id=lead.json()['id']).count()==1
        assert c.post('/api/leads',json={'design_id':d['id'],'name':'Test','email':'buyer@example.com','consent':False}).status_code==422

def test_reject_bad_inventory_and_images():
    seed()
    with TestClient(app) as c:
        assert design(c,ids='["missing"]').status_code==409
        assert design(c,ids='["sofa","sofa"]').status_code==422
        assert design(c,room=b'not image').status_code==422
        assert design(c,ids='null').status_code==422
        assert c.get('/api/assets?latitude=24').status_code==422
        assert c.get('/api/assets?latitude=0&longitude=0&radius_km=1').json()==[]
        with Session() as db:
            a=db.get(Asset,'lamp');a.stock=0;db.commit()
        assert design(c).status_code==409
        with Session() as db:
            db.get(Asset,'lamp').stock=10;db.commit()

def test_merchant_isolation():
    seed()
    with TestClient(app) as c:
        assert c.post('/api/uploads',files={'file':('a.png',photo(True))}).status_code==401
        h={'X-Merchant-Key':'test-key'}
        assert c.post('/api/uploads',headers=h,files={'file':('a.png',photo())}).status_code==422
        r=c.post('/api/uploads',headers=h,files={'file':('a.png',photo(True))});assert r.status_code==201
        a={'seller_id':'other','name':'My chair','category':'Chair','style':'Organic','price':'12.50','currency':'USD','width_cm':60,'height_cm':80,'depth_cm':60,'latitude':24.86,'longitude':67,'stock':2,'delivery_days':3,'image_url':r.json()['image_url']}
        assert c.post('/api/assets',headers=h,json=a).status_code==403
        a['seller_id']='demo'
        assert c.post('/api/assets',headers=h,json=a).status_code==201
        a['image_url']='/media/../../secret.png'
        assert c.post('/api/assets',headers=h,json=a).status_code==422
