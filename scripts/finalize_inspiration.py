"""Attach existing local thumbnails, preserve external references and exact counts."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]/'frontend/public'
folder=ROOT/'inspiration';index=json.loads((folder/'index.json').read_text())
used=set();referenced=set();total=0;local=0
for category in index['categories']:
    path=ROOT/category['file'].lstrip('/')
    rows=json.loads(path.read_text())
    assert len(rows)>=101
    for item in rows:
        file=folder/'photos'/(item['id']+'.webp')
        if file.is_file() and file.stat().st_size:
            item['remote_image_url']=item.get('remote_image_url',item['image_url'])
            item['image_url']='/inspiration/photos/'+file.name
        assert item['sha1'] not in used;used.add(item['sha1'])
        if item['image_url'].startswith('/inspiration/photos/'):
            referenced.add((ROOT/item['image_url'].lstrip('/')).resolve());local+=1
    def score(item):
        title=item['name']
        return 5*bool(re.search(r'modern|luxury|contemporary|minimal|scandinav|interior design',title,re.I))-7*bool(re.search(r'museum|castle|tower|queue|scaffold|IKEA|store',title,re.I))
    rows.sort(key=lambda i:(not i['image_url'].startswith('/inspiration/photos/'),-score(i)))
    category['count']=len(rows);total+=len(rows)
    path.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    print(category['label'],len(rows),'attributed references')
index['total']=total;index['local_thumbnail_count']=local
(folder/'index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
for file in (folder/'photos').iterdir():
    if file.is_file() and file.resolve() not in referenced:file.unlink()
print('Published',total,'distinct references;',local,'locally cached images.')
