Latest product workflow: [real seller photography](PHOTOGRAPHY_RELEASE.md). This supersedes earlier illustration/3D and single-photo setup notes below.

# Interactive room and seller-model release — 2026-10-27

## Implemented

The landing page has a live 3D room comparison, keyboard/touch before-and-after slider, three service examples (interior redesign, furniture installation, surface refresh), budget slider/presets, wall palette and play/pause reveal. Examples use matching room geometry with illustrative tiers, costs and furniture; they are not live AI results or vendor quotes. Automatic reveal runs once on visibility and respects reduced motion. WebGL failures show an explanation instead of breaking navigation.

Seller 3D studio includes sofa, chair, table and cabinet templates; centimeter dimensions; fabric/wood/metal materials; color; orbit and zoom; camera reset; GLB export; transparent PNG export; and authenticated backend persistence. A saved model may be attached to a seller-owned listing with matching physical dimensions. Saving again to that listing replaces its model. Customers can rotate the linked model from the catalog. An unattached GLB requires its owner's credentials to download.

Model uploads have 8 MB limits and bounded embedded geometry; external URIs, unsupported chunks/extensions and out-of-range buffers are rejected. Model ownership, seller approval/email-verification rules and matching inventory dimensions are enforced server-side. The database migration creates the new model/commission tables additively.

Local room staging uses the linked model's transparent snapshot and keeps its SKU and quote intact. Deferred image adapters can receive the same snapshot when explicitly enabled later; neither the raw GLB nor 3D geometry is currently sent to an AI model. No live AI request was made. Models are parametric approximations, not reconstructions from product photographs. Keep real photography in the listing and verify fit with the seller.

Optional MARKETPLACE_COMMISSION_PERCENT records order commission and seller net estimates. Blank leaves tracking disabled. Cancellations void the estimate. The operator sees a commission ledger and sellers see their own estimates. Commissions remain uncollected; this does not charge customers or make payouts. Agree the rate with merchants before configuring it.

## Flow fixes

Uploading a room, editing a design brief or selecting a creative engine no longer unnecessarily discards the confirmed product proposal. Changes affecting the quote (style, area, currency, condition and products) still invalidate it. The favicon is now supplied, removing a browser 404.

## Validation

28 backend tests passed against disposable PostgreSQL, including model ownership, invalid GLBs, dimension matching, snapshot-based rendering, commission calculation and cancellation, plus existing authentication, payment webhook and marketplace tests. Production React build passed. Browser checks exercised the comparison slider, service tabs, budget/palette, reveal play/pause, builder dimensions, reset, actual GLB and transparent PNG downloads, backend save, customer 3D viewer, mobile overflow, buyer plan/render/comparison/consultation flow and sidebar destinations. This is not a claim that every configuration or unavailable external integration was tested.

Reusable browser checks are in frontend/tests. Run `npm run check:interactions` and `npm run check:buyer` against an isolated test API seeded with app.seed, with a matching ROOMFORM_TEST_URL / CORS_ORIGINS and the demo merchant key `test-key` enabled via legacy test configuration. Never enable those test credentials on public staging. Chromium defaults to /usr/bin/chromium; override CHROMIUM_PATH as needed. The checks create synthetic accounts/models and save outputs to frontend/test-results.

Hosting, live AI, merchant checkout, Google Pay, email delivery and actual commission settlement retain their previously documented external configuration requirements.
