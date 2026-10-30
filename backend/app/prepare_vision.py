"""Explicit, checksum-pinned model installation. Uploads never download models."""
import hashlib,urllib.request,os
from .photography import MODEL_HOME
MODEL_URL='https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx'
MODEL_SHA256='309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8'
def install():
    if os.getenv('ROOM_MATTING_MODEL','u2netp')!='u2netp':raise SystemExit('Only u2netp is enabled in this release')
    target=MODEL_HOME/'u2netp.onnx'
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==MODEL_SHA256:
        print('Verified background-removal model is ready');return
    temp=target.with_suffix('.download')
    try:
        with urllib.request.urlopen(MODEL_URL,timeout=60) as response,open(temp,'wb') as out:
            total=0
            while chunk:=response.read(1024*1024):
                total+=len(chunk)
                if total>8*1024*1024:raise ValueError('Model download exceeds the expected size limit')
                out.write(chunk)
        if hashlib.sha256(temp.read_bytes()).hexdigest()!=MODEL_SHA256:raise ValueError('Matting model checksum does not match')
        temp.replace(target);print('Verified background-removal model installed')
    finally:temp.unlink(missing_ok=True)
if __name__=='__main__':install()
