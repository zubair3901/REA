"""Measured, product-protected staging. No generative edits may redraw products.
Perception is an operator-configured grounded detection + segmentation service.
Geometry checks are deterministic; photorealism and physical fit are not certified.
"""
import asyncio, base64, hashlib, json, math, os, shutil
from pathlib import Path
from urllib.parse import urlparse
from typing import Literal
from PIL import Image, ImageChops, ImageDraw, ImageFilter
import httpx
from pydantic import BaseModel, Field, ConfigDict, model_validator
from .database import DATA
from .generation import GenerationError, image_edit, png
from .rendering import decode_image

STAGES=DATA/'protected-stages';STAGES.mkdir(mode=0o700,exist_ok=True)
LABELS={'couch','sofa','table','chair','bed','rug'}
class Point(BaseModel):
    model_config=ConfigDict(extra='forbid')
    x:float=Field(ge=0,le=1,allow_inf_nan=False)
    y:float=Field(ge=0,le=1,allow_inf_nan=False)
class Placement(BaseModel):
    model_config=ConfigDict(extra='forbid')
    asset_id:str=Field(min_length=1,max_length=36)
    u:float=Field(gt=0,lt=1,allow_inf_nan=False)
    v:float=Field(gt=0,lt=1,allow_inf_nan=False)
    view:Literal['front','left','right','angled','top']='front'
class PlacementSpec(BaseModel):
    model_config=ConfigDict(extra='forbid')
    floor_quad:list[Point]=Field(min_length=4,max_length=4)
    floor_width_cm:float=Field(gt=20,le=3000,allow_inf_nan=False)
    floor_depth_cm:float=Field(gt=20,le=3000,allow_inf_nan=False)
    measurement_confirmed:Literal[True]
    placements:list[Placement]=Field(min_length=1,max_length=8)
    light_dx:float=Field(default=.25,ge=-1,le=1,allow_inf_nan=False)
    light_dy:float=Field(default=.15,ge=-1,le=1,allow_inf_nan=False)
    occlusion_mask_base64:str|None=Field(default=None,max_length=3_000_000)
    reuse_design_id:str|None=Field(default=None,pattern=r'^[a-f0-9-]{36}$')
    @model_validator(mode='after')
    def geometry(self):
        q=[(p.x,p.y) for p in self.floor_quad]
        crosses=[(q[(i+1)%4][0]-q[i][0])*(q[(i+2)%4][1]-q[(i+1)%4][1])-(q[(i+1)%4][1]-q[i][1])*(q[(i+2)%4][0]-q[(i+1)%4][0]) for i in range(4)]
        if not all(c>1e-5 for c in crosses):raise ValueError('Mark a convex floor rectangle: far left, far right, near right, near left')
        area=abs(sum(q[i][0]*q[(i+1)%4][1]-q[(i+1)%4][0]*q[i][1] for i in range(4)))/2
        if area<.015:raise ValueError('Mark a larger, clearly visible measured floor rectangle')
        if len({p.asset_id for p in self.placements})!=len(self.placements):raise ValueError('Place each selected SKU exactly once')
        return self

def capabilities():
    endpoint=os.getenv('ROOM_PERCEPTION_URL','')
    return {'enabled':os.getenv('ENABLE_PROTECTED_PLACEMENT','false')=='true','perception_configured':bool(endpoint),'calibration_required':True,'mask_convention':'white means editable; black means preserved','automatic_physical_scale':False,'supported_views':['front','left','right','angled','top'],'denoising_strength_exposed':False}

def configured_endpoint():
    if not capabilities()['enabled']:raise GenerationError('Measured product placement is not enabled on this server',503)
    endpoint=os.getenv('ROOM_PERCEPTION_URL','');url=urlparse(endpoint)
    if not endpoint:raise GenerationError('Configure a grounded detection and segmentation service before measured placement',503)
    if url.scheme!='https' or not url.hostname or url.username or url.password or url.fragment:raise GenerationError('The configured perception endpoint must be HTTPS without embedded credentials',503)
    return endpoint

