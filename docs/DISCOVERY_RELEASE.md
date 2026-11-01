# Discovery and room-transformation release

Approved scope: take inspiration from the publicly accessible home-design.ai
homepage, keep original Roomform branding/copy/assets, and connect room discovery
to real furniture/decor sellers, budgets and consultation. The reference's inner
pages could not be inspected, and no access to the user's Mac browser is claimed.

## Interface changes

- Full photographic hero, large editorial typography, room comparison slider and
  one primary redesign CTA.
- Room entry cards for the currently supported living room, bedroom and office
  categories. No unimplemented exterior/floor-plan/video tools are advertised.
- Separate inspiration page with six credited photo directions, room filtering,
  and actions that prefill the design brief and open the studio.
- Navigation separates Design studio, Inspiration, Shop and Professionals. Seller,
  business and consultation entry points remain available. Query-string pages
  support browser back/forward and direct reloads without SPA server rewrites.
- Homepage real-product explanation, tool discovery, FAQ and consultation CTA.
- Existing guided studio, product-photo results, estimates and seller workspace
  remain connected to their actual backend routes.

## GIF assets and motion

`frontend/public/demos/living.gif` and `bedroom.gif` are seven-second, 70-frame
loops, 560×374 pixels, approximately 241 KB and 278 KB. Each holds the empty view,
wipes to the furnished photo, holds, then returns. They are original animations
of credited inspiration photos and AI-edited empty-room versions, not live
customer outputs or purchasable SKU combinations.

The page uses IntersectionObserver to load animation near the viewport; offscreen
and paused demos display still images. Pause/play buttons are accessible and the
default is a still image for `prefers-reduced-motion`. GIFs require no AI key,
third-party video player or external animation service.

Rebuild with `python scripts/build_demos.py` (FFmpeg required). Generated source
photographs and attribution are included; no reference-site assets were copied.

## Verification

- Production frontend build.
- `npm run check:discovery`: actual GIF loading, pause/play, reduced motion,
  inspiration filters, project entry, history/reload, FAQ and responsive navigation.
- `npm run check:photography`: actual JPEG preparation, cutout review, listing,
  original photo gallery, authenticated buyer budget/layout, hotspots, full view,
  region editing, comparison and mobile layout, against an isolated test API.

AI and payment activation remain separate configuration/testing work. No new
provider integration, payment collection or exact-product fidelity is claimed.
