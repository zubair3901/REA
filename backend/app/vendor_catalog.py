"""Seller-maintained catalogue attributes and platform-controlled delivery instructions."""
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import select
from .database import get_db
from .models import Asset, Seller
from .workspace_models import AssetCatalogDetails, SellerDeliveryPlan, Order
from .operations import operator
from .workspace import audit

router=APIRouter()
def seller_auth(db=Depends(get_db),key:Annotated[str|None,Header(alias='X-Merchant-Key')]=None):
    from .main import merchant
    return merchant(db,key)
def owned(db,ident,seller):
    asset=db.get(Asset,ident)
    if not asset or asset.seller_id!=seller:raise HTTPException(404,'Listing not found')
    return asset
Short=Annotated[str,Field(min_length=1,max_length=100)]
Style=Literal['minimalist','industrial','scandinavian','bohemian','traditional','mid-century','modern','japandi']
class Color(BaseModel):
    model_config=ConfigDict(extra='forbid')
    name:Short
    hex:str=Field(pattern=r'^#[0-9a-fA-F]{6}$')
class ShippingDimensions(BaseModel):
    model_config=ConfigDict(extra='forbid')
    width:float=Field(gt=0,le=5000,allow_inf_nan=False)
    depth:float=Field(gt=0,le=5000,allow_inf_nan=False)
    height:float=Field(gt=0,le=5000,allow_inf_nan=False)
class CatalogIn(BaseModel):
    model_config=ConfigDict(extra='forbid')
    sku:str=Field(default='',max_length=100)
    brand:str=Field(default='',max_length=160)
    mpn:str=Field(default='',max_length=100)
    parent_asset_id:str|None=Field(default=None,max_length=36)
    description:str=Field(default='',max_length=5000)
    style_tags:list[Style]=Field(default_factory=list,max_length=8)
    dominant_colors:list[Color]=Field(default_factory=list,max_length=12)
    materials:list[Short]=Field(default_factory=list,max_length=20)
    finishes:list[Short]=Field(default_factory=list,max_length=20)
    textures:list[Short]=Field(default_factory=list,max_length=20)
    silhouette:str=Field(default='',max_length=200)
    placement:Literal['freestanding','floor-standing','wall-mounted','tabletop-only','ceiling-mounted']='freestanding'
    shipping_dimensions_cm:ShippingDimensions|None=None
    weight_kg:float|None=Field(default=None,gt=0,le=100000,allow_inf_nan=False)
    shipping_weight_kg:float|None=Field(default=None,gt=0,le=100000,allow_inf_nan=False)
    msrp:Decimal|None=Field(default=None,gt=0,le=10000000,max_digits=12,decimal_places=2)
    sale_price:Decimal|None=Field(default=None,gt=0,le=10000000,max_digits=12,decimal_places=2)
    @model_validator(mode='after')
    def prices(self):
        if self.sale_price is not None and self.msrp is not None and self.sale_price>self.msrp:raise ValueError('Sale price cannot exceed MSRP')
        if self.shipping_weight_kg is not None and self.weight_kg is not None and self.shipping_weight_kg<self.weight_kg:raise ValueError('Shipping weight cannot be less than product weight')
        return self
@router.get('/api/assets/{asset_id}/catalog-details')
def get_details(asset_id:str,seller=Depends(seller_auth),db=Depends(get_db)):
    owned(db,asset_id,seller);row=db.get(AssetCatalogDetails,asset_id)
    return {'asset_id':asset_id,'details':row.details if row else CatalogIn().model_dump(mode='json'),'price_basis':'Listing price is authoritative; MSRP and sale fields are reference metadata only'}
@router.put('/api/assets/{asset_id}/catalog-details')
def save_details(asset_id:str,body:CatalogIn,seller=Depends(seller_auth),db=Depends(get_db)):
    owned(db,asset_id,seller)
    owner=db.scalar(select(Seller).where(Seller.id==seller).with_for_update())
    if not owner or not owner.active:raise HTTPException(403,'Seller approval required')
    if body.parent_asset_id:
        current=body.parent_asset_id;seen={asset_id}
        while current:
            if current in seen:raise HTTPException(422,'Variant relationships cannot form a cycle')
            seen.add(current);owned(db,current,seller)
            parent=db.get(AssetCatalogDetails,current);current=parent.details.get('parent_asset_id') if parent else None
    if body.sku.strip():
        for row in db.scalars(select(AssetCatalogDetails).join(Asset,Asset.id==AssetCatalogDetails.asset_id).where(Asset.seller_id==seller,Asset.id!=asset_id)):
            if row.details.get('sku','').strip().casefold()==body.sku.strip().casefold():raise HTTPException(409,'This merchant SKU is already used by another listing')
    details=body.model_dump(mode='json');row=db.get(AssetCatalogDetails,asset_id)
    if row:row.details=details
    else:db.add(AssetCatalogDetails(asset_id=asset_id,details=details))
    db.commit();return {'asset_id':asset_id,'details':details,'price_basis':'Listing price is authoritative; MSRP and sale fields are reference metadata only'}

class DeliveryPlanIn(BaseModel):
    model_config=ConfigDict(extra='forbid')
    delivery_date:str=Field(max_length=10)
    address:str=Field(min_length=10,max_length=500)
    instructions:str=Field(default='',max_length=2000)
    @field_validator('delivery_date')
    @classmethod
    def valid_date(cls,v):return date.fromisoformat(v).isoformat()
@router.put('/api/operator/platform/orders/{order_id}/delivery-plan',dependencies=[Depends(operator)])
def schedule(order_id:str,body:DeliveryPlanIn,request:Request,db=Depends(get_db)):
    order=db.get(Order,order_id)
    if not order:raise HTTPException(404,'Order not found')
    if order.status in ('cancelled','delivered'):raise HTTPException(409,'This order cannot be scheduled')
    row=db.get(SellerDeliveryPlan,order_id)
    if row:
        for k,v in body.model_dump().items():setattr(row,k,v)
    else:db.add(SellerDeliveryPlan(order_id=order_id,**body.model_dump()))
    audit(db,getattr(request.state,'administrator_id','legacy-operator'),'order.delivery_scheduled',order_id,{'delivery_date':body.delivery_date})
    db.commit();return {'order_id':order_id,**body.model_dump()}
def seller_order_json(db,order):
    plan=db.get(SellerDeliveryPlan,order.id)
    return {'id':order.id,'seller_id':order.seller_id,'status':order.status,'created_at':order.created_at,
            'items':[{k:i.get(k) for k in ('asset_id','name','quantity')} for i in order.items],
            'address':plan.address if plan else '', 'delivery_date':plan.delivery_date if plan else None,
            'instructions':plan.instructions if plan else '', 'delivery_plan_status':'scheduled' if plan else 'awaiting_platform_schedule',
            'notice':'Roomform coordinates the project and supplier payment. Deliver only against the platform-issued schedule.'}
