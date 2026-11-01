"""Verify real library counts, attribution, unique sources and local image coverage."""
from pathlib import Path
from urllib.parse import urlparse
import json,sys
ROOT=Path(__file__).resolve().parents[1]/'frontend/public'
index=json.loads((ROOT/'inspiration/index.json').read_text())
seen=set();total=0;local=0
require_local="--require-local" in sys.argv
assert len(index['categories'])==10
for category in index['categories']:
    rows=json.loads((ROOT/category['file'].lstrip('/')).read_text())
    assert len(rows)==category['count'] and len(rows)>=101,category['id']
    for row in rows:
        assert row['category']==category['id']
        assert row['sha1'] not in seen,'Repeated source image: '+row['id']
        seen.add(row['sha1'])
        assert row['creator'] and row['license'] and row['description']
        assert urlparse(row['source_url']).hostname=='commons.wikimedia.org'
        assert urlparse(row['license_url']).scheme in ('https','http')
        if row['image_url'].startswith('/inspiration/photos/'):
            path=(ROOT/row['image_url'].lstrip('/')).resolve()
            assert path.is_relative_to(ROOT.resolve()) and path.is_file(),path
            assert path.stat().st_size>0
            local+=1
        else:
            assert not require_local,'Reference requires source-host availability: '+row['id']
            assert urlparse(row['image_url']).hostname in ('upload.wikimedia.org','thumb.wikimedia.org')
    total+=len(rows)
    print(category['label'],len(rows),'attributed image references')
print('Verified',total,'distinct references across ten categories;',local,'local thumbnails.')
