"""Design routes: HTTP adapters for a single application concern."""
import json
import math
import os
from decimal import Decimal
from typing import Annotated, Literal
from .room_categories import RoomCategory
from uuid import uuid4
from fastapi import File, Form, HTTPException, UploadFile
from fastapi import Request
from sqlalchemy import select
from .models import Asset, Seller, Design
from .rendering import decode_image, render, MAX_BYTES
from .quotes import quote
from .generation import models, generate, GenerationError
from .planning import validate_plan, km
from .workspace import current_customer, project_access
from .workspace_models import ProjectDesign
from .workspace_models import ProductPhoto
from fastapi import APIRouter
from .dependencies import DB
from .storage import MEDIA

router = APIRouter()

@router.post('/api/designs',status_code=201)
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
