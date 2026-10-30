"""Validate self-contained geometry assets; never fetch external model resources."""
import json,struct
from typing import Literal
from pydantic import BaseModel,Field

class ModelSpecifications(BaseModel):
    kind:Literal['sofa','chair','table','cabinet']
    width_cm:float=Field(gt=10,le=500,allow_inf_nan=False)
    height_cm:float=Field(gt=10,le=300,allow_inf_nan=False)
    depth_cm:float=Field(gt=10,le=300,allow_inf_nan=False)
    color:str=Field(pattern=r'^#[0-9a-fA-F]{6}$')
    finish:Literal['fabric','wood','metal']
class ProductModelIn(BaseModel):
    name:str=Field(min_length=2,max_length=160)
    asset_id:str|None=None
    specifications:ModelSpecifications
    thumbnail_url:str=Field(pattern=r'^/media/[a-zA-Z0-9_-]+\.png$')
    accuracy_confirmed:Literal[True]

def validate_glb(data):
    if not 20<=len(data)<=8*1024*1024:raise ValueError('Model must be a GLB smaller than 8 MB')
    magic,version,length=struct.unpack_from('<4sII',data)
    if magic!=b'glTF' or version!=2 or length!=len(data):raise ValueError('Invalid GLB 2.0 header')
    offset=12;document=None;binary_length=0;seen_binary=False
    while offset<len(data):
        if offset+8>len(data):raise ValueError('Truncated model')
        size,kind=struct.unpack_from('<II',data,offset);offset+=8
        if size%4 or offset+size>len(data):raise ValueError('Invalid model chunk')
        chunk=data[offset:offset+size];offset+=size
        if document is None:
            if kind!=0x4e4f534a or size>2*1024*1024:raise ValueError('GLB must start with bounded JSON')
            try:document=json.loads(chunk)
            except (ValueError,UnicodeError):raise ValueError('Invalid model JSON')
        elif kind==0x004e4942 and not seen_binary:binary_length=size;seen_binary=True
        else:raise ValueError('Unsupported model chunk')
    if not isinstance(document,dict) or document.get('asset',{}).get('version')!='2.0':raise ValueError('Invalid model document')
    if document.get('extensionsUsed') or document.get('extensionsRequired'):raise ValueError('Model extensions are not accepted')
    if len(document.get('nodes',[]))>500 or len(document.get('meshes',[]))>500 or len(document.get('accessors',[]))>2000:raise ValueError('Model is too complex')
    buffers=document.get('buffers',[])
    if len(buffers)!=1 or buffers[0].get('uri') or not isinstance(buffers[0].get('byteLength'),int) or not 0<buffers[0]['byteLength']<=binary_length:raise ValueError('Use one embedded GLB buffer')
    def check(value):
        if isinstance(value,dict):
            if 'uri' in value:raise ValueError('External or embedded URI resources are not accepted')
            for v in value.values():check(v)
        elif isinstance(value,list):
            for v in value:check(v)
    try:check(document)
    except RecursionError:raise ValueError('Model nesting is too deep')
    for view in document.get('bufferViews',[]):
        start=view.get('byteOffset',0);length=view.get('byteLength',0)
        if view.get('buffer',0)!=0 or not isinstance(start,int) or not isinstance(length,int) or start<0 or length<0 or start+length>binary_length:raise ValueError('Invalid model buffer range')
    for accessor in document.get('accessors',[]):
        count=accessor.get('count',0)
        if not isinstance(count,int) or not 0<=count<=1000000:raise ValueError('Model geometry exceeds limits')
    return document
