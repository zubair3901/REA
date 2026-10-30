import json,struct
from fastapi.testclient import TestClient
from app.main import app
from app.seed import seed
from app.database import Session
from app.models import Seller
from test_marketplace import photo

def glb(document=None):
    document=document or {'asset':{'version':'2.0'},'buffers':[{'byteLength':36}],'bufferViews':[{'buffer':0,'byteLength':36}],'accessors':[{'bufferView':0,'componentType':5126,'count':3,'type':'VEC3','min':[0,0,0],'max':[1,1,0]}],'meshes':[{'primitives':[{'attributes':{'POSITION':0}}]}],'nodes':[{'mesh':0}],'scenes':[{'nodes':[0]}],'scene':0}
    raw=json.dumps(document).encode();raw+=b' '*((-len(raw))%4);binary=struct.pack('<9f',0,0,0,1,0,0,0,1,0)
    return struct.pack('<4sII',b'glTF',2,28+len(raw)+len(binary))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(binary),0x004e4942)+binary

def test_model_save_attachment_visibility_and_staging(monkeypatch):
    seed();monkeypatch.setenv('MERCHANT_KEYS_JSON','{"demo":"test-key","other":"other-key"}')
    with Session() as db:db.add(Seller(id='other',name='Other seller',active=True));db.commit()
    with TestClient(app) as c:
        headers={'X-Merchant-Key':'test-key'}
        thumbnail=c.post('/api/uploads',headers=headers,files={'file':('snapshot.png',photo(True),'image/png')}).json()['image_url']
        metadata={'name':'Three dimensional sofa','asset_id':'sofa','thumbnail_url':thumbnail,'accuracy_confirmed':True,'specifications':{'kind':'sofa','width_cm':210,'height_cm':80,'depth_cm':90,'color':'#aabbcc','finish':'fabric'}}
        def save(body=metadata,data=None,h=headers):return c.post('/api/seller/models',headers=h,data={'metadata':json.dumps(body)},files={'model':('product.glb',data or glb(),'model/gltf-binary')})
        assert save(h={}).status_code==401
        assert save(h={'X-Merchant-Key':'other-key'}).status_code==422
        assert save(data=b'not glb').status_code==422
        assert save(body={**metadata,'specifications':{**metadata['specifications'],'width_cm':220}}).status_code==422
        response=save();assert response.status_code==201,response.text
        model=response.json()
        assert c.get('/api/assets/sofa/model').json()['id']==model['id']
        assert c.get(model['model_url']).status_code==200
        assert not next(a for a in c.get('/api/assets').json() if a['id']=='sofa')['has_3d_model']
        replacement=save();assert replacement.status_code==201
        assert replacement.json()['id']==model['id']
        result=c.post('/api/designs',data={'style':'modern','asset_ids':'["sofa"]','room_area':20,'room_category':'living'},files={'room':('room.png',photo(),'image/png')})
        assert result.status_code==201,result.text
        assert result.json()['placements'][0]['reference_source']=='product_photo'
        unattached=save(body={**metadata,'asset_id':None}).json()
        assert c.get(unattached['model_url']).status_code==401
        assert c.get(unattached['model_url'],headers=headers).status_code==200
        assert c.post('/api/seller/models/'+unattached['id']+'/attach',headers={'X-Merchant-Key':'other-key'},json={'asset_id':'sofa'}).status_code==404

def test_glb_rejects_external_resources_and_unbounded_geometry():
    from app.product_models import validate_glb
    import pytest
    for document in [
        {'asset':{'version':'2.0'},'buffers':[{'byteLength':36,'uri':'https://evil.example/x'}]},
        {'asset':{'version':'2.0'},'buffers':[{'byteLength':36}],'images':[{'uri':'file:///etc/passwd'}]},
        {'asset':{'version':'2.0'},'buffers':[{'byteLength':36}],'accessors':[{'count':9999999}]},
    ]:
        with pytest.raises(ValueError):validate_glb(glb(document))

def test_commission_is_uncollected_and_void_on_cancel(monkeypatch):
    from test_workspace import register,project,real_inventory,auth_reset
    from app.workspace_models import OrderCommission
    auth_reset();real_inventory();monkeypatch.setenv('MARKETPLACE_COMMISSION_PERCENT','10')
    with TestClient(app) as c:
        register(c);p=project(c)
        response=c.post('/api/workspace/orders',json={'project_id':p['id'],'items':[{'asset_id':'actual-chair','quantity':1}],'address':'12 Clifton Road, Karachi','phone':'+923001234567','consent':True})
        assert response.status_code==201,response.text
        order=response.json()['orders'][0]
        with Session() as db:
            commission=db.get(OrderCommission,order['id']);assert float(commission.amount)==32 and commission.status=='uncollected'
        assert c.post('/api/workspace/orders/'+order['id']+'/cancel').status_code==200
        with Session() as db:assert db.get(OrderCommission,order['id']).status=='void'
