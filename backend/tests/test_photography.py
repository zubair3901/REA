import json,base64
from io import BytesIO
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app.database import Session
from app.models import Asset,Seller
from app.workspace_models import ProductPhoto,DesignScene
from app.seed import seed
from test_marketplace import photo
from test_workspace import register,project,auth_reset
import httpx
import pytest

def prepared(c,headers={'X-Merchant-Key':'test-key'},angle='front'):
    r=c.post('/api/seller/photos',headers=headers,data={'angle':angle},files={'file':('chair.png',photo(True),'image/png')})
    assert r.status_code==201,r.text
    return r.json()
def approve(c,p,headers={'X-Merchant-Key':'test-key'}):
    r=c.post('/api/seller/photos/'+p['id']+'/approve',headers=headers,json={'approved':True,'rights_confirmed':True});assert r.status_code==200,r.text

def test_photo_privacy_review_ownership_and_listing(monkeypatch):
    seed();monkeypatch.setenv('ALLOW_LEGACY_PHOTOS','false');monkeypatch.setenv('MERCHANT_KEYS_JSON','{"demo":"test-key","other":"other-key"}')
    with Session() as db:db.add(Seller(id='other',name='Other',active=True));db.commit()
    h={'X-Merchant-Key':'test-key'}
    with TestClient(app) as c:
        p=prepared(c);assert p['quality']['method']=='supplied_alpha'
        assert c.patch('/api/seller/photos/'+p['id'],headers=h,json={'angle':'angled'}).json()['angle']=='angled'
        assert c.get(p['original_url']).status_code==401
        assert c.get(p['original_url'],headers=h).status_code==200
        assert c.post('/api/seller/photos/'+p['id']+'/approve',headers={'X-Merchant-Key':'other-key'},json={'approved':True,'rights_confirmed':True}).status_code==404
        body={'seller_id':'demo','name':'Actual sofa','category':'sofa','style':'modern','price':100,'currency':'USD','width_cm':200,'height_cm':80,'depth_cm':90,'latitude':24.86,'longitude':67,'stock':1,'delivery_days':2,'image_url':p['cutout_url'],'photo_ids':[p['id']]}
        assert c.post('/api/assets',headers=h,json=body).status_code==422
        approve(c,p)
        listing=c.post('/api/assets',headers=h,json=body);assert listing.status_code==201,listing.text
        assert c.get('/api/assets').status_code==200
        detail=c.get('/api/assets/'+listing.json()['id']).json();assert detail['photos'][0]['angle']=='angled'
        assert c.get(p['original_url']).status_code==200
        assert c.delete('/api/seller/photos/'+p['id'],headers=h).status_code==409
        other=prepared(c,angle='left');assert c.delete('/api/seller/photos/'+other['id'],headers=h).status_code==200
        assert c.get(other['original_url']).status_code==404

def test_provider_uses_multiple_actual_angles(monkeypatch):
    seed();monkeypatch.setenv('ROOM_OPENAI_API_KEY','not-a-real-key')
    with TestClient(app) as c:
        for angle in ('front','right'):
            p=prepared(c,angle=angle);approve(c,p)
            with Session() as db:db.get(ProductPhoto,p['id']).asset_id='sofa';db.commit()
        real=httpx.AsyncClient
        def handler(request):
            assert request.content.count(b'name="image[]"')==3
            assert b'"angle": "right"' in request.content and b'ONE item' in request.content
            return httpx.Response(200,json={'data':[{'b64_json':base64.b64encode(photo()).decode()}]})
        monkeypatch.setattr('app.generation.httpx.AsyncClient',lambda **kw:real(transport=httpx.MockTransport(handler),**kw))
        r=c.post('/api/designs',data={'style':'modern','asset_ids':'["sofa"]','room_area':20,'room_category':'living','model':'openai','ai_consent':'true'},files={'room':('room.png',photo(),'image/png')})
        assert r.status_code==201,r.text
        assert len(r.json()['placements'][0]['reference_photo_ids'])==2

