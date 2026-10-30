"""Budget-constrained catalog selection. Selection is deterministic; rendering uses AI."""
from decimal import Decimal
import os
from math import radians, sin, cos, asin, sqrt
from datetime import datetime, timezone
from uuid import uuid4
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from .database import get_db
from .models import Asset, Seller, DesignPlan
from .workspace_models import ProductPhoto
from .quotes import quote

router=APIRouter()
class PlanIn(BaseModel):
    budget: Decimal=Field(gt=0,le=10000000,max_digits=12,decimal_places=2)
    budget_confirmed: Literal[True]
    currency: str=Field(default='USD',pattern=r'^[A-Z]{3}$')
    preference: Literal['new','used','either']='either'
    style: str=Field(min_length=1,max_length=80)
    room_category: Literal['living','bedroom','office']
    room_area: float=Field(gt=0,le=1000,allow_inf_nan=False)
    latitude: float | None=Field(default=None,ge=-90,le=90,allow_inf_nan=False)
    longitude: float | None=Field(default=None,ge=-180,le=180,allow_inf_nan=False)
    @model_validator(mode='after')
    def paired_location(self):
        if (self.latitude is None)!=(self.longitude is None): raise ValueError('Supply both coordinates')
        return self

def group(asset):
    name=asset.category.lower()
    for word,category in [('sofa','seating'),('chair','seating'),('lamp','lighting'),('lighting','lighting'),('table','table'),('desk','desk'),('bed','bed'),('decor','decor'),('rug','rug')]:
        if word in name:return category
    return name

def km(a,lat,lon):
    p,q=radians(lat),radians(a.latitude)
    h=sin((q-p)/2)**2+cos(p)*cos(q)*sin(radians(a.longitude-lon)/2)**2
    return 12742*asin(min(1,sqrt(h)))

@router.post('/api/plans',status_code=201)
def plan(body:PlanIn,db=Depends(get_db)):
    query=select(Asset).join(Seller).where(Asset.active==True,Asset.stock>0,Seller.active==True,Asset.currency==body.currency)
    if os.getenv('ALLOW_LEGACY_PHOTOS','false')!='true':query=query.where(Asset.id.in_(select(ProductPhoto.asset_id).where(ProductPhoto.approved==1)))
    if body.preference=='new':query=query.where(Asset.condition=='new')
    elif body.preference=='used':query=query.where(Asset.condition!='new')
    if os.getenv('ALLOW_DEMO_CATALOG','false')!='true':query=query.where(Asset.seller_id!='demo')
    assets=db.scalars(query).all()
    if body.latitude is not None:
        assets=[a for a in assets if km(a,body.latitude,body.longitude)<=a.delivery_radius_km]
    if not assets:raise HTTPException(409,'No in-stock products match your condition, currency and delivery location. Try widening your preferences.')
    # Scale guard is a coarse filter; no geometry is inferred.
    assets=[a for a in assets if a.width_cm*a.depth_cm/10000<=body.room_area*.45]
    if not assets:raise HTTPException(409,'No matching items pass the coarse floor-area check')
    priorities={'living':['seating','table','lighting','rug','decor'],'bedroom':['bed','table','lighting','seating','rug','decor'],'office':['desk','seating','lighting','table','decor']}[body.room_category]
    groups={}
    for a in assets:groups.setdefault(group(a),[]).append(a)
    chosen=[]
    for category in priorities:
        candidates=sorted(groups.get(category,[]),key=lambda a:(a.style.lower()!=body.style.lower(),a.price,a.delivery_days,a.id))
        for candidate in candidates:
            try:estimate=quote(chosen+[candidate],body.room_area,body.room_category)
            except ValueError as exc:raise HTTPException(422,str(exc))
            if Decimal(str(estimate['total']))<=body.budget:
                chosen.append(candidate);break
    if not chosen:raise HTTPException(409,'The budget cannot cover a matching item plus estimated installation. Increase the budget or change preferences.')
    estimate=quote(chosen,body.room_area,body.room_category)
    found={group(a) for a in chosen}
    missing=[g for g in priorities[:3] if g not in found]
    record=DesignPlan(id=str(uuid4()),parameters=body.model_dump(mode='json'),asset_ids=[a.id for a in chosen])
    db.add(record);db.commit()
    return {'id':record.id,'asset_ids':record.asset_ids,'quote':estimate,'remaining_budget':float(body.budget-Decimal(str(estimate['total']))),'missing_categories':missing,'selection_method':'budget-constrained catalog matching','expires_in_seconds':1800,'limitations':['Budget includes selected items and estimated labor only; taxes, shipping and structural work excluded','No stock is reserved','Dimensions are a coarse filter; physical fit needs on-site confirmation','Missing categories indicate a partial room proposal']}

def validate_plan(db,plan_id,style,area,category):
    plan=db.get(DesignPlan,plan_id)
    if not plan:raise HTTPException(404,'Budget plan not found')
    created=plan.created_at.replace(tzinfo=timezone.utc) if plan.created_at.tzinfo is None else plan.created_at
    if (datetime.now(timezone.utc)-created).total_seconds()>1800:raise HTTPException(409,'Budget plan expired; confirm a fresh proposal')
    p=plan.parameters
    if p['style']!=style or p['room_category']!=category or p['room_area']!=area:raise HTTPException(409,'Room settings changed; confirm a fresh budget plan')
    return plan
