import base64,json
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import httpx,pytest
from PIL import Image,ImageChops,ImageDraw
from fastapi.testclient import TestClient
from app.main import app
from app.database import Session
from app.models import Asset
from app.workspace_models import AIUsage,DesignScene
from app.seed import seed
from app.protected_placement import PlacementSpec,prepare_products,stage_products,generate_protected,GenerationError,homography,project,STAGES
from test_photography import prepared,approve
from test_workspace import register,project as saved_project
from test_marketplace import photo

def spec(ident='sofa',**patch):
    return PlacementSpec.model_validate({'floor_quad':[{'x':.15,'y':.4},{'x':.85,'y':.4},{'x':.95,'y':.95},{'x':.05,'y':.95}],'floor_width_cm':600,'floor_depth_cm':600,'measurement_confirmed':True,'placements':[{'asset_id':ident,'u':.5,'v':.8,'view':'front'}],**patch})
def encoded(image):
    data=BytesIO();image.save(data,'PNG');return base64.b64encode(data.getvalue()).decode()
def enable(monkeypatch):
    monkeypatch.setenv('ENABLE_PROTECTED_PLACEMENT','true');monkeypatch.setenv('ROOM_PERCEPTION_URL','https://perception.example/segment');monkeypatch.setenv('ROOM_GEMINI_API_KEY','not-real');monkeypatch.setenv('ROOM_AI_DAILY_LIMIT','20')

def test_geometry_requires_real_measurements_and_convex_floor():
    for patch in ({'measurement_confirmed':False},{'floor_width_cm':float('nan')},{'floor_quad':[{'x':.1,'y':.1}]*4}):
        with pytest.raises(ValueError):spec(**patch)
    h=homography([(0,0),(1,0),(1,1),(0,1)],[(10,20),(90,20),(100,90),(0,90)])
    assert project(h,0,0)==pytest.approx((10,20));assert project(h,1,1)==pytest.approx((100,90))

def test_harmonization_cannot_redraw_product_or_unmasked_room(monkeypatch,tmp_path):
    enable(monkeypatch);room=Image.new('RGB',(800,600),'beige');product=Image.new('RGBA',(100,100));ImageDraw.Draw(product).rectangle((10,10,90,90),fill=(10,80,170,255));product.save(tmp_path/'sku.png')
    asset=SimpleNamespace(id='sku',name='Actual chair',category='chair',width_cm=100,depth_cm=60)
    refs={'sku':[{'path':'/media/sku.png','angle':'front','photo_id':'photo-1'}]};settings=spec('sku')
    cleanup=Image.new('L',room.size);ImageDraw.Draw(cleanup).rectangle((10,10,45,45),fill=255)
    async def perception(image):return cleanup,{'detected_objects':1}
    monkeypatch.setattr('app.protected_placement.perceive',perception)
    calls=[]
    async def edit(model,refs,prompt,mask):
        calls.append(prompt);return Image.new('RGBA',room.size,'red')
    monkeypatch.setattr('app.protected_placement.image_edit',edit)
    reserved=[];output=tmp_path/'test-protected.png'
    placements,hotspots,report,cache=__import__('asyncio').run(generate_protected('gemini',room,[asset],tmp_path,output,settings,refs,lambda ops:reserved.extend(ops)))
    empty=room.copy();empty.paste('red',(10,10,46,46))
    layers=prepare_products(room,[asset],tmp_path,refs,settings);stage,lock,ring,_=stage_products(empty,layers,settings)
    result=Image.open(output).convert('RGB')
    difference=ImageChops.multiply(ImageChops.difference(result,stage),Image.merge('RGB',(lock,lock,lock)))
    assert difference.getbbox() is None
    assert result.getpixel((0,0))==room.getpixel((0,0))
    assert result.getpixel((20,20))==(255,0,0)
    assert report['product_pixels_preserved'] and not report['fit_guaranteed']
    assert len(calls)==2 and len(reserved)==3 and placements[0]['reference_photo_ids']==['photo-1']
    assert hotspots[0]['source']=='measured_photo_overlay'

