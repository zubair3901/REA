"""Catalog routes: HTTP adapters for a single application concern."""
import math
import os
from typing import Annotated
from uuid import uuid4
from fastapi import Depends, HTTPException
from sqlalchemy import select
from .models import Asset, Seller
from .workspace_models import ProductPhoto
from .photography import photo_json
from fastapi import APIRouter
from .dependencies import DB, merchant
from .storage import MEDIA
from .schemas import AssetIn, AssetUpdate, BulkAssets

router = APIRouter()

@router.get('/api/assets')
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

@router.post('/api/assets',status_code=201)
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

@router.get('/api/seller/listings')
def own_listings(db: DB, seller: Annotated[str,Depends(merchant)]):
    rows=db.scalars(select(Asset).where(Asset.seller_id==seller)).all()
    return [{c.name:getattr(a,c.name) for c in Asset.__table__.columns} for a in rows]

@router.patch('/api/assets/{asset_id}')
def update_listing(asset_id:str, body:AssetUpdate, db:DB, seller:Annotated[str,Depends(merchant)]):
    asset=db.get(Asset,asset_id)
    if not asset or asset.seller_id!=seller: raise HTTPException(404,'Listing not found')
    owner=db.get(Seller,seller)
    if not owner or not owner.active: raise HTTPException(403,'Seller approval is pending')
    values=body.model_dump(exclude_unset=True)
    if any(v is None for v in values.values()):raise HTTPException(422,'Listing fields cannot be null')
    if 'image_url' in values or 'photo_ids' in values:
        from .photography import attach_photos
        from .workspace_models import ProductPhoto
        ids=values.pop('photo_ids',None)
        primary=values.get('image_url',asset.image_url)
        if not (MEDIA/primary.rsplit('/',1)[-1]).is_file():raise HTTPException(422,'Product photo file is unavailable; upload it again')
        if ids is None:ids=[p.id for p in db.scalars(select(ProductPhoto).where(ProductPhoto.asset_id==asset_id,ProductPhoto.approved==1))]
        if not ids:raise HTTPException(422,'Choose reviewed product photos for this listing')
        attach_photos(db,seller,asset.id,ids,primary)
        for photo in db.scalars(select(ProductPhoto).where(ProductPhoto.asset_id==asset_id)):
            if photo.id not in ids:photo.asset_id=None
    for key,value in values.items():setattr(asset,key,value)
    db.commit()
    return {c.name:getattr(asset,c.name) for c in Asset.__table__.columns}

@router.post('/api/seller/listings/bulk',status_code=201)
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

@router.get('/api/assets/{asset_id}')
def real_product_detail(asset_id:str,db:DB):
    asset=db.get(Asset,asset_id)
    if not asset or not asset.active or asset.stock<=0 or not db.get(Seller,asset.seller_id).active or (asset.seller_id=='demo' and os.getenv('ALLOW_DEMO_CATALOG','false')!='true'):raise HTTPException(404,'Product is currently unavailable')
    photos=db.scalars(select(ProductPhoto).where(ProductPhoto.asset_id==asset.id,ProductPhoto.approved==1)).all()
    if not photos and os.getenv('ALLOW_LEGACY_PHOTOS','false')!='true':raise HTTPException(404,'This listing needs approved real photographs')
    return {**{c.name:getattr(asset,c.name) for c in Asset.__table__.columns},'seller_name':db.get(Seller,asset.seller_id).name,'photos':[photo_json(p) for p in photos]}
