"""Import distinct Commons image references with attribution; never copy site assets.
Uses public MediaWiki search. Remote thumbnails are lazy-loaded by the gallery.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape
import re,json,time
import httpx

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'frontend/public/inspiration';OUT.mkdir(exist_ok=True)
CATEGORIES=[('living','Living room','"living room" interior'),('bedroom','Bedroom','bedroom interior'),('kitchen','Kitchen','kitchen interior'),('bathroom','Bathroom','bathroom interior'),('restaurant','Restaurant','restaurant interior'),('garden','Garden','garden design'),('exterior','Exteriors','house exterior'),('landscape','Landscape','landscape garden'),('office','Office','office interior'),('dining','Dining room','"dining room"')]
TARGET=110
CACHE=Path("/tmp/roomform-inspiration-cache");CACHE.mkdir(exist_ok=True)

def plain(s):return re.sub(r'\s+',' ',unescape(re.sub('<[^>]+>',' ',s or ''))).strip()
def collect(category):
 ident,label,query=category;items=[];seen=set();offset=0
 cached=CACHE/(ident+'.json')
 if cached.exists():return ident,label,json.loads(cached.read_text())
 with httpx.Client(timeout=45,follow_redirects=True,headers={'User-Agent':'RoomformInspirationImporter/1.0 (public photo attribution research)'}) as client:
  for page in range(16):
   params={'action':'query','format':'json','generator':'search','gsrsearch':query+' filetype:bitmap -drawing -floorplan -diagram -sketch -painting -map -poster','gsrnamespace':6,'gsrlimit':50,'gsroffset':offset,'prop':'imageinfo','iiprop':'url|extmetadata|sha1|size','iiurlwidth':800}
   for attempt in range(6):
    r=client.get('https://commons.wikimedia.org/w/api.php',params=params);r.raise_for_status();data=r.json()
    if not data.get('error'):break
    if data['error'].get('code')!='cirrussearch-too-busy-error':raise RuntimeError(data['error'])
    time.sleep(2+attempt*2)
   if data.get('error'):raise RuntimeError(data['error'])
   pages=sorted(data.get('query',{}).get('pages',{}).values(),key=lambda p:p.get('index',999))
   for p in pages:
    info=(p.get('imageinfo') or [{}])[0];m=info.get('extmetadata',{});meta=lambda k:plain(m.get(k,{}).get('value',''))
    name=p['title'][5:];sha=info.get('sha1');license=meta('LicenseShortName');license_url=meta('LicenseUrl')
    if not re.search(r'\.(jpg|jpeg|png|webp)$',name,re.I) or re.search(r'\b(18|19)\d{2}\b|floor.?plan|diagram|drawing|logo|map of',name,re.I):continue
    if not (license.startswith('CC BY') or license in ['CC0','Public domain','PDM']):continue
    if min(info.get('width',0),info.get('height',0))<600 or not .65<info['width']/info['height']<2.5:continue
    if not sha or sha in seen or not info.get('thumburl'):continue
    seen.add(sha)
    title=plain(re.sub(r'\.[^.]+$','',name).replace('_',' '));description=meta('ImageDescription')
    # Keep source descriptions as evidence; do not invent unseen design details.
    items.append({'id':str(p['pageid']),'category':ident,'name':title[:120],'description':(description or f'{label} photographic reference: {title}.')[:280],'image_url':info['thumburl'],'source_url':info.get('descriptionurl'),'creator':meta('Artist')[:300] or 'See source credit','license':license,'license_url':license_url or 'https://commons.wikimedia.org/wiki/Commons:Licensing','sha1':sha})
   if len(items)>=TARGET+25:break
   continuation=data.get('continue',{}).get('gsroffset')
   if continuation is None:break
   offset=continuation
  cached.write_text(json.dumps(items))
  return ident,label,items
results={}
with ThreadPoolExecutor(max_workers=1) as pool:
 for future in as_completed([pool.submit(collect,c) for c in CATEGORIES]):
  ident,label,items=future.result();results[ident]=(label,items);print(ident,len(items),'candidates',flush=True)
# Ensure that a photo is not counted twice across categories.
used=set();index=[]
for ident,label,_ in CATEGORIES:
 items=[]
 for item in results[ident][1]:
  text=item['name']+' '+item['description']
  if re.search(r'floor.?plan|ground plan|blueprint|engraving|etching|lithograph|drawing|sketch|plan of|design of|\b1[0-9]{3}[a-z]?\b',text,re.I):continue
  if item['sha1'] in used:continue
  items.append(item);used.add(item['sha1'])
  if len(items)>=TARGET:break
 items.sort(key=lambda i: -(5*bool(re.search(r'modern|luxury|contemporary|minimal|scandinav|interior design',i['name'],re.I))-7*bool(re.search(r'museum|castle|tower|queue|scaffold|IKEA|store',i['name'],re.I))))
 (OUT/(ident+'.json')).write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n')
 index.append({'id':ident,'label':label,'count':len(items),'file':'/inspiration/'+ident+'.json'})
 print(ident,'published',len(items),flush=True)
(OUT/'index.json').write_text(json.dumps({'source':'Wikimedia Commons','license_note':'Licenses and author credits are per image. Source search categorization is not a manual architectural review.','categories':index},ensure_ascii=False,indent=2)+'\n')
if any(i['count']<101 for i in index):raise SystemExit('One or more categories need additional sourced photos; see actual counts above.')
