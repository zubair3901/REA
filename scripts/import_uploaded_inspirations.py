"""Import explicitly provided inspiration ZIPs; originals stay outside Git."""
import argparse, hashlib, io, json, re, zipfile
from pathlib import Path
from collections import Counter
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parents[1]

DESCRIPTIONS = {'living': 'A welcoming sitting area with a compact layout and coordinated furniture.', 'bedroom': 'A restful bedroom with layered textiles and a considered furniture layout.', 'kitchen': 'A compact kitchen combining practical storage and coordinated finishes.', 'office': 'A focused workspace with room for a desk, storage and everyday essentials.', 'dining': 'An intimate dining area with seating arranged for everyday meals.', 'garden': 'An outdoor retreat with planting and places to sit and unwind.', 'bathroom': 'Bathroom finishes and fixtures for a personal retreat.', 'restaurant': 'A welcoming hospitality space.', 'landscape': 'Planting and outdoor design inspiration.', 'exterior': 'Architectural exterior inspiration.'}

def categorize(name):
 s=name.lower()
 if 'studio with hidden bed' in s:return 'living'
 for category,pattern in [('kitchen',r'kitchen'),('office',r'office|workspace|desk|writing'),('bedroom',r'bedroom|\bbed\b'),('dining',r'dining|breakfast'),('garden',r'garden|courtyard|patio|terrace'),('bathroom',r'bathroom|bath'),('restaurant',r'restaurant'),('landscape',r'landscape'),('exterior',r'exterior|facade')]:
  if re.search(pattern,s):return category
 return 'living'
def style(name):
 s=name.lower()
 for match,value in [('japandi','minimalist'),('minimal','minimalist'),('nordic','scandinavian'),('scandinavian','scandinavian'),('industrial','industrial'),('boho','bohemian'),('bohemian','bohemian'),('traditional','traditional'),('classic','traditional')]:
  if match in s:return value
 return 'modern'
def run(paths):
 out=ROOT/'frontend/public/inspiration/curated';out.mkdir(parents=True,exist_ok=True)
 records=[];seen=set();duplicates=[]
 for path in sorted(paths):
  with zipfile.ZipFile(path) as z:
   for info in z.infolist():
    if info.is_dir() or info.filename.startswith('__MACOSX') or Path(info.filename).suffix.lower() not in ('.png','.jpg','.jpeg','.webp'):continue
    if info.file_size>35*1024*1024:raise ValueError('Oversized image')
    raw=z.read(info);digest=hashlib.sha256(raw).hexdigest()
    if digest in seen:duplicates.append(info.filename);continue
    seen.add(digest)
    with Image.open(io.BytesIO(raw)) as original:
     image=ImageOps.exif_transpose(original).convert('RGB');w,h=image.size
     full=image.copy();full.thumbnail((1800,1800));full.save(out/(digest[:16]+'-full.webp'),'WEBP',quality=88,method=6)
     image.thumbnail((760,1000));image.save(out/(digest[:16]+'.webp'),'WEBP',quality=83,method=6)
    name=re.sub(r'\s*\(\d+\)$','',Path(info.filename).stem).strip();category=categorize(name)
    records.append(dict(id='provided-'+digest[:16],name=name,category=category,style=style(name),description=DESCRIPTIONS[category],image='/inspiration/curated/'+digest[:16]+'.webp',full_image='/inspiration/curated/'+digest[:16]+'-full.webp',width=w,height=h,source_filename=Path(info.filename).name,sha256=digest))
 (out.parent/'curated.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'images':len(records),'categories':dict(Counter(r['category'] for r in records)),'duplicates':duplicates},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('archives',nargs='+');run(p.parse_args().archives)
