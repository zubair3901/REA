"""Real-photo preparation. Neural matting changes alpha, never synthesizes furniture."""
import os,threading
from pathlib import Path
from io import BytesIO
from PIL import Image,ImageFilter,ImageStat,ImageOps
from fastapi import HTTPException
from sqlalchemy import select
from .database import DATA
from .models import Seller,Asset
from .workspace_models import ProductPhoto
from .rendering import decode_image

ORIGINALS=DATA/'product-originals';ORIGINALS.mkdir(exist_ok=True)
ROOMS=DATA/'private-rooms';ROOMS.mkdir(exist_ok=True)
MODEL_HOME=DATA/'matting-models';MODEL_HOME.mkdir(exist_ok=True)
_session=None;_session_model=None;_lock=threading.Lock()

def remove_background(image):
    global _session,_session_model
    if image.getchannel('A').getextrema()[0]<250:return image,'supplied_alpha'
    model=os.getenv('ROOM_MATTING_MODEL','u2netp')
    if model!='u2netp':raise HTTPException(503,'This release supports the reviewed u2netp matting model')
    path=MODEL_HOME/'u2netp.onnx'
    if not path.is_file():raise HTTPException(503,'Background-removal model is not installed. Run python -m app.prepare_vision first.')
    try:
        import numpy as np
        import onnxruntime as ort
        with _lock:
            if _session is None:
                options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
                _session=ort.InferenceSession(str(path),sess_options=options,providers=['CPUExecutionProvider']);_session_model=model
            rgb=np.asarray(image.convert('RGB').resize((320,320),Image.Resampling.LANCZOS),dtype=np.float32)
            rgb=rgb/max(float(rgb.max()),1.0)
            rgb=(rgb-np.array([.485,.456,.406],dtype=np.float32))/np.array([.229,.224,.225],dtype=np.float32)
            tensor=np.transpose(rgb,(2,0,1))[None,...].astype(np.float32)
            prediction=_session.run(None,{_session.get_inputs()[0].name:tensor})[0][0,0]
        low,high=float(prediction.min()),float(prediction.max())
        if not np.isfinite(prediction).all() or high-low<1e-8:raise HTTPException(422,'No distinct product was found. Retake the photo against a contrasting background.')
        alpha=Image.fromarray(np.clip((prediction-low)/(high-low)*255,0,255).astype('uint8')).resize(image.size,Image.Resampling.LANCZOS).filter(ImageFilter.MedianFilter(3))
        output=image.copy().convert('RGBA');output.putalpha(alpha)
        return output,'neural_u2netp'
    except HTTPException:raise
    except ImportError:raise HTTPException(503,'Install backend/requirements-vision.txt to enable automatic background removal')
    except Exception:raise HTTPException(503,'Background removal could not complete. Try a clearer photo or an existing transparent image.')

def prepare_photo(raw):
    image=decode_image(raw);image.thumbnail((1536,1536));image.info.clear()
    gray=image.convert('L');contrast=ImageStat.Stat(gray).stddev[0];edges=ImageStat.Stat(gray.filter(ImageFilter.FIND_EDGES)).mean[0]
    warnings=[]
    if min(image.size)<400:warnings.append('Low resolution: use a photo at least 800 pixels wide when possible.')
    if contrast<18 or edges<2:warnings.append('Low detail or contrast: check focus and lighting.')
    cutout,method=remove_background(image.copy())
    alpha=cutout.getchannel('A');bounds=alpha.point(lambda a:255 if a>20 else 0).getbbox()
    if not bounds:raise HTTPException(422,'No clear foreground product was found. Retake the photo against a contrasting background.')
    coverage=sum(alpha.histogram()[20:])/float(image.width*image.height)
    if coverage>.97:warnings.append('Most of the background remains. Review the cutout before approving.')
    if coverage<.03:warnings.append('The detected product is very small. Move closer and retake the photo.')
    crop=cutout.crop(bounds)
    # Preserve photographed RGB values: only crop, alpha and a transparent safety margin change.
    pad=max(8,int(max(crop.size)*.04));result=Image.new('RGBA',(crop.width+2*pad,crop.height+2*pad));result.alpha_composite(crop,(pad,pad))
    return image,result,{'method':method,'width':image.width,'height':image.height,'foreground_fraction':round(coverage,3),'warnings':warnings,'review_required':True}

def photo_json(photo):
    return {'id':photo.id,'seller_id':photo.seller_id,'asset_id':photo.asset_id,'angle':photo.angle,'cutout_url':photo.cutout_url,'original_url':'/api/product-photos/'+photo.id+'/original','quality':photo.quality,'approved':bool(photo.approved)}

def attach_photos(db,seller,asset_id,ids,primary):
    if len(set(ids))!=len(ids) or len(ids)>6:raise HTTPException(422,'Choose up to six distinct product photos')
    photos=[]
    for ident in ids:
        photo=db.get(ProductPhoto,ident)
        if not photo or photo.seller_id!=seller or (photo.asset_id and photo.asset_id!=asset_id):raise HTTPException(403,'Every photo must belong to your account and this listing')
        if not photo.approved:raise HTTPException(422,'Review and approve every cutout before publishing')
        photos.append(photo)
    if photos and primary not in [p.cutout_url for p in photos]:raise HTTPException(422,'Choose a primary image from your approved photos')
    for photo in photos:photo.asset_id=asset_id
    return photos

def reference_sets(db,assets):
    result={}
    for asset in assets:
        photos=db.scalars(select(ProductPhoto).where(ProductPhoto.asset_id==asset.id,ProductPhoto.approved==1).order_by(ProductPhoto.created_at)).all()
        photos=sorted(photos,key=lambda p:(p.cutout_url!=asset.image_url,p.angle!='front',p.id))
        if photos:result[asset.id]=[{'path':p.cutout_url,'angle':p.angle,'photo_id':p.id} for p in photos[:3]]
    return result