def solve(matrix,vector):
    a=[list(map(float,row))+[float(v)] for row,v in zip(matrix,vector)]
    for col in range(len(vector)):
        pivot=max(range(col,len(a)),key=lambda i:abs(a[i][col]))
        if abs(a[pivot][col])<1e-10:raise ValueError('Floor perspective is degenerate; retake the room photo')
        a[col],a[pivot]=a[pivot],a[col];div=a[col][col];a[col]=[v/div for v in a[col]]
        for row in range(len(a)):
            if row!=col:
                factor=a[row][col];a[row]=[v-factor*w for v,w in zip(a[row],a[col])]
    return [row[-1] for row in a]

def homography(source,target):
    matrix=[];vector=[]
    for (u,v),(x,y) in zip(source,target):
        matrix.extend([[u,v,1,0,0,0,-x*u,-x*v],[0,0,0,u,v,1,-y*u,-y*v]]);vector.extend([x,y])
    return solve(matrix,vector)

def project(h,u,v):
    divisor=h[6]*u+h[7]*v+1
    if abs(divisor)<1e-6:raise ValueError('The marked floor approaches an unstable vanishing line')
    return ((h[0]*u+h[1]*v+h[2])/divisor,(h[3]*u+h[4]*v+h[5])/divisor)

def decode_mask(encoded,size):
    try:
        raw=base64.b64decode(encoded,validate=True)
        if len(raw)>2_000_000:raise ValueError()
        mask=decode_image(raw)
        if mask.size!=size:raise ValueError()
        # Binary luminance only; alpha is not the mask convention in this contract.
        return mask.convert('L').point(lambda p:255 if p>=128 else 0)
    except (ValueError,TypeError):raise GenerationError('Mask must be a binary PNG/JPEG/WebP matching the working room dimensions',422)

def coverage(mask):return sum(mask.histogram()[128:])/(mask.width*mask.height)

def provider_mask(mask):
    result=Image.new('RGBA',mask.size,'white');result.putalpha(ImageChops.invert(mask));return png(result)

async def perceive(room):
    endpoint=configured_endpoint()
    headers={'Authorization':'Bearer '+os.environ['ROOM_PERCEPTION_API_KEY']} if os.getenv('ROOM_PERCEPTION_API_KEY') else {}
    try:
        async with httpx.AsyncClient(timeout=90,follow_redirects=False) as client:
            response=await client.post(endpoint,headers=headers,json={'task':'grounded_segmentation','image_base64':base64.b64encode(png(room)).decode(),'classes':sorted(LABELS),'mask_convention':'white_remove_black_preserve','image_width':room.width,'image_height':room.height})
        if response.status_code!=200:raise GenerationError('The perception service did not complete. No automatic retry was sent.',503)
        if len(response.content)>4_000_000:raise GenerationError('Perception response exceeded its size limit')
        data=response.json();mask=decode_mask(data['mask_base64'],room.size)
        detections=data.get('detections',[])
        if not isinstance(detections,list) or len(detections)>32:raise ValueError()
        allowed=Image.new('L',room.size,0);draw=ImageDraw.Draw(allowed)
        for item in detections:
            box=item['box'];confidence=float(item['confidence'])
            if item['label'] not in LABELS or not math.isfinite(confidence) or confidence<.8 or confidence>1:raise GenerationError('Furniture detection is uncertain. Use a clearer room photo or the reference-guided workflow.',422)
            if len(box)!=4 or any(not isinstance(v,(float,int)) or not math.isfinite(v) for v in box):raise ValueError()
            x,y,w,h=box
            if min(x,y)<0 or min(w,h)<=0 or x+w>1.000001 or y+h>1.000001:raise ValueError()
            draw.rectangle((int(x*room.width),int(y*room.height),min(room.width-1,math.ceil((x+w)*room.width)),min(room.height-1,math.ceil((y+h)*room.height))),fill=255)
        if coverage(mask)>.60:raise GenerationError('Cleanup would affect too much of this photo. Use a clearer, less obstructed room photo.',422)
        if ImageChops.subtract(mask,allowed).getbbox():raise GenerationError('Segmentation extends outside confident furniture detections; cleanup was stopped.',422)
        if detections and not mask.getbbox():raise GenerationError('The perception service returned detections without a usable mask',422)
        return mask,{'detected_objects':len(detections),'cleanup_fraction':round(coverage(mask),4)}
    except GenerationError:raise
    except (httpx.HTTPError,ValueError,KeyError,TypeError):raise GenerationError('The perception service returned unusable detection/mask data',503)

