"""Operator smoke: one real, potentially billable generation request; no automatic retries."""
import argparse
import asyncio
import json
from pathlib import Path
from sqlalchemy import select
from uuid import uuid4
from .database import Session, DATA
from .models import Asset
from .rendering import decode_image
from .generation import generate,models

async def main():
    p=argparse.ArgumentParser();p.add_argument('--provider',choices=['openai','gemini'],required=True);p.add_argument('--room',required=True);p.add_argument('--asset-id',action='append',required=True);p.add_argument('--style',default='modern');args=p.parse_args()
    if not next(m for m in models() if m['id']==args.provider)['available']: raise SystemExit('Provider key is not injected into this process')
    with Session() as db:
        assets=db.scalars(select(Asset).where(Asset.id.in_(args.asset_id),Asset.stock>0,Asset.active==True)).all()
        if len(assets)!=len(set(args.asset_id)) or len(assets)>8: raise SystemExit('Select 1–8 available catalog IDs')
        output=DATA/'media'/f'smoke-{uuid4()}.jpg'
        placements=await generate(args.provider,decode_image(Path(args.room).read_bytes()),assets,DATA/'media',output,args.style,'living',25)
        print(json.dumps({'output':str(output),'references':placements,'fidelity':'requires human review'}))
if __name__=='__main__': asyncio.run(main())
