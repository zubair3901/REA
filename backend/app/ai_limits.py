"""Server-side beta spend guard. Failed attempts are counted; no paid automatic retries."""
import os
from datetime import datetime,timezone,timedelta
from uuid import uuid4
from sqlalchemy import select,func
from fastapi import HTTPException
from .workspace_models import Customer,AIUsage

def reserve_attempt(db,customer_id,project_id,operation):
    try:limit=int(os.getenv('ROOM_AI_DAILY_LIMIT','3'))
    except ValueError:raise HTTPException(503,'AI usage limit is misconfigured')
    if not 0<=limit<=1000:raise HTTPException(503,'AI usage limit is misconfigured')
    db.scalar(select(Customer).where(Customer.id==customer_id).with_for_update())
    cutoff=datetime.now(timezone.utc)-timedelta(days=1)
    count=db.scalar(select(func.count()).select_from(AIUsage).where(AIUsage.customer_id==customer_id,AIUsage.created_at>=cutoff))
    if count>=limit:raise HTTPException(429,'Your rolling 24-hour AI attempt limit has been reached. No provider request was sent.')
    db.add(AIUsage(id=str(uuid4()),customer_id=customer_id,project_id=project_id,operation=operation));db.commit()
