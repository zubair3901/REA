"""Media routes: HTTP adapters for a single application concern."""
import os
import re
from typing import Annotated
from uuid import uuid4
from fastapi import Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi import Request
from sqlalchemy import select
from .models import Asset, Seller
from .rendering import decode_image, MAX_BYTES
from .workspace import current_customer, project_access
from .workspace_models import ProjectDesign
from .workspace_models import ProductModel
from fastapi import APIRouter
from .dependencies import DB, merchant
from .storage import MEDIA

router = APIRouter()

@router.post('/api/uploads',status_code=201)
async def upload(file: Annotated[UploadFile,File()], seller: Annotated[str,Depends(merchant)]):
    raw=await file.read(MAX_BYTES+1)
    try: image=decode_image(raw)
    except ValueError as e: raise HTTPException(422,str(e))
    if image.getchannel('A').getextrema()[0] == 255: raise HTTPException(422,'Product image needs a transparent background')
    filename=f'{seller}_{uuid4().hex}.png'
    # Seller IDs come from operator configuration; disallow path characters.
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',seller): raise HTTPException(500,'Invalid configured seller ID')
    image.thumbnail((2000,2000)); image.save(MEDIA/filename)
    return {'image_url':f'/media/{filename}'}

@router.get('/media/{filename}')
def media_file(filename:str,request:Request,db:DB):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+\.(png|jpg|glb)',filename):raise HTTPException(404,'Image not found')
    if filename.endswith('.glb'):
        row=db.scalar(select(ProductModel).where(ProductModel.model_url=='/media/'+filename))
        if not row:raise HTTPException(404,'Model not found')
        owner=db.get(Seller,row.seller_id);asset=db.get(Asset,row.asset_id) if row.asset_id else None
        if not (owner and owner.active and asset and asset.active and asset.stock>0):
            if merchant(db,request.headers.get('X-Merchant-Key'))!=row.seller_id:raise HTTPException(404,'Model not found')
    if filename.endswith(('.jpg','.png')):
        link=db.get(ProjectDesign,filename[:-4])
        if link:
            from .operations import operator
            if request.headers.get('X-Operator-Key') or request.cookies.get('roomform_admin'):operator(request,request.headers.get('X-Operator-Key'),db)
            else:project_access(db,link.project_id,current_customer(request,db))
        elif (filename.endswith('.jpg') or re.fullmatch(r'[a-f0-9-]{36}\.png',filename)) and os.getenv('ALLOW_GUEST_PREVIEWS','false')!='true':raise HTTPException(404,'Image not found')
    path=MEDIA/filename
    if not path.is_file():raise HTTPException(404,'Image not found')
    return FileResponse(path,headers={'Cache-Control':'private, no-store' if filename.endswith(('.jpg','.png')) else 'public, max-age=3600','X-Content-Type-Options':'nosniff'})
