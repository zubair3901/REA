# Roomform project overview — 1 November 2026

## Executive status

Roomform has an implemented web marketplace foundation and a tested development
backend. It is suitable for controlled development/pilot testing, not a public
production launch. There is no externally deployed private staging site. The
latest rendering integration is a measured, product-protected **beta** tested
with simulated providers; no live Gemini/OpenAI/SAM quality result is claimed.

The React frontend build passes. The current Python suite has **48 passing tests**
on SQLite. The photographic seller/buyer browser flow, discovery/library checks,
and new measured-placement UI checks pass. The latter simulates AI readiness and
the final POST, while using actual local accounts/projects/catalog interactions.
Earlier PostgreSQL checks covered a previous release; final staging validation of
the latest integration against hosted PostgreSQL remains necessary.

At this review, this runtime has no ROOM_GEMINI_API_KEY, ROOM_OPENAI_API_KEY,
ROOM_PERCEPTION_URL, SMTP_HOST or STRIPE_SECRET_KEY. Values were not printed or
committed. Configuration examples are not active service bindings.

## Product and current scope

Customers plan a room, set their investment and new/pre-loved preference, explore
real seller references, save a design, request products and book consultation.
Merchants and individual resale sellers list real furniture/decor. Skilled
professionals receive service requests. Business accounts share projects using
named seats. REA informed initial app inspection; Roomform runs its own React,
FastAPI and database implementation rather than the original app's private APIs.

Current rendering handles up to eight distinct SKUs, one instance per SKU. It is
room-by-room visualization, not complete architectural planning or an automated
whole-home construction system. Floor plans, cinematic AI video generation,
continuous walkthroughs and automated contractor procurement are not implemented.
Worker-style GIFs are AI-illustrated promotional montages, not generated customer
videos or evidence of an automated renovation service.

## Frontend

- React 19 / Vite, responsive navigation, local fonts and original Roomform styling.
- Landing page: manual comparison slider, two worker-installation GIFs with pause
  and reduced-motion controls, room entry cards, sourcing explanation and CTA.
- Inspiration: ten categories, 110 references each (1,100 total), descriptions,
  one “Design this” action per card, credits, search and pagination. 506 thumbnails
  are local; 594 use public Commons URLs and depend on source availability.
  Inspiration is not merchant stock. “Design this” transfers a category/brief.
- Studio: saved-project selection, photo upload, budget/currency, new/pre-loved
  preference, catalog matching/manual selection, style and provider selection.
- Results: comparison, large/full-view canvas, SKU hotspots, original product
  photography, estimates, replacements, download, product and consultation CTAs.
- Measured beta: four floor corners, confirmed physical width/depth, product-view
  and position controls, light direction, optional foreground mask and cleanup reuse.
- Seller portal: merchant/individual registration, approval status, photograph
  preparation/review, listing creation, inventory updates and order status.
- Professional, business/team, customer project and operator interfaces exist.

The frontend can be previewed through VS Code/Vite alone. Accounts, saved work,
stock, quotes and orders require the backend. Your Mac's Python-wheel compatibility
is not confirmed resolved: the last report was a pydantic-core installation error,
and its Python version/architecture were not supplied. Python 3.12 is the tested
backend environment; VS Code by itself does not remove Python dependencies.

## Backend layers

Python FastAPI exposes validated APIs; SQLAlchemy manages relational data. SQLite
is local development storage. PostgreSQL 16 is the supplied deployment database.
Core records include customers/sessions, sellers/accounts, assets/product photos,
projects/designs/scenes, plans/quotes, orders, professionals/service requests,
organizations/memberships, payments/credits, mail/outbox, audit and quota records.

Key modules: `main.py` (catalog/design APIs), `photography.py` (actual-photo
preparation), `planning.py`/`quotes.py` (selection and pricing), `workspace.py`
(accounts/projects/teams), `commerce.py` (orders/services), `payments.py`,
`scene_routes.py` (results/replacement), `generation.py` (provider adapters), and
`protected_placement.py` (measured protected workflow).

