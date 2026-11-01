# Worker demos and ten-category inspiration library

The hero remains a manual before/after image slider. The living-room and bedroom
GIFs below it are AI-illustrated, six-stage installation montages: empty room,
workers preparing, carrying/assembling furniture, styling, and a finished room.
They are not continuous real-world video or claims about renovation time. Both
have play/pause controls, viewport-aware loading and reduced-motion stills.
Source storyboards and the reproducible FFmpeg builder are included.

## Library

The published library contains 110 distinct source-image references in each of ten categories, 1,100 total:
living room, bedroom, kitchen, bathroom, restaurant, garden, exteriors, landscape,
office and dining room. These are actual attributed Commons image records, not
repeated stock photos relabeled to inflate counts. Different photographs may show
the same building or space; this is a photo-reference library, not 1,100 verified
unique renovation projects. Search categorization is not a manual review of every
photo's design quality or suitability.

Each card has a short source description, creator/license disclosure, and exactly
one design CTA: “Design this”. Categories have search and pagination (24 images
per page). Category selections persist in the URL. Images lazy-load. Credits and
license terms remain attached to every source. 506 thumbnails are cached locally;
the remaining 594 retain their public Commons image URLs and depend on source-host
availability. The source requested a bulk-download pause, so the importer stops
network work on HTTP 429 and honors the requested cooldown. The UI has a clear
unavailable-photo fallback. Cached thumbnails are encoded for local preview speed. Import and cache scripts are included.

“Design this” prefills the category and textual reference brief in the studio. It
does not silently turn a kitchen into a living room or pretend that objects in a
reference photo are actual seller stock. The API now validates all ten categories
and has matching catalog-selection priorities.

## Estimates and AI

New category installation rates must be explicitly configured in
`LABOR_RATES_JSON`. Existing living/bedroom/office USD baselines are unchanged;
other categories fail clearly if their local labor rate is missing. No arbitrary
renovation prices are invented for plumbing, structural work or landscaping.
The studio discloses the need for an installation estimate before budgeted rendering. Provider availability and live product
fidelity remain separate configuration and validation work.

## Verification

Backend tests cover category validation, rejection when rates are absent, and
budget proposal success using an explicitly configured category rate. Frontend
checks cover all category counts, source-hash uniqueness, attribution, category
switching, pagination, search, the single design CTA, worker GIF controls, reduced
motion, the unchanged hero slider and mobile navigation. The existing seller →
photo preparation → listing → buyer budget/layout → hotspot flow remains tested.
