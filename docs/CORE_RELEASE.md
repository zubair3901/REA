Latest product workflow: [real seller photography](PHOTOGRAPHY_RELEASE.md). This supersedes earlier illustration/3D and single-photo setup notes below.

# Core release: agreed scope and current implementation

Premium direction is confirmed: cinematic AI video, not an interactive 3D tour. Core work remains room/home redesign, real-product catalog, complete seller workflow, confirmed investment estimate and consultation CTA.

## Implemented and locally testable

- Discover → room photo → room type/area/style/brief → investment confirmation → new/pre-loved/either → auto catalog selection or manual selection → image provider → comparison → itemized estimate → consultation request.
- Supplier and individual signup/login, expiring/revocable sessions, pending approval and owner-scoped listings.
- Listing fields: product photo, category, style, price/currency, dimensions, condition, stock, coordinates, delivery area/radius and lead time.
- Supplier bulk upload: JSON manifest plus transparent photos, up to 100 listings and 50 MB in the browser; listing creation is all-or-nothing after ownership and field validation.
- Operator workspace: approve/suspend suppliers, see consultation requests with designs/estimates, and record follow-up status. Backend requires ROOM_OPERATOR_KEY. Configure this as a private backend runtime secret, never a VITE_ variable. It is checked locally, not sent to an external provider.
- Consultation records are persisted with a webhook outbox. Optional configured booking URL can send customers to a paid scheduling event. Neither recording a booking status nor receiving a lead constitutes payment collection or an actual calendar reservation.
- Budget plans filter active/in-stock inventory, seller approval, condition, currency and optional delivery coverage. Estimated labor is included; tax, shipping and structural work are excluded. Current prices and availability are checked again before generation; stock is not reserved.

## Reference library versus commercial catalog

Imported 140 CC0 furniture/decor designs, with 560 transparent PNGs at four angles, from the official Kenney Furniture Kit. Source, original license and archive SHA256 are retained in frontend/public/reference-catalog. Reproduce with scripts/import_reference_catalog.py and the official ZIP.

These are low-poly digital illustrations, not photographic merchant products. They have no physical stock, real price, measured dimensions or delivery commitment and are not inserted into commercial quotes. The separate PNG asset library provides search, angle selection and downloads for staging/prototyping.

For realistic SKU-aware production results, suppliers must provide genuine product photography (preferably multiple angles), verified dimensions/prices and availability. Do not populate fake saleable stock to make a catalog appear large.

## Public skill applied

Anthropic frontend-design: https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md . Applied to hierarchy, readable labels, explicit failure/empty states, keyboard focus and mobile layout. The user's existing ivory/emerald visual direction is retained rather than re-themed. No third-party skill authorizes access to private image-generation services or substitutes for real provider credentials.

## Validation

Backend tests cover model request shapes with simulated provider responses, real local compositing/quotes, seller authentication/ownership, planning, operator authorization, seller suspension and atomic bulk imports. Browser checks cover reference counts/search/angle changes, restricted operator workspace, supplier bulk form and mobile layout, plus the budget-first design-to-lead journey.

Live hosted image output, live webhook delivery, real supplier availability, paid subscriptions and cinematic video output require further verification. This is a development release, not a publicly launched production service.

## Remaining launch requirements

1. Customer identity, private media storage, owned persistent projects and deletion/retention controls.
2. Real image-provider keys reaching the running backend; test image quality against real room and supplier photographs.
3. Email verification/reset, abuse throttling and reviewed operator access controls.
4. Payment checkout, signed subscription webhooks, server-side entitlements and metered usage credits for the proposed USD 25/month tier.
5. A licensed cinematic image-to-video provider, asynchronous job queue, failure/credit handling and explicit generated-video limitations.
6. Stock reservations, quantities/orders, final shipping/tax/local labor configuration and booking reconciliation.
7. Production hosting/PostgreSQL, backups, monitoring and real consultation operations.

Never promise unlimited premium inference until per-image/video costs and target margins are measured.
