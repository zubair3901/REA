# Product and implementation review

## Product definition

A budget-first, real-inventory interior design marketplace. A client confirms a room photo, room area/type, style, investment ceiling, currency, location and new/pre-loved/either preference. The system proposes available products, then an image model reimagines the room using those references. The client reviews the itemized estimate and connects to merchants, secondhand sellers and consultation/build teams.

A proposed premium subscription is USD 25/month. No money is currently collected, no premium entitlement is granted, and no walkthrough is generated. Premium direction is now confirmed: cinematic AI video, not an interactive 3D tour. Its provider, payment and credit enforcement remain to be implemented.

## Implemented in this change

- POST /api/plans: confirmed budget, currency, condition and optional delivery coordinates; eligible products must be active, in stock, from active sellers and in delivery radius if coordinates supplied.
- Budget matching reserves estimated labor within the ceiling, picks a diverse set of available product categories, prefers matching catalog style, and reports missing core categories. This is deterministic catalog matching, not an LLM selecting arbitrary prices.
- Plans expire in 30 minutes. Generation rechecks stock, active seller/listing, price ceiling, condition and delivery radius. Nothing is reserved or purchased.
- Manual selections can also carry a confirmed budget/currency/condition ceiling; backend rejects overspending.
- UI supports “choose products for me,” budget confirmation and new/pre-loved/either before creating a room.
- Broader seller categories include bed, desk, rug, storage, art and textiles.
- Seller logout now revokes the server session instead of only clearing UI state.
- Previously generated test listings were backed up and hidden, not deleted. Tests now use a disposable database initialized before application imports.
- Proposed premium price is shown explicitly as planned/unavailable, avoiding false checkout claims.

## Review findings in priority order

| Priority | Finding and evidence | Required change |
|---|---|---|
| P0 | main.py exposes /media through StaticFiles, and /api/designs and /api/leads have no customer ownership authentication | Customer accounts, private object storage, signed image URLs, owner-scoped designs/leads, retention/deletion |
| P0 | generation.py calls paid providers without a verified subscription or usage debit | Server-side entitlements, credit ledger, per-account limits, request idempotency and spending cap before public AI access |
| P0 | No payment integration, subscription tables or verified payment webhooks exist | Stripe/Paddle checkout; signed idempotent webhook processing; cancellation, refund and failed-payment handling; server-enforced entitlement |
| P0 | Still-image providers cannot prove SKU identity or recover true room geometry | Real-photo quality benchmark, product identity/omission review, customer confirmation, room measurements/multiple views where needed |
| P1 | Synchronous provider requests can last 180 seconds | Durable render/video queue, status polling, cancellation and retry policy that avoids duplicate paid jobs |
| P1 | Stock is checked but not reserved and quote quantity is one per selected SKU | Quantities, reservations/expiry, orders, seller confirmation, availability timestamps |
| P1 | quotes.py defaults to USD labor only; shipping/tax/structural work excluded | Operator-reviewed local labor tables, currency conversion policy, delivery charges and clear scope |
| P1 | Seller registration has password hashing but no email verification, recovery, throttling or review dashboard | Verification/reset flows, login/signup limits, operator moderation and suspension UI |
| P1 | Customer project gallery is memory-only | Persistent project ownership, version history, favorites, downloads and share links with permissions |
| P1 | worker.py retries webhook events but has no operations UI | Scheduled worker deployment, delivery monitoring, retry/dead-letter console and integration tests with real destination |
| P1 | Native APK was statically inspected, not run; current interface is independent | Treat homepage reference as design inspiration; do not claim exact original-app fidelity |
| P2 | Supplier listings are single-image and category/style are loosely typed | Multiple angles, material/color tags, lead time, delivery fee, assembly, warranty and condition grading |
| P2 | Supplier inventory is manual | Bulk CSV import, external stock sync, low-stock notifications and listing analytics |
| P2 | Automatic selection currently chooses one candidate per broad category | Alternative proposal sets, quantities, compatibility ranking and customer keep/remove/replace controls |

## Premium at USD 25/month

Use a metered plan, not unlimited expensive inference. Determine included image credits and walkthrough credits from measured provider costs, target margin, payment fees, storage, video rendering and support. Show credits before generation and require explicit confirmation for paid overages.

The backend, not a frontend flag or checkout success URL, must decide premium access. A signed payment webhook grants entitlements; renewal failure/cancellation updates them. Each render reserves usage credit transactionally; success finalizes it and failure releases it according to policy.

Cinematic AI video is the practical first candidate: generate from the approved final room using a licensed image-to-video model, disclose geometry hallucination and offer an MP4 preview. Interactive 3D requires reconstruction/scene assets, calibrated dimensions and navigation; one generated room image is insufficient to establish a true measured 3D scene. Do not label a pan/zoom slideshow as an immersive walkthrough.

## Recommended product improvements

1. “Keep this” masks and room constraints: preserve doors/windows and existing furniture the customer likes.
2. Buyable alternatives: replace one expensive/unavailable SKU while preserving style and ceiling.
3. Multi-angle seller photography and structured materials/colors for better reference fidelity.
4. Supplier availability and dimension confirmation before customer payment.
5. Consultation handoff packet: approved image, selected SKUs, dimensions, exclusions and project notes.
6. Sustainable sourcing options, used-item condition verification and pickup versus delivery.
7. Supplier performance metrics and clearly disclosed sponsored placement.
8. Designer/builder verification, quotations and milestone tracking after consultation.
9. Side-by-side budget tiers (refresh, balanced, premium) within explicitly selected spending ceilings.

## Validation and limits

Twelve backend tests pass, including plan confirmation, budget constraints, used-only selection, current-price rechecks and rendering without manually selected product IDs. Real browser flow passed from budget confirmation through automatic selection, local composite, comparison, quote and lead submission, with no JavaScript errors or mobile horizontal overflow. Existing model adapter tests simulate provider transport.

Live hosted AI, premium payment, video/3D generation, PostgreSQL deployment and production load remain unverified. Current local/demo rendering must not be described as live premium inference.
