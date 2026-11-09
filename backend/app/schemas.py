"""Validated transport contracts for catalog, leads, photos and model attachments."""
import re
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

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

class AssetUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    stock: int | None=Field(default=None,ge=0,le=1000000)
    active: bool | None=None
    price: Decimal | None=Field(default=None,gt=0,le=10000000,max_digits=12,decimal_places=2)
    delivery_days: int | None=Field(default=None,ge=0,le=365)
    name: str | None=Field(default=None,min_length=2,max_length=160)
    category: str | None=Field(default=None,min_length=2,max_length=80)
    style: str | None=Field(default=None,min_length=2,max_length=80)
    width_cm: float | None=Field(default=None,gt=0,le=2000,allow_inf_nan=False)
    height_cm: float | None=Field(default=None,gt=0,le=2000,allow_inf_nan=False)
    depth_cm: float | None=Field(default=None,gt=0,le=2000,allow_inf_nan=False)
    condition: Literal['new','like_new','good','fair'] | None=None
    delivery_location: str | None=Field(default=None,max_length=200)
    delivery_radius_km: float | None=Field(default=None,ge=0,le=500,allow_inf_nan=False)
    latitude: float | None=Field(default=None,ge=-90,le=90,allow_inf_nan=False)
    longitude: float | None=Field(default=None,ge=-180,le=180,allow_inf_nan=False)
    image_url: str | None=Field(default=None,pattern=r'^/media/[a-zA-Z0-9_-]+\.png$')
    photo_ids: list[str] | None=Field(default=None,min_length=1,max_length=6)

class BulkAssets(BaseModel):
    assets: list[AssetIn] = Field(min_length=1,max_length=100)

class SellerOrderStatus(BaseModel):
    status:Literal['confirmed','dispatched','delivered','cancelled']

class ModelAttachment(BaseModel):
    asset_id:str=Field(min_length=1,max_length=36)

class PhotoApproval(BaseModel):
    approved:Literal[True]
    rights_confirmed:Literal[True]

class ListingPhotos(BaseModel):
    photo_ids:list[str]=Field(min_length=1,max_length=6)
    image_url:str=Field(pattern=r'^/media/[a-zA-Z0-9_-]+\.png$')

class PhotoAngle(BaseModel):
    angle:Literal['front','left','right','back','detail','angled','top']