@pytest.mark.parametrize('provider',['openai','gemini'])
def test_masked_replacement_preserves_outside_pixels_and_budget(monkeypatch,provider):
    seed();auth_reset();monkeypatch.setenv('ROOM_OPENAI_API_KEY','not-a-real-key');monkeypatch.setenv('ROOM_GEMINI_API_KEY','not-a-real-key')
    with TestClient(app) as c:
        register(c);pr=project(c,budget=5000)
        source=c.post('/api/designs',data={'project_id':pr['id'],'style':'modern','asset_ids':'["sofa","lamp"]','room_area':20,'room_category':'living','budget_ceiling':'5000','budget_currency':'USD','budget_confirmed':'true'},files={'room':('room.png',photo(),'image/png')})
        assert source.status_code==201,source.text
        design=source.json();original=Image.open(BytesIO(c.get(design['image_url']).content)).convert('RGB')
        body={'old_asset_id':'sofa','new_asset_id':'chair','region':{'x':.1,'y':.3,'width':.4,'height':.5},'model':provider,'ai_consent':True,'confirm_region':True}
        with TestClient(app) as stranger:assert stranger.post('/api/designs/'+design['id']+'/replace',json=body).status_code==401
        real=httpx.AsyncClient
        def handler(request):
            if provider=='openai':assert b'name="mask"' in request.content and b'Edit only the masked region' in request.content
            else:
                payload=json.loads(request.content);assert 'edit mask' in payload['contents'][0]['parts'][-2]['text']
            data=BytesIO();Image.new('RGB',original.size,'red').save(data,'PNG');encoded=base64.b64encode(data.getvalue()).decode()
            return httpx.Response(200,json={'data':[{'b64_json':encoded}]} if provider=='openai' else {'candidates':[{'content':{'parts':[{'inlineData':{'data':encoded}}]}}]})
        monkeypatch.setattr('app.generation.httpx.AsyncClient',lambda **kw:real(transport=httpx.MockTransport(handler),**kw))
        r=c.post('/api/designs/'+design['id']+'/replace',json=body);assert r.status_code==201,r.text
        child=r.json();assert child['outside_region_preserved'] and child['parent_id']==design['id']
        result=Image.open(BytesIO(c.get(child['image_url']).content)).convert('RGB')
        assert result.getpixel((0,0))==original.getpixel((0,0))
        assert result.getpixel((160,240))==(255,0,0)
        assert {i['asset_id'] for i in child['quote']['items']}=={'chair','lamp'}
        assert c.get('/api/designs/'+design['id']).status_code==200
        with TestClient(app) as stranger:assert stranger.get(child['image_url']).status_code==401
        # A changed price cannot bypass the saved ceiling.
        with Session() as db:db.get(Asset,'chair').price=9000;db.commit()
        assert c.post('/api/designs/'+design['id']+'/replace',json=body).status_code==409

def test_grounding_rejects_hallucinated_and_invalid_boxes(monkeypatch):
    import asyncio
    from app.localization import locate_products
    from app.database import DATA
    seed();monkeypatch.setenv('ENABLE_AI_HOTSPOTS','true');monkeypatch.setenv('ROOM_OPENAI_API_KEY','not-real')
    real=httpx.AsyncClient
    def handler(request):return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps({'hotspots':[{'asset_id':'sofa','x':.1,'y':.2,'width':.3,'height':.3,'confidence':.9},{'asset_id':'invented','x':.1,'y':.2,'width':.3,'height':.3,'confidence':1},{'asset_id':'lamp','x':.9,'y':.9,'width':.3,'height':.3,'confidence':1}]})}}]})
    monkeypatch.setattr('app.localization.httpx.AsyncClient',lambda **kw:real(transport=httpx.MockTransport(handler),**kw))
    with Session() as db:
        assets=[db.get(Asset,'sofa'),db.get(Asset,'lamp')]
        result=asyncio.run(locate_products('openai',Image.new('RGB',(500,500),'white'),assets,DATA/'media'))
    assert len(result)==1 and result[0]['asset_id']=='sofa' and result[0]['source']=='ai_suggested'

def test_daily_ai_cap_blocks_before_provider_request(monkeypatch):
    seed();auth_reset();monkeypatch.setenv('ROOM_OPENAI_API_KEY','not-real');monkeypatch.setenv('ROOM_AI_DAILY_LIMIT','0')
    with TestClient(app) as c:
        register(c);pr=project(c)
        r=c.post('/api/designs',data={'project_id':pr['id'],'style':'modern','asset_ids':'["sofa"]','room_area':20,'room_category':'living','model':'openai','ai_consent':'true'},files={'room':('room.png',photo(),'image/png')})
        assert r.status_code==429 and 'No provider request was sent' in r.json()['detail']