def prepare_products(room,assets,media,photo_sets,spec):
    if set(p.asset_id for p in spec.placements)!={a.id for a in assets}:raise GenerationError('Measured placements must match every selected SKU exactly once',422)
    h=homography([(0,0),(1,0),(1,1),(0,1)],[(p.x*room.width,p.y*room.height) for p in spec.floor_quad])
    prepared=[];footprints=[]
    for placement in spec.placements:
        asset=next(a for a in assets if a.id==placement.asset_id)
        if asset.category.lower() in ('art','wall art','textiles'):raise GenerationError('This measured beta supports floor-standing items; wall placement needs a separate wall calibration',422)
        refs=(photo_sets or {}).get(asset.id,[])
        reference=next((r for r in refs if r['angle']==placement.view),None)
        if reference is None:raise GenerationError(f'{asset.name} needs an approved {placement.view} photograph. Choose a supported photographed view; unseen sides will not be invented.',422)
        product=decode_image((media/reference['path'].rsplit('/',1)[-1]).read_bytes())
        if product.getchannel('A').getextrema()[0]>0:raise GenerationError('Use a reviewed transparent product cutout for measured placement',422)
        bounds=product.getchannel('A').getbbox()
        if not bounds:raise GenerationError('The selected product photo is empty',422)
        product=product.crop(bounds)
        width=asset.width_cm/spec.floor_width_cm;depth=asset.depth_cm/spec.floor_depth_cm
        u,v=placement.u,placement.v;footprint=(u-width/2,v-depth,u+width/2,v)
        if min(footprint)<0 or max(footprint)>1:raise GenerationError(f'{asset.name} does not fit within the measured floor rectangle at that position',422)
        for other in footprints if asset.category.lower()!='rug' else []:
            if min(footprint[2],other[2])-max(footprint[0],other[0])>1e-5 and min(footprint[3],other[3])-max(footprint[1],other[1])>1e-5:raise GenerationError('Selected product footprints overlap. Move the products apart.',422)
        if asset.category.lower()!='rug':footprints.append(footprint)
        if asset.category.lower()=='rug':
            if placement.view!='top':raise GenerationError('Rug floor warping needs an approved top-down photograph',422)
            target=[project(h,footprint[0],footprint[1]),project(h,footprint[2],footprint[1]),project(h,footprint[2],footprint[3]),project(h,footprint[0],footprint[3])]
            inverse=homography(target,[(0,0),(product.width,0),(product.width,product.height),(0,product.height)])
            warped=product.transform(room.size,Image.Transform.PERSPECTIVE,inverse,Image.Resampling.BICUBIC,fillcolor=(0,0,0,0))
            bounds=warped.getchannel('A').getbbox()
            if not bounds:raise GenerationError('Rug footprint is not visible',422)
            prepared.append({'asset':asset,'photo':reference,'image':warped.crop(bounds),'x':bounds[0],'y':bounds[1],'v':v,'footprint':footprint,'geometry_method':'measured_floor_homography','view':'top'})
            continue
        if placement.view=='top':raise GenerationError('Use a compatible upright view for solid furniture',422)
        left=project(h,u-width/2,v);right=project(h,u+width/2,v);anchor=project(h,u,v)
        pixel_width=math.dist(left,right)
        # Solid furniture stays a uniformly scaled photograph, never a flat projective warp.
        if placement.view!='front':pixel_width*=((asset.width_cm+asset.depth_cm)/math.sqrt(2))/asset.width_cm
        target_width=round(pixel_width);target_height=round(product.height*pixel_width/product.width)
        if not 8<=target_width<=room.width or not 8<=target_height<=room.height:raise GenerationError('This product view cannot be scaled credibly into the measured photo. Use a compatible photo angle.',422)
        product=product.resize((target_width,target_height),Image.Resampling.LANCZOS)
        x=round(anchor[0]-target_width/2);y=round(anchor[1]-target_height)
        if x<0 or y<0 or x+target_width>room.width or y+target_height>room.height:raise GenerationError('A product would be clipped by the image. Choose a different placement or wider room photo.',422)
        prepared.append({'asset':asset,'photo':reference,'image':product,'x':x,'y':y,'v':v,'footprint':footprint,'geometry_method':'measured_floor_uniform_photo_scale','view':placement.view})
    return sorted(prepared,key=lambda p:(p['asset'].category.lower()!='rug',p['v']))

