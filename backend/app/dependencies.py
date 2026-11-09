"""Request-scoped database and seller authentication dependencies."""
import hmac
import json
import os
from typing import Annotated
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session as DBSession
from .database import get_db
from .accounts import session_seller

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