### Seller and inventory mechanism

1. Seller creates an account as merchant or individual; account approval gates
   publishing. Email verification is required when secure-staging settings enable it.
2. Seller uploads their actual product photo. Transparent photos can be used
   directly; optional CPU U2NETP/ONNX matting removes other backgrounds.
3. Seller reviews the cutout, confirms rights, and labels available angles.
   Additional angles are optional. Top-down photos are supported for rug warping.
4. Listing stores price/currency, dimensions, condition, stock, location, delivery
   radius and lead time. Public matching respects active sellers/listings and stock.
5. Original seller photographs remain linked to the SKU. Synthetic references are
   hidden by default. Real launch inventory must still be onboarded; test fixtures
   are not operational merchant stock.

### Buyer, budget and orders

1. Authenticate and create/select a private or authorized shared project.
2. Upload a room and confirm budget, currency and condition preference.
3. Choose products manually or request a deterministic budget-constrained proposal.
4. The backend checks current listing prices, availability, delivery coverage and
   coarse floor-area constraints. It does not reserve stock for an image preview.
5. Estimate = item subtotals + configured area-based installation labor. Timeline =
   longest listing delivery lead time + area-based setup days (at least one).
   Shipping, taxes and structural works are excluded. New room categories require
   explicit locally researched rates; missing rates produce a clear rejection.
6. Save output, quote and SKU mapping to the project. Inventory can change during
   rendering; orders/replacements revalidate and sellers confirm availability.
7. Product requests group items by seller. Confirmation reserves stock; cancellation
   restores reserved stock. Dispatch/delivery states are tracked. No live carrier,
   automated merchant payout or collected order payment is implied.
8. Consultation/professional request records a brief and contact consent. A
   professional/operator can respond, quote, schedule and update work status.
   No live Calendly/calendar integration or paid-call collection is configured.

## AI incorporation: three distinct paths

### A. Local photographic layout

Pillow composites actual cutouts locally. No external model/key is needed. It is
approximate concept staging; it does not clean the room or infer camera geometry.
Automatic matting is an optional installation, disabled in the lightweight Mac
preview unless supported dependencies/model are installed.

### B. Reference-guided generation

Gemini is the preferred configured provider; OpenAI is optional. The server sends
the room, selected original product references and structured SKU/style/dimension
information to the chosen provider. Returned images are validated and stored.
This can change or omit a product; identity remains explicitly unverified. Optional
vision grounding suggests hotspots but is not product-identity proof. BRIA, FLUX,
Photoroom and other providers were researched, not integrated or quality-benchmarked.

### C. Measured, product-protected beta

See `PROTECTED_PLACEMENT.md` for exact contracts and limitations.

1. Customer supplies a measured floor rectangle and compatible photographed views.
   A photo alone cannot provide absolute size. No automatic depth/vanishing-point
   inference is claimed by this implementation.
2. API validates ownership, inventory/budget, geometry and available photos.
3. An operator-configured grounded detector + segmentation service supplies boxes,
   confidence and a removal mask. SAM 2 requires such detector/point/box prompts.
   The service adapter is implemented; the GPU/model service itself is not deployed.
4. The image provider fills masked furniture-removal holes. All other room pixels
   are restored locally. Uncertain/oversized/inconsistent masks are rejected.
5. A measured-floor homography maps positions. Solid products are uniformly scaled
   cutouts; rugs can be floor-warped from top-down photos. Unseen views are rejected.
6. Local shadows, depth ordering and optional retained-foreground masks compose
   the scene. Layout/visibility checks reject clearly incompatible placements.
7. Gemini/OpenAI harmonizes only contact/shadow surroundings. The server discards
   other changes and restores every product pixel from the transformed composite.
   No unsupported `denoising_strength=0.18` promise is made.