def stage_products(empty,prepared,spec,occlusion=None,foreground_source=None):
    stage=empty.convert('RGBA');product_mask=Image.new('L',stage.size,0);layers=[];hotspots=[];shadow_mask=Image.new('L',stage.size,0)
    for p in prepared:
        image=p['image'];x,y=p['x'],p['y'];w,h=image.size
        shadow=Image.new('L',stage.size,0);draw=ImageDraw.Draw(shadow)
        cx=x+w/2+spec.light_dx*w*.12;cy=y+h+spec.light_dy*w*.08
        draw.ellipse((cx-w*.44,cy-max(2,w*.04),cx+w*.44,cy+max(2,w*.04)),fill=65)
        shadow=shadow.filter(ImageFilter.GaussianBlur(max(2,w*.025)));shadow_mask=ImageChops.lighter(shadow_mask,shadow)
        layer=Image.new('RGBA',stage.size);layer.alpha_composite(image,(x,y));layers.append(layer)
    shadow_layer=Image.new('RGBA',stage.size,(0,0,0,0));shadow_layer.putalpha(shadow_mask);stage=Image.alpha_composite(stage,shadow_layer)
    for p,layer in zip(prepared,layers):
        stage=Image.alpha_composite(stage,layer);product_mask=ImageChops.lighter(product_mask,layer.getchannel('A'))
        hotspots.append({'asset_id':p['asset'].id,'x':p['x']/stage.width,'y':p['y']/stage.height,'width':p['image'].width/stage.width,'height':p['image'].height/stage.height,'source':'measured_photo_overlay','confidence':None})
    if occlusion is not None:
        # Retained room foreground is restored locally, not regenerated by the provider.
        stage=Image.composite((foreground_source or empty).convert('RGBA'),stage,occlusion)
        product_mask=ImageChops.subtract(product_mask,occlusion)
    for i,(p,layer) in enumerate(zip(prepared,layers)):
        original=layer.getchannel('A').point(lambda a:255 if a>0 else 0);visible=original.copy()
        for front in layers[i+1:]:visible=ImageChops.subtract(visible,front.getchannel('A').point(lambda a:255 if a>0 else 0))
        if occlusion is not None:visible=ImageChops.subtract(visible,occlusion)
        fraction=coverage(visible)/max(coverage(original),1e-9)
        p['visible_fraction']=round(fraction,3)
        if fraction<.20:raise GenerationError(f"{p['asset'].name} would be mostly hidden. Adjust the layout or foreground mask.",422)
    binary=product_mask.point(lambda a:255 if a>0 else 0)
    if coverage(binary)<.0005:raise GenerationError('The selected products are not visibly placed in this view',422)
    # Only contact/shadow surroundings can change. All source-product pixels are locked.
    ring=ImageChops.subtract(binary.filter(ImageFilter.MaxFilter(31)),binary)
    ring=ImageChops.lighter(ring,shadow_mask.point(lambda a:255 if a>0 else 0))
    ring=ImageChops.subtract(ring,binary)
    if occlusion is not None:ring=ImageChops.subtract(ring,occlusion)
    return stage.convert('RGB'),binary,ring,hotspots

