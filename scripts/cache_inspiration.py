"""Cache credited thumbnails as WebP for reliable, fast local browsing.
Only resolution/encoding changes; visual source credits remain per image.
Requires FFmpeg. Re-running retries failed sources and reuses cached images.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tempfile import TemporaryDirectory
import json,subprocess,time,threading
import httpx
ROOT=Path(__file__).resolve().parents[1]/'frontend/public/inspiration'
PHOTOS=ROOT/'photos';PHOTOS.mkdir(exist_ok=True)
BACKOFF=Path('/tmp/roomform-commons-backoff.json')
rate_limited=threading.Event()
if BACKOFF.exists() and json.loads(BACKOFF.read_text()).get('until',0)>time.time():rate_limited.set()

def cache(item):
    ident=item['id'];output=PHOTOS/(ident+'.webp')
    if output.exists():return item,output.name
    if rate_limited.is_set():return item,None
    existing=[p for p in PHOTOS.glob(ident+'.*') if p.suffix!='.webp']
    raw=None
    try:
        if existing:raw=existing[0].read_bytes()
        else:
            with httpx.Client(timeout=30,follow_redirects=True,headers={'User-Agent':'RoomformInspirationPreview/1.0'}) as client:
                for attempt in range(3):
                    r=client.get(item.get('remote_image_url',item['image_url']))
                    if r.status_code==429:
                        rate_limited.set();BACKOFF.write_text(json.dumps({'until':time.time()+max(600,int(r.headers.get('retry-after','600')))}));print('Source requested download pause; remaining network fetches stopped.',flush=True);return item,None
                    if r.status_code>=500:time.sleep(2);continue
                    r.raise_for_status();break
                else:return item,None
            if not r.headers.get('content-type','').startswith('image/'):return item,None
            raw=r.content
        if not raw or len(raw)>8*1024*1024:return item,None
        with TemporaryDirectory(prefix='roomform-thumb-') as tmp:
            source=Path(tmp)/'source';source.write_bytes(raw)
            result=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-threads','1','-i',str(source),'-vf',"scale='min(640,iw)':-2",'-frames:v','1','-c:v','libwebp','-q:v','78','-threads','1',str(output)],capture_output=True)
            if result.returncode:output.unlink(missing_ok=True);return item,None
        return item,output.name
    except (httpx.HTTPError,ValueError):return item,None

for path in sorted(ROOT.glob('*.json')):
    if path.stem=='index':continue
    items=json.loads(path.read_text());count=0
    with ThreadPoolExecutor(max_workers=3) as pool:
        tasks=[pool.submit(cache,item) for item in items]
        for done,future in enumerate(as_completed(tasks),1):
            item,filename=future.result()
            if filename:
                item['remote_image_url']=item.get('remote_image_url',item['image_url'])
                item['image_url']='/inspiration/photos/'+filename;count+=1
            if done%25==0:print(path.stem,done,'checked',flush=True)
    path.write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n')
    print(path.stem,count,'/',len(items),'images cached',flush=True)