8. A lossless PNG, exact overlay/SKU boxes, private originals and private cleanup
   cache are saved. Protected replacement reuses that project's clean room and
   recomposites the actual replacement. Existing versions remain saved.

There is no required staff approval queue for room outputs. Failures return an
explanation or request better inputs, without automatic paid retries. Product
pixel locking is tested; physical fit, photorealism, inferred cleanup surfaces and
angle compatibility are not certified. Complete automatic room layout, automatic
foreground/depth estimation and high-quality cinematic generation remain future work.

Provider keys remain server-side and require API accounts/billing; a consumer
ChatGPT Plus subscription does not automatically fund the app's API calls. Users
sign into Roomform; provider account passwords are not used as app API credentials.

## Monetization

- One-time $3/3-image and $5/6-image package definitions and payment/credit records
  exist; package sales remain disabled. Provider costs and paid-generation credit
  consumption/entitlements need final integration before activation.
- Business seat logic: Basic one named user, Ultra three, Enterprise custom.
  Activation/renewal is operator-managed; recurring billing/prices are not finalized.
  Named-user seats are not a certified concurrent-device enforcement system.
- Optional commission ledger tracks configured amounts; it does not collect or
  distribute money automatically.
- Bank-reference submission/reconciliation exists. Optional Stripe hosted checkout
  and signed idempotent webhook code exists. No live payment collection is verified.
  Google Pay depends on a supported merchant account/device; “all banks”, Easypaisa,
  JazzCash and other local payment integrations are not currently connected.

The beta quota guard is not the paid package ledger. A fresh measured workflow
reserves three daily attempt slots atomically; cached reuse/replacement reserves
one. Failed/unused reservations count. With the default three slots/day, this is
one fresh measured workflow/day; limits and paid metering need a commercial design.
Actual provider spending, retries and quality acceptance must inform package prices.

## Security and operations

Implemented protections include scrypt password hashes, hashed session records,
HttpOnly/SameSite cookies, origin checks, scoped project/seller/team access,
named administrator accounts with TOTP, database account/AI limits, upload checks,
private room/generated-image access and signed/idempotent payment webhook handling.
Original room media and protected cleanup caches are not static public catalog
assets. Product catalog images are public under the listing workflow. These checks
are not a penetration-test or production-security certification.

SMTP/recovery/verification queues exist but need SMTP credentials and a running
mail worker. Docker Compose supplies PostgreSQL/API/Nginx; Caddy staging overlay
supplies HTTPS/basic authentication configuration. It has not been deployed to a
public domain. Production storage, backup/restore, monitoring, retention rules,
security review, payment validation and load testing remain required.

Rendering is currently synchronous, with bounded service timeouts and an extended
proxy timeout. Durable queued jobs, cancellation/recovery and comprehensive billing
reconciliation are needed before high-volume paid traffic. No uptime, throughput,
conversion rate or image-fidelity percentage has been measured for a live business.

## Recommended next milestone

1. Standardize the local/backend runtime (Python 3.12, Node 24) and private staging
   with PostgreSQL, persistent private media, HTTPS and tested backups.
2. Bind Gemini API access/billing and deploy/connect the grounded segmentation
   service through secure settings. Never paste keys into chat or frontend code.
3. Onboard genuine sellers and professionals; verify stock, delivery and local labor
   rates for a focused city pilot. Add SMTP for actual account communications.
4. Benchmark a small, repeatable set of real room/product pairs, views, measurements,
   masks and swaps. Measure product preservation, geometric plausibility, failure
   rate, latency and total provider cost. Do not invent an accuracy percentage.
5. Fix quality failures, complete paid credit accounting and select an approved
   payment provider. Test buyer → seller → professional and payment/refund paths.
6. Expand categories/automation and add cinematic video only after the core room →
   real-product → consultation/order experience is reliable and commercially viable.
