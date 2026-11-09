from fastapi.testclient import TestClient
from app.main import app
from app.database import Session
from app.models import Asset,Seller
from app.workspace_models import Order,SellerDeliveryPlan
from test_workspace import auth_reset,register,project,real_inventory,OP

def setup(monkeypatch):
    auth_reset();real_inventory();monkeypatch.setenv('MERCHANT_KEYS_JSON','{"real":"seller-secret","demo":"test-key"}');monkeypatch.setenv('ROOM_OPERATOR_KEY','workspace-operator-test')
    return {'X-Merchant-Key':'seller-secret'}

def test_catalog_validation_variant_ownership_and_edits(monkeypatch):
    headers=setup(monkeypatch)
    with TestClient(app) as c:
        path='/api/assets/actual-chair/catalog-details'
        assert c.get(path).status_code==401
        assert c.get(path,headers={'X-Merchant-Key':'test-key'}).status_code==404
        body={'sku':'CHAIR-1','style_tags':['minimalist','industrial','traditional'],'dominant_colors':[{'name':'Walnut','hex':'#493020'}],'materials':['Walnut'],'weight_kg':12,'shipping_weight_kg':15,'shipping_dimensions_cm':{'width':80,'height':100,'depth':80},'msrp':'200','sale_price':'150'}
        r=c.put(path,headers=headers,json=body);assert r.status_code==200,r.text
        assert r.json()['details']['sku']=='CHAIR-1'
        assert c.put(path,headers=headers,json={**body,'dominant_colors':[{'name':'Bad','hex':'red'}]}).status_code==422
        assert c.put(path,headers=headers,json={**body,'parent_asset_id':'chair'}).status_code==404
        assert c.put(path,headers=headers,json={**body,'parent_asset_id':'actual-chair'}).status_code==422
        with Session() as db:
            a=db.get(Asset,'actual-chair');fields={col.name:getattr(a,col.name) for col in Asset.__table__.columns if col.name not in ('id',)};db.add(Asset(id='other-chair',**fields));db.commit()
        assert c.put('/api/assets/other-chair/catalog-details',headers=headers,json=body).status_code==409
        assert c.put('/api/assets/other-chair/catalog-details',headers=headers,json={'parent_asset_id':'actual-chair'}).status_code==200
        assert c.put(path,headers=headers,json={'parent_asset_id':'other-chair'}).status_code==422
        update={'name':'Updated actual chair','category':'accent-chair','style':'bohemian','width_cm':65,'height_cm':82,'depth_cm':70,'condition':'good','latitude':24.8,'longitude':67.1,'delivery_radius_km':25,'delivery_location':'Karachi'}
        r=c.patch('/api/assets/actual-chair',headers=headers,json=update);assert r.status_code==200,r.text
        assert r.json()['name']=='Updated actual chair'
        assert c.patch('/api/assets/actual-chair',headers=headers,json={'image_url':'/media/foreign.png'}).status_code==422
        assert c.patch('/api/assets/actual-chair',headers=headers,json={'seller_id':'demo'}).status_code==422
        assert c.patch('/api/assets/actual-chair',headers=headers,json={'latitude':999}).status_code==422
        from app.workspace_models import ProductPhoto
        from app.main import MEDIA
        from PIL import Image
        Image.new('RGBA',(20,20),(120,80,30,128)).save(MEDIA/'real_approved.png')
        with Session() as db:
            db.add(ProductPhoto(id='approved-photo',seller_id='real',asset_id=None,angle='front',original_file='approved-photo.png',cutout_url='/media/real_approved.png',quality={},approved=1));db.commit()
        assert c.patch('/api/assets/actual-chair',headers=headers,json={'photo_ids':['approved-photo'],'image_url':'/media/real_approved.png'}).status_code==200
        assert c.patch('/api/assets/chair',headers={'X-Merchant-Key':'test-key'},json={'photo_ids':['approved-photo'],'image_url':'/media/real_approved.png'}).status_code==403


def test_platform_delivery_schedule_and_seller_redaction(monkeypatch):
    headers=setup(monkeypatch)
    with TestClient(app) as c:
        register(c);p=project(c)
        body={'project_id':p['id'],'items':[{'asset_id':'actual-chair','quantity':1}],'address':'Buyer private address in Karachi','phone':'+923001234567','consent':True}
        order=c.post('/api/workspace/orders',json=body).json()['orders'][0]
        schedule='/api/operator/platform/orders/'+order['id']+'/delivery-plan'
        delivery={'delivery_date':'2027-01-06','address':'Roomform receiving depot, Karachi','instructions':'Deliver one chair by 4 PM; contact platform operations.'}
        assert c.patch('/api/seller/orders/'+order['id'],headers=headers,json={'status':'confirmed'}).status_code==200
        assert c.patch('/api/seller/orders/'+order['id'],headers=headers,json={'status':'dispatched'}).status_code==409
        assert c.put(schedule,json=delivery).status_code==401
        assert c.put(schedule,headers=OP,json={**delivery,'delivery_date':'bad'}).status_code==422
        assert c.put(schedule,headers=OP,json=delivery).status_code==200
        r=c.get('/api/seller/orders',headers=headers).json()[0]
        assert r['address']==delivery['address'] and r['delivery_date']=='2027-01-06'
        for key in ('phone','customer_id','project_id','total','currency','commission'):assert key not in r
        assert set(r['items'][0])=={'asset_id','name','quantity'}
        r=c.patch('/api/seller/orders/'+order['id'],headers=headers,json={'status':'dispatched'}).json()
        assert 'phone' not in r and 'total' not in r and 'unit_price' not in r['items'][0]
        assert c.get('/api/seller/orders',headers={'X-Merchant-Key':'test-key'}).json()==[]