# Avoid requiring pytest-asyncio as a new production/test dependency.
def test_protected_api_quota_reuse_privacy_and_replacement(monkeypatch):
    enable(monkeypatch);seed();real=httpx.AsyncClient;perception_calls=[]
    def transport(request):
        if request.url.host=='perception.example':
            body=json.loads(request.content);image=Image.open(BytesIO(base64.b64decode(body['image_base64'])));perception_calls.append(body)
            mask=Image.new('L',image.size)
            return httpx.Response(200,json={'mask_base64':encoded(mask),'detections':[]})
        assert request.url.host=='generativelanguage.googleapis.com'
        body=json.loads(request.content);image=Image.open(BytesIO(base64.b64decode(body['contents'][0]['parts'][1]['inlineData']['data'])))
        changed=Image.new('RGB',image.size,'red')
        return httpx.Response(200,json={'candidates':[{'content':{'parts':[{'inlineData':{'data':encoded(changed)}}]}}]})
    monkeypatch.setattr('httpx.AsyncClient',lambda **kw:real(transport=httpx.MockTransport(transport),**kw))
    with TestClient(app) as client:
        for ident in ('sofa','chair'):
            item=prepared(client);approve(client,item)
            with Session() as db:
                from app.workspace_models import ProductPhoto
                db.get(ProductPhoto,item['id']).asset_id=ident;db.commit()
        register(client);project=saved_project(client,budget=5000)
        body={'project_id':project['id'],'style':'modern','asset_ids':'["sofa"]','room_category':'living','room_area':24,'model':'gemini','ai_consent':'true','pipeline':'protected','placement_spec':spec().model_dump_json(),'budget_confirmed':'true','budget_ceiling':'5000','budget_currency':'USD'}
        monkeypatch.setenv('ROOM_AI_DAILY_LIMIT','2')
        limited=client.post('/api/designs',data=body,files={'room':('room.png',photo(),'image/png')});assert limited.status_code==429,limited.text;assert not perception_calls
        monkeypatch.setenv('ROOM_AI_DAILY_LIMIT','20')
        created=client.post('/api/designs',data=body,files={'room':('room.png',photo(),'image/png')});assert created.status_code==201,created.text
        design=created.json();assert design['render_mode']=='protected_placement';assert design['image_url'].endswith('.png');assert len(perception_calls)==1
        with TestClient(app) as stranger:
            assert stranger.get(design['image_url']).status_code==401
            assert stranger.post('/api/designs/'+design['id']+'/protected-replace',json={'old_asset_id':'sofa','new_asset_id':'chair','view':'front','ai_consent':True}).status_code==401
        changed=client.post('/api/designs/'+design['id']+'/protected-replace',json={'old_asset_id':'sofa','new_asset_id':'chair','view':'front','ai_consent':True})
        assert changed.status_code==201,changed.text;assert len(perception_calls)==1
        assert changed.json()['quote']['protected_report']['reserved_attempt_slots']==1
        assert changed.json()['parent_id']==design['id']
        assert client.get(design['image_url']).status_code==200
        # A cache is tied to its project and cannot be borrowed through a different project.
        other=saved_project(client,name='Other room')
        borrowed={**body,'project_id':other['id'],'placement_spec':spec(reuse_design_id=design['id']).model_dump_json()}
        assert client.post('/api/designs',data=borrowed,files={'room':('room.png',photo(),'image/png')}).status_code==404

def test_rug_projection_missing_angles_clipping_and_occlusion(tmp_path):
    product=Image.new('RGBA',(120,120));ImageDraw.Draw(product).rectangle((10,10,110,110),fill='blue');product.save(tmp_path/'rug.png')
    room=Image.new('RGB',(800,600),'beige');asset=SimpleNamespace(id='rug',name='Real rug',category='rug',width_cm=150,depth_cm=150)
    refs={'rug':[{'path':'/media/rug.png','angle':'top','photo_id':'top-photo'}]}
    with pytest.raises(GenerationError):prepare_products(room,[asset],tmp_path,refs,spec('rug'))
    settings=spec('rug',placements=[{'asset_id':'rug','u':.5,'v':.8,'view':'top'}]);layers=prepare_products(room,[asset],tmp_path,refs,settings)
    assert layers[0]['geometry_method']=='measured_floor_homography'
    with pytest.raises(GenerationError):stage_products(room,layers,settings,Image.new('L',room.size,255))
    with pytest.raises(GenerationError):prepare_products(room,[asset],tmp_path,refs,spec('rug',floor_width_cm=50,placements=[{'asset_id':'rug','u':.5,'v':.8,'view':'top'}]))

@pytest.mark.parametrize('fault',['uncertain','outside_box','too_large'])
def test_perception_rejects_unsafe_cleanup_masks(monkeypatch,fault):
    enable(monkeypatch);real=httpx.AsyncClient;room=Image.new('RGB',(800,600),'beige')
    def transport(request):
        mask=Image.new('L',room.size)
        ImageDraw.Draw(mask).rectangle((0,0,799,599) if fault=='too_large' else (20,20,50,50),fill=255)
        return httpx.Response(200,json={'mask_base64':encoded(mask),'detections':[{'label':'sofa','confidence':.4 if fault=='uncertain' else .95,'box':[.5,.5,.2,.2] if fault=='outside_box' else [0,0,1,1]}]})
    monkeypatch.setattr('httpx.AsyncClient',lambda **kw:real(transport=httpx.MockTransport(transport),**kw))
    with pytest.raises(GenerationError) as error:__import__('asyncio').run(__import__('app.protected_placement',fromlist=['perceive']).perceive(room))
    assert error.value.status==422
