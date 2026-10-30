"""Import the official CC0 Kenney archive supplied as a local ZIP."""
import hashlib,json,re,sys,zipfile
from pathlib import Path
from io import BytesIO
from PIL import Image
archive=Path(sys.argv[1])
out=Path(__file__).resolve().parents[1]/'frontend/public/reference-catalog'
out.mkdir(exist_ok=True)
groups={};count=0
with zipfile.ZipFile(archive) as z:
    (out/'LICENSE.txt').write_bytes(z.read('License.txt'))
    for n in z.namelist():
        if not n.startswith('Isometric/') or not n.endswith('.png'):continue
        name,angle=Path(n).stem.rsplit('_',1)
        with Image.open(BytesIO(z.read(n))) as original:
            image=original.convert('RGBA')
            if image.getchannel('A').getextrema()[0]==255:continue
            image.save(out/Path(n).name)
        count+=1
        groups.setdefault(name,{'id':name,'name':re.sub(r'(?<!^)(?=[A-Z])',' ',name).title(),'images':{},'license':'CC0','source':'https://kenney.nl/assets/furniture-kit','reference_only':True,'purchasable':False})['images'][angle]='/reference-catalog/'+Path(n).name
manifest={'source':'https://kenney.nl/assets/furniture-kit','archive_sha256':hashlib.file_digest(archive.open('rb'),'sha256').hexdigest(),'license':'CC0','note':'Low-poly digital references, not merchant inventory. No prices, stock, physical dimensions or delivery claims.','products':list(groups.values()),'image_count':count}
(out/'catalog.json').write_text(json.dumps(manifest,indent=2))
print(len(groups),'reference designs;',count,'transparent PNGs')
