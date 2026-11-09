"""Photo routes: HTTP adapters for a single application concern."""
import re
from typing import Annotated, Literal
from uuid import uuid4
from fastapi import Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi import Request
from sqlalchemy import select
from .models import Asset, Seller
from .rendering import MAX_BYTES
from .workspace_models import ProductPhoto
from .photography import prepare_photo, photo_json, ORIGINALS
from fastapi import APIRouter
from .dependencies import DB, merchant
from .storage import MEDIA
from .schemas import PhotoApproval, ListingPhotos, PhotoAngle

router = APIRouter()

@router.post('/api/seller/photos',status_code=201)
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

@router.post('/api/seller/photos/{photo_id}/approve')
def approve_product_photo(photo_id:str,body:PhotoApproval,db:DB,seller:Annotated[str,Depends(merchant)]):
    photo=db.get(ProductPhoto,photo_id)
    if not photo or photo.seller_id!=seller:raise HTTPException(404,'Your photo was not found')
    photo.approved=1;db.commit();return photo_json(photo)

@router.get('/api/seller/photos')
def seller_photos(db:DB,seller:Annotated[str,Depends(merchant)]):
    return [photo_json(p) for p in db.scalars(select(ProductPhoto).where(ProductPhoto.seller_id==seller).order_by(ProductPhoto.created_at.desc()).limit(200))]

@router.get('/api/product-photos/{photo_id}/original')
def original_product_photo(photo_id:str,request:Request,db:DB):
    photo=db.get(ProductPhoto,photo_id)
    if not photo:raise HTTPException(404,'Photo not found')
    asset=db.get(Asset,photo.asset_id) if photo.asset_id else None;owner=db.get(Seller,photo.seller_id)
    public=photo.approved and asset and asset.active and asset.stock>0 and owner and owner.active
    if not public and merchant(db,request.headers.get('X-Merchant-Key'))!=photo.seller_id:raise HTTPException(404,'Photo not found')
    path=ORIGINALS/photo.original_file
    if not path.is_file():raise HTTPException(404,'Photo not found')
    return FileResponse(path,headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'})

@router.delete('/api/seller/photos/{photo_id}')
def delete_unattached_photo(photo_id:str,db:DB,seller:Annotated[str,Depends(merchant)]):
    photo=db.get(ProductPhoto,photo_id)
    if not photo or photo.seller_id!=seller:raise HTTPException(404,'Your photo was not found')
    if photo.asset_id:raise HTTPException(409,'Replace the listing photographs before deleting this image')
    original=ORIGINALS/photo.original_file;cutout=MEDIA/photo.cutout_url.rsplit('/',1)[-1]
    db.delete(photo);db.commit();original.unlink(missing_ok=True);cutout.unlink(missing_ok=True);return {'removed':True}

@router.post('/api/seller/listings/{asset_id}/photos')
def update_listing_photos(asset_id:str,body:ListingPhotos,db:DB,seller:Annotated[str,Depends(merchant)]):
    asset=db.get(Asset,asset_id)
    if not asset or asset.seller_id!=seller:raise HTTPException(404,'Your listing was not found')
    if not db.get(Seller,seller).active:raise HTTPException(403,'Seller approval required')
    from .photography import attach_photos
    attach_photos(db,seller,asset.id,body.photo_ids,body.image_url)
    for photo in db.scalars(select(ProductPhoto).where(ProductPhoto.asset_id==asset.id,ProductPhoto.id.not_in(body.photo_ids))):photo.asset_id=None
    asset.image_url=body.image_url;db.commit();return {'id':asset.id,'photo_ids':body.photo_ids,'image_url':asset.image_url}

@router.patch('/api/seller/photos/{photo_id}')
def label_product_angle(photo_id:str,body:PhotoAngle,db:DB,seller:Annotated[str,Depends(merchant)]):
    photo=db.get(ProductPhoto,photo_id)
    if not photo or photo.seller_id!=seller:raise HTTPException(404,'Your photo was not found')
    photo.angle=body.angle;db.commit();return photo_json(photo)
