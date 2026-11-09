"""Seller order routes: HTTP adapters for a single application concern."""
from typing import Annotated
from fastapi import Depends
from sqlalchemy import select
from .commerce import seller_order_update
from .workspace_models import Order
from fastapi import APIRouter
from .dependencies import DB, merchant
from .schemas import SellerOrderStatus

router = APIRouter()

@router.get('/api/seller/orders')
def seller_orders(db:DB,seller:Annotated[str,Depends(merchant)]):
    from .vendor_catalog import seller_order_json
    return [seller_order_json(db,o) for o in db.scalars(select(Order).where(Order.seller_id==seller).order_by(Order.created_at.desc()))]

@router.patch('/api/seller/orders/{order_id}')
def seller_order_status(order_id:str,body:SellerOrderStatus,db:DB,seller:Annotated[str,Depends(merchant)]):
    from .vendor_catalog import seller_order_json
    seller_order_update(db,order_id,seller,body.status)
    return seller_order_json(db,db.get(Order,order_id))
