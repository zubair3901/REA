The [interface redesign](docs/ATELIER_REDESIGN.md) and [current screenshot gallery](docs/ui-review/index.html) show the latest desktop and mobile experience.

The [product-fidelity and API handoff](docs/PRODUCT_FIDELITY_HANDOFF.md) records the latest voice decisions, provider links, automation requirements and next evaluation.

The [real seller photography release](docs/PHOTOGRAPHY_RELEASE.md) and [current UI gallery](docs/ui-review/index.html) supersede the earlier synthetic product workflow.

See the [interactive release](docs/INTERACTIVE_RELEASE.md) and [updated UI gallery](docs/ui-review/index.html) for the latest landing demos, seller 3D builder and verification.

# Current release

See [launch guide](docs/LAUNCH.md) for the current project-based business model, working workflows, deployment and remaining external configuration. This guide supersedes older pricing and session-only project notes below.

# Roomform · real products, real possibilities

A modular React + FastAPI interior marketplace prototype with transparent product compositing, server-priced budgets and consultation lead capture. Built independently from the requested Home AI concept. **Not a verified clone or production-complete service.**

## Run locally

Requires Python 3.12+ and Node 22+. This prepared cloud environment already has both.

Terminal 1, from the repository root:

```bash
python -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
export PYTHONPATH=backend
.venv/bin/python -m app.seed
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Terminal 2:

```bash
cd frontend
npm ci
npm run dev
```

Seed is opt-in/idempotent and creates four **illustrative, non-saleable** products located in Karachi, priced in USD. Upload a non-sensitive room photo, select products, render, review the budget, then submit a consented consultation request. No model download or credential is required for this concept renderer. Room category and size drive the estimate. Timeline = longest delivery + area-based installation days. Quotes do not reserve stock.

## Merchant portal

Operator creates an approved seller row in `sellers`, then configures `MERCHANT_KEYS_JSON` as a map of seller IDs to distinct random API keys before starting the API. Example for a local demo only:

```bash
export MERCHANT_KEYS_JSON='{"demo":"your-generated-long-random-key"}'
```

Use the Partner tab with that seller ID/key. Upload transparent PNG/WebP photography, dimensions (cm), price/currency, coordinates, delivery days and stock. Only the owning seller can publish the uploaded image. Currency labor rates must be explicitly configured via `LABOR_RATES_JSON`; USD is the only default. Products of mixed currencies cannot share one quote.

## Layers

- `frontend/`: React/Vite studio, budget, merchant portal and consented CTA.
- `backend/app/main.py`: validated HTTP API and scoped merchant authorization.
- `backend/app/models.py`, `migrations/001_initial.sql`: relational seller/catalog/design/lead/outbox schema.
- `backend/app/rendering.py`: fixed-SKU compositor; exact product pixels, approximate geometry/shadows.
- `backend/ai/render_inpaint.py`: optional GPU Diffusers background-only inpainting CLI, then fixed-SKU overlay. Not installed/executed here. Requires caller wall mask, licensed `MODEL_ID`, model dependencies and GPU. It does not infer depth or produce exact perspective.
- `backend/app/quotes.py`: decimal pricing and disclosed labor/timeline assumptions.
- `backend/app/worker.py`: transactionally queued webhook lead delivery.
- `docs/REVERSE_ENGINEERING.md`: observed facts, APK/JADX blockers and extraction procedure.
- `docs/PRODUCTION.md`: concrete deployment and production gaps.

## Verification

```bash
.venv/bin/python -m pytest -q
cd frontend && npm run build
```

Tests exercise real image rendering, quote totals, lead/outbox persistence, merchant ownership, stock conflicts and invalid uploads. Frontend compiled with Vite. No mobile APK, paid booking, live vendor inventory, GPU model or original app endpoint has been validated.

## Hosting

Frontend: Vercel/StackBlitz/IDX, root `frontend`, build `npm run build`, output `dist`. Set `VITE_API_URL` at build time to the backend's HTTPS origin. Static frontend alone cannot run the Python backend.

Backend: persistent Python/container host with PostgreSQL and persistent media storage. Copy `.env.example` into your process manager's secure configuration; it is not loaded automatically. Apply `migrations/001_initial.sql` once with `psql`; set `AUTO_CREATE_SCHEMA=false`. Local SQLite auto-creation is for development only.

For Docker: set `POSTGRES_PASSWORD`, `docker compose up -d db`, apply the migration with `docker compose exec -T db psql -U orbit -d orbit < migrations/001_initial.sql`, then `docker compose up --build -d api`. Seed only for demos: `docker compose exec api python -m app.seed`. The Docker/PostgreSQL lane is provided, not verified in this environment.

Set `CONSULTATION_URL` to your paid Calendly event URL. To automate lead routing, configure HTTPS `LEAD_WEBHOOK_URL` and `LEAD_WEBHOOK_TOKEN`, then schedule `PYTHONPATH=backend .venv/bin/python -m app.worker`. Receiver must deduplicate event IDs. No payment is collected by this app.

Before public launch follow [production requirements](docs/PRODUCTION.md), particularly customer identity, private image storage, quotas, verified payments and retention. Current media URLs are public; use non-sensitive demonstration images only.

## Multi-model reference-guided AI generation

The studio now offers local product compositing, OpenAI GPT Image editing, and Gemini image generation. Each AI request contains the actual room, every selected product image, SKU names and dimensions, and the chosen style/room type. The model receives explicit architectural-preservation, product-identity, scale, lighting and shadow instructions. Keys stay on the server; the user must consent to sending room/product photos to the selected provider.

Configure one or both providers using the variables in .env.example and restart FastAPI. An availability flag means a key is configured, not that billing, model permission, or inference has been verified. Provider failures never silently fall back to a fake AI image. Each action performs one provider request without paid automatic retries. Generated images are re-decoded/validated and stored; returned quote manifests disclose that SKU identity is unverified. AI may alter or omit a referenced item, so selected inventory is not represented as detected image contents.

API: GET /api/models; POST /api/designs adds model=composite|openai|gemini and ai_consent=true for external models. Response mode is ai_reference for generative results. Two provider transport tests verify actual request shapes and result persistence using simulated provider responses; no paid inference has been executed because no image-provider credentials are configured. Six backend tests pass overall.

Official API references used: https://platform.openai.com/docs/api-reference/images/createEdit and https://ai.google.dev/gemini-api/docs/image-generation . Default model IDs can be overridden server-side for models supported by each editing API.

The interface remains Roomform's independent reconstruction, not a verified pixel-identical reproduction of Home AI. The original APK was inspected but has not been run in an emulator. Public-launch requirements in docs/PRODUCTION.md still apply, including authenticated generation, spending caps, private media storage and async jobs.

## Seller accounts and secondhand listings

Self-service registration/login is available in the partner portal for merchants and individuals. Passwords are salted scrypt hashes; sessions are hashed in the database, expire after 24 hours, and can be revoked by logout. New sellers are pending review and cannot publish until approved.

For an existing database, back it up and run:

```bash
PYTHONPATH=backend .venv/bin/python -m app.migrate
```

Migration is additive and repeatable, adding seller accounts/sessions and product condition/delivery columns without deleting existing data. Fresh installations create the updated schema automatically in local mode. Operator approval:

```bash
PYTHONPATH=backend .venv/bin/python -m app.approve_seller SELLER_ID
```

Use --disable to suspend listings through seller status. Operator approval has no public HTTP endpoint. Approved sellers can upload product photography, create new or secondhand listings with condition, delivery area/radius, and manage price/stock/visibility/delivery lead times. Credentials are held only in UI memory. Registration does not yet verify email ownership; email verification, account recovery, login throttling and moderation tooling remain required before an open public marketplace.

A live provider check (one billable request, no automatic retries) is available after a key reaches the backend process:

```bash
PYTHONPATH=backend .venv/bin/python -m app.smoke_ai --provider gemini --room /absolute/path/room.jpg --asset-id sofa --asset-id lamp
```

Use real merchant photos for meaningful quality evaluation; demo catalog art is deliberately illustrative. Review exact product fidelity and room geometry before showing any generation as a purchasable design.

## Frontend redesign

The new experience separates Discover, AI Design Studio, session projects, real furniture, seller onboarding and consultations. The photo-led homepage uses an original ivory/emerald design inspired by the reference site's navigation and editorial layout. It does not copy the reference site's branding or images.

Inspiration cards apply a room category, style and editable design brief. The studio sends design_brief (up to 1,200 characters) to the selected generative provider along with room/product references. The local compositor does not interpret the brief. Before/after comparison uses the original photo and actual returned result. The gallery is explicitly session-only; download images before refreshing. Marketplace supports name search, new/pre-loved filtering and opt-in 50 km location filtering.

Verified after redesign: inspiration → prefilled brief → upload → product selection → real local composite → before/after slider → itemized budget → consented consultation lead → session project reopening. Desktop and 390 px mobile browser checks passed without horizontal overflow or JavaScript errors. Eight backend tests and the Vite production build passed. Live external AI inference still requires provider keys in the backend runtime.

Photography: images downloaded from Unsplash into frontend/public/images; source IDs and URLs are recorded in frontend/public/images/CREDITS.md. Images are illustrative inspiration, not outputs generated for the current user or merchant inventory.

## Budget-first automatic furnishing

AI Design Studio now includes investment confirmation and new/pre-loved/either filters before rendering. “Choose products for me” requests a budget-constrained catalog proposal via POST /api/plans, including estimated labor. The backend picks eligible in-stock references; the selected image model handles visual reimagination. Missing categories are shown rather than fabricating vendor inventory.

Plans last 30 minutes and do not reserve stock. Every generation rechecks current eligibility/prices and must stay within the confirmed item-and-labor ceiling; taxes/shipping/structural work remain excluded. Optional delivery matching uses supplier radius and browser-provided coordinates. Local labor must be configured for the requested currency.

Existing databases: run PYTHONPATH=backend .venv/bin/python -m app.migrate to create design_plans. Fresh PostgreSQL schema is in migrations/001_initial.sql.

The proposed USD 25/month premium tier is explicitly marked planned/unavailable: subscription payment and true walkthrough generation are not implemented. See docs/PROJECT_REVIEW.md for the prioritized code/product review, premium architecture, cost controls and next features.

## Core release expansion

See docs/CORE_RELEASE.md for the current agreed scope. Premium is cinematic AI video; 3D navigation is excluded from the initial premium pipeline.

The separate PNG asset library contains 140 CC0 reference designs / 560 transparent images, searchable with four viewing angles and downloads. These are digital illustrations, not merchant inventory. No fabricated prices or stock are assigned. Supplier photographs remain necessary for photorealistic product identity.

Sell with us now supports JSON + photo batch onboarding (up to 100 rows), in addition to individual listings. Download supplier-manifest.example.json in the portal. Uploaded images must belong to the authenticated seller; bulk listing validation is atomic.

Operations provides supplier approval/suspension and a consultation inbox. Configure ROOM_OPERATOR_KEY securely on the backend and restart. Without configuration, access is denied. Operator keys are kept in component memory and are not persisted by the browser. Never expose this secret as VITE_.

Provider, payments and storage limitations remain documented in docs/PRODUCTION.md. Confirming consultation_booked in Operations is only recordkeeping; it does not create a calendar booking or collect payment.
