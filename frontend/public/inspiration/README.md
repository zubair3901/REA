# Attributed inspiration reference library

Ten categories, each containing more than 100 distinct image references from
Wikimedia Commons. Exact published counts are in index.json. Source search results are filtered for reusable licenses, minimum image
size, duplicate file hashes and obvious plans/drawings/archival scans. They have
not all been individually reviewed for architectural relevance or design quality.
They are inspiration references, never merchant stock or purchasable products.

Every category JSON retains the original creator, source file page, source image
URL, license name, license URL, and original Commons SHA-1. The website shows those
credits and license links below each image. Images are not relicensed as Roomform
assets. Their original licenses continue to apply, including attribution and
share-alike obligations where applicable. WebP thumbnails under `photos/` are resized/re-encoded copies; JPEG thumbnails
retain source encoding. Otherwise the visual content is unchanged.

Source descriptions may mention locations, designers, shops or historical rooms;
those are public source metadata, not claims of a Roomform partnership. Clicking
“Design this” carries a category and a textual brief into the studio, not a claim
that furniture shown in the reference is stocked by Roomform sellers.

Rebuild metadata: `.venv/bin/python scripts/import_inspiration.py` (httpx).
Cache thumbnails: `.venv/bin/python scripts/cache_inspiration.py` (httpx, FFmpeg).
Then check actual source counts and cached-image coverage before publishing.

Current snapshot: 1,100 source references; 506 cached local thumbnails. The other
594 are public remote thumbnails and require source-host availability. Bulk caching
paused when Commons requested a cooldown; the downloader stops network requests
on HTTP 429. Failed images show an explicit fallback, never an unrelated picture.
After caching, run `python scripts/finalize_inspiration.py` to attach newly cached
files, followed by `python scripts/verify_inspiration.py`. Use
`--require-local` with verification only when all references have been cached.
