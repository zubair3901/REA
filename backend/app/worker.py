"""Run periodically: python -m app.worker. Receiver must deduplicate by event ID."""
import os
import httpx
from sqlalchemy import select
from .database import Session
from .models import Outbox

def dispatch():
    url=os.getenv('LEAD_WEBHOOK_URL','')
    if not url.startswith('https://'): raise RuntimeError('Set an HTTPS LEAD_WEBHOOK_URL')
    token=os.getenv('LEAD_WEBHOOK_TOKEN','')
    with Session() as db, httpx.Client(timeout=15,follow_redirects=False) as client:
        events=db.scalars(select(Outbox).where(Outbox.delivered==False,Outbox.attempts<10).with_for_update(skip_locked=True).limit(25)).all()
        for event in events:
            event.attempts+=1
            try:
                r=client.post(url,json=event.payload,headers={'Authorization':f'Bearer {token}','Idempotency-Key':event.id})
                r.raise_for_status();event.delivered=True
            except httpx.HTTPError: pass  # Keep payload/PII out of logs; retry next scheduled run.
        db.commit()
if __name__=='__main__': dispatch()
