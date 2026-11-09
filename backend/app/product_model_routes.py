"""Product model routes: HTTP adapters for a single application concern."""
from typing import Annotated
from uuid import uuid4
from fastapi import Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from .models import Asset, Seller
from .workspace_models import ProductModel
from .product_models import ProductModelIn, validate_glb
from .workspace import record as model_record
from fastapi import APIRouter
from .dependencies import DB, merchant
from .storage import MEDIA
from .schemas import ModelAttachment

router = APIRouter()

@router.get('/api/seller/models')
def seller_models(db:DB,seller:Annotated[str,Depends(merchant)]):
    return [model_record(m) for m in db.scalars(select(ProductModel).where(ProductModel.seller_id==seller).order_by(ProductModel.created_at.desc()))]

@router.post('/api/seller/models',status_code=201)
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

@router.get('/api/assets/{asset_id}/model')
def listing_model(asset_id:str,db:DB):
    asset=db.get(Asset,asset_id)
    if not asset or not asset.active or asset.stock<=0 or not db.get(Seller,asset.seller_id).active:raise HTTPException(404,'Listing not available')
    row=db.scalar(select(ProductModel).where(ProductModel.asset_id==asset_id))
    if not row:raise HTTPException(404,'This listing has no 3D model')
    return model_record(row)

@router.post('/api/seller/models/{model_id}/attach')
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
