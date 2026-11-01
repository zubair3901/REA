import hmac
import json
import math
import os
import re
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Annotated, Literal
from .room_categories import RoomCategory
from uuid import uuid4
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi import Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession
from .database import DATA, Base, engine, get_db
from .models import Asset, Seller, Design, Lead, Outbox
from .rendering import decode_image, render, MAX_BYTES
from .quotes import quote
from .generation import models, generate, GenerationError
from .accounts import router as account_router, session_seller
from .planning import router as planning_router, validate_plan, km
from .operations import router as operations_router
from .workspace import router as workspace_router, current_customer, project_access
from .commerce import router as commerce_router, seller_order_update
from .workspace_operations import router as platform_operator_router
from .workspace_models import ProjectDesign, Order
from .security import SecurityMiddleware
from .recovery import router as recovery_router
from .admin_auth import router as admin_auth_router
from .verification import router as verification_router
from .payments import router as payments_router
from .seller_verification import router as seller_verification_router
from .scene_routes import router as scene_router

MEDIA = DATA / 'media'; MEDIA.mkdir(exist_ok=True)
@asynccontextmanager
async def lifespan(app):
    if os.getenv('AUTO_CREATE_SCHEMA', 'true') == 'true': Base.metadata.create_all(engine)
    yield
app = FastAPI(title='Roomform Marketplace', version='1.0.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv('CORS_ORIGINS','http://localhost:5173').split(','), allow_credentials=True, allow_methods=['GET','POST','PATCH','DELETE'], allow_headers=['Content-Type','X-Merchant-Key','X-Operator-Key'])
app.add_middleware(SecurityMiddleware)
app.include_router(account_router)
app.include_router(planning_router)
app.include_router(operations_router)
app.include_router(workspace_router)
app.include_router(recovery_router)
app.include_router(admin_auth_router)
app.include_router(verification_router)
app.include_router(payments_router)
app.include_router(seller_verification_router)
app.include_router(commerce_router)
app.include_router(scene_router)
app.include_router(platform_operator_router)
DB = Annotated[DBSession, Depends(get_db)]

def merchant(db: Annotated[DBSession, Depends(get_db)], key: Annotated[str | None, Header(alias='X-Merchant-Key')] = None):
    bindings = json.loads(os.getenv('MERCHANT_KEYS_JSON','{}'))
    for seller_id, expected in bindings.items():
        if os.getenv('ALLOW_LEGACY_OPERATOR_KEY','false')=='true' and key and hmac.compare_digest(key, expected): return seller_id
    seller_id=session_seller(db,key)
    if seller_id:
        if os.getenv('REQUIRE_VERIFIED_EMAIL','false')=='true':
            from .workspace_models import SellerEmailVerification
            verification=db.get(SellerEmailVerification,seller_id)
            if not verification or not verification.verified_at:raise HTTPException(403,'Verify your seller email before managing inventory or orders')
        return seller_id
    raise HTTPException(401, 'A valid merchant key or seller login is required')

class AssetIn(BaseModel):
    seller_id: str = Field(min_length=1,max_length=36)
    name: str = Field(min_length=2,max_length=160)
    category: str = Field(min_length=2,max_length=80)
    style: str = Field(min_length=2,max_length=80)
    price: Decimal = Field(gt=0,le=10000000,max_digits=12,decimal_places=2)
    currency: str = Field(pattern=r'^[A-Z]{3}$')
    width_cm: float = Field(gt=0,le=2000,allow_inf_nan=False)
    height_cm: float = Field(gt=0,le=2000,allow_inf_nan=False)
    depth_cm: float = Field(gt=0,le=2000,allow_inf_nan=False)
    condition: Literal['new','like_new','good','fair']='new'
    delivery_location: str=Field(default='',max_length=200)
    delivery_radius_km: float=Field(default=50,ge=0,le=500,allow_inf_nan=False)
    photo_ids: list[str]=Field(default_factory=list,max_length=6)
    image_url: str
    latitude: float = Field(ge=-90,le=90,allow_inf_nan=False)
    longitude: float = Field(ge=-180,le=180,allow_inf_nan=False)
    stock: int = Field(ge=0,le=1000000)
    delivery_days: int = Field(ge=0,le=365)
    @field_validator('image_url')
    @classmethod
    def local_image(cls,v):
        if not re.fullmatch(r'/media/[a-zA-Z0-9_-]+\.png',v): raise ValueError('Upload a transparent PNG first')
        return v

class LeadIn(BaseModel):
    design_id: str = Field(min_length=36,max_length=36)
    name: str = Field(min_length=2,max_length=160)
    email: str = Field(max_length=254,pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    phone: str = Field(default='',max_length=40)
    consent: Literal[True]

@app.get('/health')
def health(): return {'status':'ok','ai_generation_enabled':os.getenv('ENABLE_AI_GENERATION','false')=='true' and any(m['available'] for m in models() if m['id']!='composite')}

@app.get('/api/models')
def available_models():
    return [{**m, **({'available':False,'reason':'AI placement is disabled by the operator'} if m['id']!='composite' and os.getenv('ENABLE_AI_GENERATION','false')!='true' else {})} for m in models()]

@app.get('/api/assets')
def assets(db: DB, latitude: float | None=None, longitude: float | None=None, radius_km: float=50):
    if (latitude is None) != (longitude is None): raise HTTPException(422,'Supply both coordinates')
    if not math.isfinite(radius_km) or not 0 < radius_km <= 500: raise HTTPException(422,'Radius must be 0–500 km')
    if latitude is not None and (not math.isfinite(latitude) or not math.isfinite(longitude) or abs(latitude)>90 or abs(longitude)>180): raise HTTPException(422,'Invalid coordinates')
    query=select(Asset).join(Seller).where(Asset.active==True,Asset.stock>0,Seller.active==True)
    if os.getenv('ALLOW_LEGACY_PHOTOS','false')!='true':query=query.where(Asset.id.in_(select(ProductPhoto.asset_id).where(ProductPhoto.approved==1)))
    rows=db.scalars(query.limit(500)).all()
    if os.getenv('ALLOW_DEMO_CATALOG','false')!='true':rows=[a for a in rows if a.seller_id!='demo']
    if latitude is not None:
        def distance(a):
            p,q=math.radians(latitude),math.radians(a.latitude)
            h=math.sin((q-p)/2)**2+math.cos(p)*math.cos(q)*math.sin(math.radians(a.longitude-longitude)/2)**2
            return 6371*2*math.asin(min(1,math.sqrt(h)))
        rows=[a for a in rows if distance(a)<=radius_km]
    photos=db.scalars(select(ProductPhoto).where(ProductPhoto.asset_id.in_([a.id for a in rows]),ProductPhoto.approved==1)).all()
    return [{**{c.name:getattr(a,c.name) for c in Asset.__table__.columns},'photo_count':sum(p.asset_id==a.id for p in photos),'has_3d_model':False} for a in rows]

@app.post('/api/uploads',status_code=201)
async def upload(file: Annotated[UploadFile,File()], seller: Annotated[str,Depends(merchant)]):
    raw=await file.read(MAX_BYTES+1)
    try: image=decode_image(raw)
    except ValueError as e: raise HTTPException(422,str(e))
    if image.getchannel('A').getextrema()[0] == 255: raise HTTPException(422,'Product image needs a transparent background')
    filename=f'{seller}_{uuid4().hex}.png'
    # Seller IDs come from operator configuration; disallow path characters.
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',seller): raise HTTPException(500,'Invalid configured seller ID')
    image.thumbnail((2000,2000)); image.save(MEDIA/filename)
    return {'image_url':f'/media/{filename}'}

@app.post('/api/assets',status_code=201)
def create_asset(body: AssetIn, db: DB, seller: Annotated[str,Depends(merchant)]):
    if body.seller_id!=seller: raise HTTPException(403,'Merchant may only publish their own listings')
    owner=db.get(Seller,seller)
    if not owner or not owner.active: raise HTTPException(403,'Merchant is not approved')
    if not body.image_url.startswith(f'/media/{seller}_') or not (MEDIA/body.image_url.rsplit('/',1)[-1]).is_file(): raise HTTPException(422,'Upload your own product image')
    from .photography import attach_photos
    if not body.photo_ids and os.getenv('ALLOW_LEGACY_PHOTOS','false')!='true':raise HTTPException(422,'Prepare and approve real product photos before publishing')
    a=Asset(id=str(uuid4()),**body.model_dump(exclude={'photo_ids'}));db.add(a);db.flush()
    attach_photos(db,seller,a.id,body.photo_ids,body.image_url);db.commit()
    return {'id':a.id,**body.model_dump()}

@app.post('/api/designs',status_code=201)
async def create_design(request: Request, db: DB, room: Annotated[UploadFile,File()], style: Annotated[str,Form()], asset_ids: Annotated[str,Form()], room_area: Annotated[float,Form(gt=0,le=1000)], room_category: Annotated[RoomCategory,Form()], model: Annotated[Literal['composite','openai','gemini'],Form()]='composite', ai_consent: Annotated[bool,Form()]=False, design_brief: Annotated[str,Form(max_length=1200)]='', plan_id: Annotated[str,Form()]='', budget_ceiling: Annotated[Decimal | None,Form(gt=0,le=10000000)]=None, budget_confirmed: Annotated[bool,Form()]=False, condition_preference: Annotated[Literal['new','used','either'],Form()]='either', budget_currency: Annotated[str,Form()]='', project_id: Annotated[str,Form()]='', pipeline: Annotated[Literal['reference','protected'],Form()]='reference', placement_spec: Annotated[str,Form(max_length=3100000)]=''):
    measured=None;protected_report=None;protected_cache=None;protected_hotspots=[];reuse=None
    if pipeline=='protected':
        if model=='composite' or not project_id:raise HTTPException(422,'Measured AI placement requires a saved project and an AI provider')
        from .protected_placement import PlacementSpec,configured_endpoint
        from pydantic import ValidationError
        try:measured=PlacementSpec.model_validate_json(placement_spec)
        except ValidationError:raise HTTPException(422,'Supply a measured convex floor rectangle, dimensions, confirmation and one placement per selected product')
        try:configured_endpoint()
        except GenerationError as exc:raise HTTPException(exc.status,str(exc))
    if project_id:
        user=current_customer(request,db)
        project_access(db,project_id,user)
    elif os.getenv('ALLOW_GUEST_PREVIEWS','false')!='true':
        raise HTTPException(422,'Select a saved project before creating a preview')
    if model!='composite' and os.getenv('ENABLE_AI_GENERATION','false')!='true':
        raise HTTPException(503,'AI integration is deferred. Use the local product preview.')
    if model!='composite' and not ai_consent: raise HTTPException(422,'Consent is required before sending room and product images to an AI provider')
    if model!='composite' and not next(m for m in models() if m['id']==model)['available']: raise HTTPException(503,'Selected AI provider is not configured')
    if not math.isfinite(room_area) or len(style)>80: raise HTTPException(422,'Invalid room settings')
    if budget_ceiling is not None and not budget_confirmed: raise HTTPException(422,'Confirm your investment ceiling first')
    plan=validate_plan(db,plan_id,style,room_area,room_category) if plan_id else None
    try:
        ids=plan.asset_ids if plan else json.loads(asset_ids)
        if not isinstance(ids,list) or not 1<=len(ids)<=8 or any(not isinstance(i,str) for i in ids) or len(set(ids))!=len(ids): raise ValueError('Select 1–8 distinct products')
        image=decode_image(await room.read(MAX_BYTES+1))
    except (ValueError,TypeError) as e: raise HTTPException(422,str(e))
    rows=db.scalars(select(Asset).join(Seller).where(Asset.id.in_(ids),Asset.active==True,Asset.stock>0,Seller.active==True)).all()
    if os.getenv('ALLOW_DEMO_CATALOG','false')!='true' and any(a.seller_id=='demo' for a in rows):raise HTTPException(409,'Illustrative inventory is not available for room designs')
    if len(rows)!=len(ids): raise HTTPException(409,'One or more listings are no longer available')
    if os.getenv('ALLOW_LEGACY_PHOTOS','false')!='true':
        approved_ids=set(db.scalars(select(ProductPhoto.asset_id).where(ProductPhoto.asset_id.in_(ids),ProductPhoto.approved==1)))
        if any(a.id not in approved_ids for a in rows):raise HTTPException(409,'Choose listings with approved real seller photographs')
    rows=sorted(rows,key=lambda a:ids.index(a.id))
    try: budget=quote(rows,room_area,room_category)
    except ValueError as e: raise HTTPException(422,str(e))
    if budget_ceiling is not None:
        if budget_currency and any(a.currency!=budget_currency for a in rows): raise HTTPException(422,'Selected products use a different currency')
        if Decimal(str(budget['total']))>budget_ceiling: raise HTTPException(409,'Selected products plus labor exceed your confirmed budget')
        if any((condition_preference=='new' and a.condition!='new') or (condition_preference=='used' and a.condition=='new') for a in rows): raise HTTPException(409,'A selected product does not match the confirmed condition preference')
        budget={**budget,'confirmed_budget':str(budget_ceiling),'preference':condition_preference}
    if plan:
        params=plan.parameters
        if params.get('latitude') is not None and any(km(a,params['latitude'],params['longitude'])>a.delivery_radius_km for a in rows):
            raise HTTPException(409,'Delivery coverage changed; confirm a fresh proposal')
        if any(a.currency!=params['currency'] or (params['preference']=='new' and a.condition!='new') or (params['preference']=='used' and a.condition=='new') for a in rows):
            raise HTTPException(409,'Listings changed; confirm a fresh budget plan')
        if Decimal(str(budget['total']))>Decimal(str(params['budget'])):
            raise HTTPException(409,'Current prices exceed your budget; confirm a fresh plan')
        budget={**budget,'confirmed_budget':params['budget'],'preference':params['preference'],'plan_id':plan.id}
    if measured and measured.reuse_design_id:
        from .workspace_models import DesignScene
        from .protected_placement import STAGES
        previous=db.get(ProjectDesign,measured.reuse_design_id);previous_scene=db.get(DesignScene,measured.reuse_design_id)
        if not previous or previous.project_id!=project_id or not previous_scene:raise HTTPException(404,'Cached cleanup is not part of this project')
        cache=previous_scene.parameters.get('protected_cache')
        empty=STAGES/measured.reuse_design_id/'empty.png'
        if not cache or not empty.is_file():raise HTTPException(409,'Cached cleanup is unavailable. Start with a fresh cleanup.')
        reuse={**cache,'empty_path':empty}
    if model!='composite' and project_id and pipeline!='protected':
        from .ai_limits import reserve_attempt
        reserve_attempt(db,user.id,project_id,'room_placement')
    design_id=str(uuid4()); path=MEDIA/(design_id+('.png' if measured else '.jpg'))
    try:
        # Run CPU/image work outside the event loop.
        from starlette.concurrency import run_in_threadpool
        from .photography import reference_sets
        photo_sets=reference_sets(db,rows)
        model_refs={ident:refs[0]['path'] for ident,refs in photo_sets.items()}
        if model=='composite':
            placements=await run_in_threadpool(render,image,rows,MEDIA,path,model_refs)
        elif measured:
            from .protected_placement import generate_protected
            from .ai_limits import reserve_attempts
            placements,protected_hotspots,protected_report,protected_cache=await generate_protected(model,image,rows,MEDIA,path,measured,photo_sets,lambda operations:reserve_attempts(db,user.id,project_id,operations),reuse)
        else:
            placements=await generate(model,image,rows,MEDIA,path,style,room_category,room_area,design_brief,model_refs,photo_sets=photo_sets)
    except GenerationError as e: raise HTTPException(e.status,str(e))
    except (ValueError,OSError): raise HTTPException(422,'Could not render one of the product images')
    d=Design(id=design_id,style=style,image_url=f'/media/{path.name}',render_mode='protected_placement' if measured else ('asset_composite' if model=='composite' else 'ai_reference'),quote=budget,placements=placements)
    if model!='composite':
        d.quote={**budget,'product_fidelity':'unverified','items_basis':'selected reference inventory, not detected image contents','model_provider':model}
    if measured:d.quote={**budget,'product_fidelity':'photographed_pixels_protected','items_basis':'locally composited seller cutouts','model_provider':model,'protected_report':protected_report}
    db.add(d);db.flush()
    from .photography import ROOMS
    from .workspace_models import DesignScene
    original_file=d.id+'.png';image.save(ROOMS/original_file)
    output_image=decode_image(path.read_bytes())
    if measured:hotspots=protected_hotspots
    elif model=='composite':
        hotspots=[{'asset_id':p['asset_id'],'x':p['x']/output_image.width,'y':p['y']/output_image.height,'width':p['width']/output_image.width,'height':p['height']/output_image.height,'source':'exact_overlay','confidence':1.0} for p in d.placements]
    else:
        from .localization import locate_products
        hotspots=await locate_products(model,output_image,rows,MEDIA,photo_sets)
    db.add(DesignScene(design_id=d.id,original_file=original_file,parameters={'pipeline':pipeline,'protected_cache':protected_cache,'style':style,'room_area':room_area,'room_category':room_category,'brief':design_brief,'model':model,'budget_ceiling':str(budget_ceiling) if budget_ceiling is not None else budget.get('confirmed_budget'),'preference':plan.parameters['preference'] if plan else condition_preference,'currency':budget_currency or budget['currency'],'latitude':plan.parameters.get('latitude') if plan else None,'longitude':plan.parameters.get('longitude') if plan else None},hotspots=hotspots))
    if project_id: db.add(ProjectDesign(design_id=d.id,project_id=project_id))
    db.commit()
    return {'id':d.id,'image_url':d.image_url,'render_mode':d.render_mode,'quote':d.quote,'placements':d.placements,'hotspots':hotspots,'hotspot_status':'measured_photo_overlay' if measured else ('exact_overlay' if model=='composite' else ('ai_suggested' if hotspots else 'mark_products_to_locate')),'limitations':(['Product pixels are preserved from the transformed cutout, not a guarantee of physical fit or photorealism','Scale depends on your measured floor rectangle; unseen sides are never generated','Only cleanup holes and immediate contact/shadow regions are edited by AI'] if measured else ['AI product identity and placement are not guaranteed; confirm every SKU with the seller','Budget lists selected references, not verified image contents','Room dimensions and buildability require on-site review'] if model!='composite' else ['Concept staging, not a photorealistic AI render','Perspective and room geometry are not inferred','Product scale is approximate; verify dimensions on site','Style is a selection label; wall color is unchanged'])}

@app.post('/api/leads',status_code=201)
def create_lead(body: LeadIn,request:Request,db: DB):
    link=db.get(ProjectDesign,body.design_id)
    if link:project_access(db,link.project_id,current_customer(request,db))
    if not db.get(Design,body.design_id): raise HTTPException(404,'Design not found')
    lead=Lead(id=str(uuid4()),**body.model_dump());db.add(lead);db.flush()
    db.add(Outbox(id=str(uuid4()),lead_id=lead.id,payload={'event':'consultation.requested','lead_id':lead.id,**body.model_dump()}));db.commit()
    return {'id':lead.id,'status':lead.status,'consultation_url':os.getenv('CONSULTATION_URL') or None,'payment_collected':False}


class AssetUpdate(BaseModel):
    stock: int | None=Field(default=None,ge=0,le=1000000)
    active: bool | None=None
    price: Decimal | None=Field(default=None,gt=0,le=10000000,max_digits=12,decimal_places=2)
    delivery_days: int | None=Field(default=None,ge=0,le=365)

@app.get('/api/seller/listings')
def own_listings(db: DB, seller: Annotated[str,Depends(merchant)]):
    rows=db.scalars(select(Asset).where(Asset.seller_id==seller)).all()
    return [{c.name:getattr(a,c.name) for c in Asset.__table__.columns} for a in rows]

@app.patch('/api/assets/{asset_id}')
def update_listing(asset_id:str, body:AssetUpdate, db:DB, seller:Annotated[str,Depends(merchant)]):
    asset=db.get(Asset,asset_id)
    if not asset or asset.seller_id!=seller: raise HTTPException(404,'Listing not found')
    owner=db.get(Seller,seller)
    if not owner or not owner.active: raise HTTPException(403,'Seller approval is pending')
    for key,value in body.model_dump(exclude_unset=True).items():
        if value is None: raise HTTPException(422,'Listing fields cannot be null')
        setattr(asset,key,value)
    db.commit()
    return {c.name:getattr(asset,c.name) for c in Asset.__table__.columns}


class BulkAssets(BaseModel):
    assets: list[AssetIn] = Field(min_length=1,max_length=100)

@app.post('/api/seller/listings/bulk',status_code=201)
def bulk_listings(body: BulkAssets, db: DB, seller: Annotated[str,Depends(merchant)]):
    owner=db.get(Seller,seller)
    if not owner or not owner.active: raise HTTPException(403,'Seller approval is pending')
    rows=[]
    for index,asset in enumerate(body.assets):
        if asset.seller_id!=seller: raise HTTPException(403,f'Row {index+1}: seller mismatch')
        if not asset.image_url.startswith(f'/media/{seller}_') or not (MEDIA/asset.image_url.rsplit('/',1)[-1]).is_file():
            raise HTTPException(422,f'Row {index+1}: upload a product photo owned by this seller first')
        if not asset.photo_ids and os.getenv('ALLOW_LEGACY_PHOTOS','false')!='true':raise HTTPException(422,'Bulk listings require prepared real photo IDs')
        row=Asset(id=str(uuid4()),**asset.model_dump(exclude={'photo_ids'}));db.add(row);db.flush()
        from .photography import attach_photos
        attach_photos(db,seller,row.id,asset.photo_ids,asset.image_url)
        rows.append(row)
    db.add_all(rows);db.commit()
    return {'created':len(rows),'asset_ids':[a.id for a in rows]}


@app.get('/media/{filename}')
def media_file(filename:str,request:Request,db:DB):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+\.(png|jpg|glb)',filename):raise HTTPException(404,'Image not found')
    if filename.endswith('.glb'):
        row=db.scalar(select(ProductModel).where(ProductModel.model_url=='/media/'+filename))
        if not row:raise HTTPException(404,'Model not found')
        owner=db.get(Seller,row.seller_id);asset=db.get(Asset,row.asset_id) if row.asset_id else None
        if not (owner and owner.active and asset and asset.active and asset.stock>0):
            if merchant(db,request.headers.get('X-Merchant-Key'))!=row.seller_id:raise HTTPException(404,'Model not found')
    if filename.endswith(('.jpg','.png')):
        link=db.get(ProjectDesign,filename[:-4])
        if link:
            from .operations import operator
            if request.headers.get('X-Operator-Key') or request.cookies.get('roomform_admin'):operator(request,request.headers.get('X-Operator-Key'),db)
            else:project_access(db,link.project_id,current_customer(request,db))
        elif (filename.endswith('.jpg') or re.fullmatch(r'[a-f0-9-]{36}\.png',filename)) and os.getenv('ALLOW_GUEST_PREVIEWS','false')!='true':raise HTTPException(404,'Image not found')
    path=MEDIA/filename
    if not path.is_file():raise HTTPException(404,'Image not found')
    return FileResponse(path,headers={'Cache-Control':'private, no-store' if filename.endswith(('.jpg','.png')) else 'public, max-age=3600','X-Content-Type-Options':'nosniff'})

@app.get('/api/seller/orders')
def seller_orders(db:DB,seller:Annotated[str,Depends(merchant)]):
    from .workspace_models import OrderCommission
    result=[]
    for o in db.scalars(select(Order).where(Order.seller_id==seller).order_by(Order.created_at.desc())):
        commission=db.get(OrderCommission,o.id)
        result.append({**{c.name:getattr(o,c.name) for c in Order.__table__.columns},'commission':model_record(commission) if commission else None})
    return result

class SellerOrderStatus(BaseModel):
    status:Literal['confirmed','dispatched','delivered','cancelled']
@app.patch('/api/seller/orders/{order_id}')
def seller_order_status(order_id:str,body:SellerOrderStatus,db:DB,seller:Annotated[str,Depends(merchant)]):
    return seller_order_update(db,order_id,seller,body.status)

# Parametric product models are seller-owned until attached to a public listing.
from .workspace_models import ProductModel
from .product_models import ProductModelIn,validate_glb
from .workspace import record as model_record

@app.get('/api/seller/models')
def seller_models(db:DB,seller:Annotated[str,Depends(merchant)]):
    return [model_record(m) for m in db.scalars(select(ProductModel).where(ProductModel.seller_id==seller).order_by(ProductModel.created_at.desc()))]

@app.post('/api/seller/models',status_code=201)
async def save_product_model(db:DB,seller:Annotated[str,Depends(merchant)],metadata:Annotated[str,Form(max_length=10000)],model:Annotated[UploadFile,File()]):
    from pydantic import ValidationError
    try:body=ProductModelIn.model_validate_json(metadata)
    except ValidationError:raise HTTPException(422,'Check the model name, dimensions, material and confirmation')
    owner=db.get(Seller,seller)
    if not owner or not owner.active:raise HTTPException(403,'Seller approval required to save a model')
    if not body.thumbnail_url.startswith(f'/media/{seller}_') or not (MEDIA/body.thumbnail_url.rsplit('/',1)[-1]).is_file():raise HTTPException(422,'Upload your own transparent product snapshot first')
    existing=None
    if body.asset_id:
        asset=db.get(Asset,body.asset_id)
        if not asset or asset.seller_id!=seller:raise HTTPException(404,'Your listing was not found')
        for key in ('width_cm','height_cm','depth_cm'):
            if abs(getattr(asset,key)-getattr(body.specifications,key))>.1:raise HTTPException(422,'Model dimensions must match the selected listing dimensions')
        existing=db.scalar(select(ProductModel).where(ProductModel.asset_id==body.asset_id))
        if existing and existing.seller_id!=seller:raise HTTPException(404,'Your model was not found')
    raw=await model.read(8*1024*1024+1)
    try:validate_glb(raw)
    except (ValueError,TypeError,KeyError,AttributeError,IndexError,RecursionError):raise HTTPException(422,'Use a valid self-contained GLB under 8 MB with no external resources')
    ident=str(uuid4());path=MEDIA/f'{seller}_{ident}.glb';path.write_bytes(raw)
    row=ProductModel(id=ident,seller_id=seller,asset_id=body.asset_id,name=body.name,specifications=body.specifications.model_dump(),thumbnail_url=body.thumbnail_url,model_url=f'/media/{path.name}')
    old_path=None
    if existing:
        old_path=MEDIA/existing.model_url.rsplit('/',1)[-1]
        for key in ('name','specifications','thumbnail_url','model_url'):setattr(existing,key,getattr(row,key))
        row=existing
    else:db.add(row)
    try:db.commit()
    except Exception:
        db.rollback();path.unlink(missing_ok=True);raise
    if old_path:old_path.unlink(missing_ok=True)
    return model_record(row)

@app.get('/api/assets/{asset_id}/model')
def listing_model(asset_id:str,db:DB):
    asset=db.get(Asset,asset_id)
    if not asset or not asset.active or asset.stock<=0 or not db.get(Seller,asset.seller_id).active:raise HTTPException(404,'Listing not available')
    row=db.scalar(select(ProductModel).where(ProductModel.asset_id==asset_id))
    if not row:raise HTTPException(404,'This listing has no 3D model')
    return model_record(row)

class ModelAttachment(BaseModel):
    asset_id:str=Field(min_length=1,max_length=36)
@app.post('/api/seller/models/{model_id}/attach')
def attach_product_model(model_id:str,body:ModelAttachment,db:DB,seller:Annotated[str,Depends(merchant)]):
    row=db.get(ProductModel,model_id);asset=db.get(Asset,body.asset_id)
    if not row or row.seller_id!=seller or not asset or asset.seller_id!=seller:raise HTTPException(404,'Your model or listing was not found')
    owner=db.get(Seller,seller)
    if not owner or not owner.active:raise HTTPException(403,'Seller approval required')
    if row.asset_id:raise HTTPException(409,'This model is already attached to a listing')
    if db.scalar(select(ProductModel).where(ProductModel.asset_id==body.asset_id)):raise HTTPException(409,'This listing already has a model')
    if any(abs(getattr(asset,k)-row.specifications[k])>.1 for k in ('width_cm','height_cm','depth_cm')):raise HTTPException(422,'Listing measurements must match the model. Create a model with the correct dimensions.')
    row.asset_id=asset.id
    from sqlalchemy.exc import IntegrityError
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'This listing already has a model')
    return model_record(row)

from .workspace_models import ProductPhoto
from .photography import prepare_photo,photo_json,ORIGINALS

@app.post('/api/seller/photos',status_code=201)
async def prepare_product_photo(db:DB,seller:Annotated[str,Depends(merchant)],file:Annotated[UploadFile,File()],angle:Annotated[Literal['front','left','right','back','detail','angled','top'],Form()]='front'):
    owner=db.get(Seller,seller)
    if not owner or not owner.active:raise HTTPException(403,'Seller approval is required before preparing photos')
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',seller):raise HTTPException(500,'Invalid seller identity')
    from starlette.concurrency import run_in_threadpool
    try:original,cutout,quality=await run_in_threadpool(prepare_photo,await file.read(MAX_BYTES+1))
    except ValueError as e:raise HTTPException(422,str(e))
    ident=str(uuid4());original_file=ident+'.png';filename=f'{seller}_photo_{ident}.png'
    original.save(ORIGINALS/original_file);cutout.save(MEDIA/filename)
    photo=ProductPhoto(id=ident,seller_id=seller,angle=angle,original_file=original_file,cutout_url='/media/'+filename,quality=quality)
    db.add(photo);db.commit();return photo_json(photo)

class PhotoApproval(BaseModel):
    approved:Literal[True]
    rights_confirmed:Literal[True]
@app.post('/api/seller/photos/{photo_id}/approve')
def approve_product_photo(photo_id:str,body:PhotoApproval,db:DB,seller:Annotated[str,Depends(merchant)]):
    photo=db.get(ProductPhoto,photo_id)
    if not photo or photo.seller_id!=seller:raise HTTPException(404,'Your photo was not found')
    photo.approved=1;db.commit();return photo_json(photo)

@app.get('/api/seller/photos')
def seller_photos(db:DB,seller:Annotated[str,Depends(merchant)]):
    return [photo_json(p) for p in db.scalars(select(ProductPhoto).where(ProductPhoto.seller_id==seller).order_by(ProductPhoto.created_at.desc()).limit(200))]

@app.get('/api/product-photos/{photo_id}/original')
def original_product_photo(photo_id:str,request:Request,db:DB):
    photo=db.get(ProductPhoto,photo_id)
    if not photo:raise HTTPException(404,'Photo not found')
    asset=db.get(Asset,photo.asset_id) if photo.asset_id else None;owner=db.get(Seller,photo.seller_id)
    public=photo.approved and asset and asset.active and asset.stock>0 and owner and owner.active
    if not public and merchant(db,request.headers.get('X-Merchant-Key'))!=photo.seller_id:raise HTTPException(404,'Photo not found')
    path=ORIGINALS/photo.original_file
    if not path.is_file():raise HTTPException(404,'Photo not found')
    return FileResponse(path,headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'})

@app.get('/api/assets/{asset_id}')
def real_product_detail(asset_id:str,db:DB):
    asset=db.get(Asset,asset_id)
    if not asset or not asset.active or asset.stock<=0 or not db.get(Seller,asset.seller_id).active or (asset.seller_id=='demo' and os.getenv('ALLOW_DEMO_CATALOG','false')!='true'):raise HTTPException(404,'Product is currently unavailable')
    photos=db.scalars(select(ProductPhoto).where(ProductPhoto.asset_id==asset.id,ProductPhoto.approved==1)).all()
    if not photos and os.getenv('ALLOW_LEGACY_PHOTOS','false')!='true':raise HTTPException(404,'This listing needs approved real photographs')
    return {**{c.name:getattr(asset,c.name) for c in Asset.__table__.columns},'seller_name':db.get(Seller,asset.seller_id).name,'photos':[photo_json(p) for p in photos]}

@app.delete('/api/seller/photos/{photo_id}')
def delete_unattached_photo(photo_id:str,db:DB,seller:Annotated[str,Depends(merchant)]):
    photo=db.get(ProductPhoto,photo_id)
    if not photo or photo.seller_id!=seller:raise HTTPException(404,'Your photo was not found')
    if photo.asset_id:raise HTTPException(409,'Replace the listing photographs before deleting this image')
    original=ORIGINALS/photo.original_file;cutout=MEDIA/photo.cutout_url.rsplit('/',1)[-1]
    db.delete(photo);db.commit();original.unlink(missing_ok=True);cutout.unlink(missing_ok=True);return {'removed':True}

class ListingPhotos(BaseModel):
    photo_ids:list[str]=Field(min_length=1,max_length=6)
    image_url:str=Field(pattern=r'^/media/[a-zA-Z0-9_-]+\.png$')
@app.post('/api/seller/listings/{asset_id}/photos')
def update_listing_photos(asset_id:str,body:ListingPhotos,db:DB,seller:Annotated[str,Depends(merchant)]):
    asset=db.get(Asset,asset_id)
    if not asset or asset.seller_id!=seller:raise HTTPException(404,'Your listing was not found')
    if not db.get(Seller,seller).active:raise HTTPException(403,'Seller approval required')
    from .photography import attach_photos
    attach_photos(db,seller,asset.id,body.photo_ids,body.image_url)
    for photo in db.scalars(select(ProductPhoto).where(ProductPhoto.asset_id==asset.id,ProductPhoto.id.not_in(body.photo_ids))):photo.asset_id=None
    asset.image_url=body.image_url;db.commit();return {'id':asset.id,'photo_ids':body.photo_ids,'image_url':asset.image_url}

class PhotoAngle(BaseModel):
    angle:Literal['front','left','right','back','detail','angled','top']
@app.patch('/api/seller/photos/{photo_id}')
def label_product_angle(photo_id:str,body:PhotoAngle,db:DB,seller:Annotated[str,Depends(merchant)]):
    photo=db.get(ProductPhoto,photo_id)
    if not photo or photo.seller_id!=seller:raise HTTPException(404,'Your photo was not found')
    photo.angle=body.angle;db.commit();return photo_json(photo)

@app.get('/api/placement/capabilities')
def placement_capabilities():
    from .protected_placement import capabilities
    return capabilities()
