"""Optional offline background inpainting, followed by exact merchant compositing.

Run from backend with MODEL_ID selecting a licensed Diffusers inpainting model.
Needs torch, diffusers, transformers, accelerate, safetensors installed separately.
White pixels in wall_mask authorize editing; black pixels protect original room.
No target app endpoint is used. GPU/model path has not been validated here.
"""
import argparse
import json
import os
from pathlib import Path
from types import SimpleNamespace

def main():
    import torch
    from diffusers import AutoPipelineForInpainting
    from PIL import Image, ImageOps
    from app.rendering import decode_image, render
    p=argparse.ArgumentParser()
    p.add_argument('--room',required=True)
    p.add_argument('--wall-mask',required=True)
    p.add_argument('--inventory',required=True,help='JSON array: id, image_url, width_cm for each chosen SKU')
    p.add_argument('--media',required=True)
    p.add_argument('--style',required=True)
    p.add_argument('--output',required=True)
    args=p.parse_args()
    model=os.environ.get('MODEL_ID')
    if not model: raise SystemExit('Set MODEL_ID to a compatible licensed inpainting model')
    if not torch.cuda.is_available(): raise SystemExit('This optional lane requires a CUDA GPU')
    room=decode_image(Path(args.room).read_bytes()).convert('RGB')
    room.thumbnail((1024,1024))
    with Image.open(args.wall_mask) as source: mask=source.convert('L').resize(room.size)
    pipeline=AutoPipelineForInpainting.from_pretrained(model,torch_dtype=torch.float16,use_safetensors=True).to('cuda')
    # Generate only wall/background treatment first; merchant pixels are inserted last.
    generated=pipeline(prompt=f'Interior architectural background, {args.style} wall finish, preserve room geometry, no furniture, no objects',image=room,mask_image=mask,num_inference_steps=30).images[0].resize(room.size)
    background=Image.composite(generated,room,mask)
    assets=[SimpleNamespace(**a) for a in json.loads(Path(args.inventory).read_text())]
    media=Path(args.media).resolve()
    for a in assets:
        if not str(a.image_url).startswith('/media/'): raise ValueError('Only inventory media references are accepted')
    placements=render(background.convert('RGBA'),assets,media,Path(args.output))
    Path(args.output+'.manifest.json').write_text(json.dumps({'mode':'background_inpainting_then_fixed_assets','model':model,'style':args.style,'placements':placements,'limitations':['Placement geometry remains approximate','No photorealistic SKU integration guarantee']},indent=2))
if __name__=='__main__': main()