async def generate_protected(model,room,assets,media,output,spec,photo_sets,reserve,reuse=None):
    configured_endpoint()
    room=room.copy();room.thumbnail((1280,960));room=room.convert('RGB');fingerprint=hashlib.sha256(png(room)).hexdigest()
    prepared=await asyncio.to_thread(prepare_products,room,assets,media,photo_sets,spec)
    occlusion=decode_mask(spec.occlusion_mask_base64,room.size) if spec.occlusion_mask_base64 else None
    await asyncio.to_thread(stage_products,room,prepared,spec,occlusion,room)
    if reuse:
        if reuse['room_hash']!=fingerprint or reuse['provider']!=model:raise GenerationError('The cached room does not match this image/provider. Disable reuse and create a fresh cleanup.',409)
        empty=decode_image(reuse['empty_path'].read_bytes()).convert('RGB')
        if empty.size!=room.size:raise GenerationError('Cached room dimensions do not match',409)
        detection={'cleanup_reused':True}
        reserve(['protected_harmonization'])
    else:
        reserve(['grounded_segmentation','protected_cleanup','protected_harmonization'])
        cleanup,detection=await perceive(room)
        if occlusion is not None:cleanup=ImageChops.subtract(cleanup,occlusion)
        if cleanup.getbbox():
            edited=await image_edit(model,[png(room)],'Remove ONLY the furniture inside the editable mask. Reconstruct the exposed floor/wall behind it. Preserve architecture, windows, camera, lighting and all unmasked objects. Add no furniture or decoration. Return the cleaned room.',provider_mask(cleanup))
            edited=edited.convert('RGB').resize(room.size,Image.Resampling.LANCZOS)
            empty=Image.composite(edited,room,cleanup)
        else:empty=room.copy()
    stage,protected,ring,hotspots=await asyncio.to_thread(stage_products,empty,prepared,spec,occlusion,room)
    harmonized=await image_edit(model,[png(stage)],'Harmonize ONLY the contact/shadow mask around the already placed photographed furniture. Adjust contact shadows and immediate surrounding light only. Never redraw, recolor, repair or replace any product. Preserve all architecture and camera geometry. Add no objects. The product is a protected photographic layer; do not invent its hidden surfaces.',provider_mask(ring))
    harmonized=harmonized.convert('RGB').resize(stage.size,Image.Resampling.LANCZOS)
    result=Image.composite(harmonized,stage,ring)
    result=Image.composite(stage,result,protected)
    if ImageChops.multiply(ImageChops.difference(result,stage),Image.merge('RGB',(protected,protected,protected))).getbbox():raise GenerationError('Product pixel preservation check failed; output was not published')
    # PNG avoids JPEG changing protected pixels after the QA check.
    cache=STAGES/output.stem;cache.mkdir(mode=0o700,exist_ok=True)
    try:
        empty.save(cache/'empty.png','PNG');os.chmod(cache/'empty.png',0o600)
        if occlusion is not None:occlusion.save(cache/'foreground.png','PNG');os.chmod(cache/'foreground.png',0o600)
        result.save(output,'PNG')
    except Exception:
        shutil.rmtree(cache,ignore_errors=True);output.unlink(missing_ok=True);raise
    placements=[{'asset_id':p['asset'].id,'x':p['x'],'y':p['y'],'width':p['image'].width,'height':p['image'].height,'quantity':1,'status':'protected_photograph_composited','reference_photo_ids':[p['photo']['photo_id']],'reference_source':'seller_photograph','geometry_method':p['geometry_method'],'view':p['view'],'visible_fraction':p['visible_fraction']} for p in prepared]
    report={'product_pixels_preserved':True,'fit_guaranteed':False,'photorealism_validated':False,'geometry_source':'customer_measured_floor_rectangle','view_source':'approved_photograph_angle_label','denoising_strength':None,'harmonization_scope':'contact_ring_only','cleanup':detection,'occlusion_source':'customer_mask' if occlusion else 'not_supplied','paid_retry_count':0,'reserved_attempt_slots':1 if reuse else 3}
    return placements,hotspots,report,{'room_hash':fingerprint,'provider':model,'has_occlusion':occlusion is not None,'spec':spec.model_dump(exclude={'occlusion_mask_base64','reuse_design_id'})}
