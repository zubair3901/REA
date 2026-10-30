Latest product workflow: [real seller photography](PHOTOGRAPHY_RELEASE.md). This supersedes earlier illustration/3D and single-photo setup notes below.

# Roomform marketplace release

The current scope replaces the earlier consumer $25/month proposal. Consumers buy $3 / 3-image or $5 / 6-image project packages when AI launches. Business workspaces support Basic (one named user), Ultra (three), and Enterprise (custom seats). Business prices and image allowances require a commercial decision.

## Working application

- Customer registration, HttpOnly session cookies, logout and persistent private projects.
- Project status, budget, new/pre-loved preference and saved local product previews.
- Seller and individual resale onboarding, operator approval, transparent image uploads, bulk listings, prices, stock and delivery coverage.
- Order requests grouped by seller, stock reserved on confirmation, dispatch/delivery tracking and cancellation restoring reserved stock.
- Skilled professional applications and approval, public directory, private inquiries, quotes, customer acceptance and work status.
- Consultation requests from saved projects, operator response and scheduling status.
- Team registration, operator activation/renewal, named seats, adding/removing registered colleagues and shared projects.
- Project payment references, operator reconciliation, one-time credit granting and audit history. Package sales are disabled until AI delivery is ready.
- Password recovery tokens and a queued SMTP mail worker. SMTP must be configured to deliver mail.

Orders currently arrange payment, shipping and taxes directly with sellers. Consultation status records an agreed appointment; it does not integrate a calendar. Business renewals are operator-managed, not automatic recurring card billing. Local previews are approximate composites, not AI renders. PNG reference illustrations are not real merchant inventory.

## Local development

Use Python 3.12+ and Node 24. From the repository root:

```sh
python -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
PYTHONPATH=backend .venv/bin/python -m app.migrate
PYTHONPATH=backend .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

In another terminal, run `npm ci` then `npm run dev` in `frontend`. Vite proxies API and images to the backend on the same origin. Environment settings must be loaded by the shell/process manager; copying `.env.example` alone does not load it into Python.

Set `ROOM_OPERATOR_KEY` to a unique secret before starting the API to enable Operations. Do not use a VITE variable for secrets. The illustrative seed is optional: `PYTHONPATH=backend .venv/bin/python -m app.seed`.

## Deployment

The supplied Compose stack runs PostgreSQL, the API, and a compiled frontend behind Nginx. Configure `POSTGRES_PASSWORD`, `ROOM_OPERATOR_KEY`, `APP_URL`, and `CORS_ORIGINS` in a private `.env` file. For public hosting, terminate HTTPS at your hosting proxy, set `COOKIE_SECURE=true`, and use your HTTPS origin for APP_URL/CORS_ORIGINS. Run `docker compose up --build -d`. The web port defaults to 8080. Do not expose PostgreSQL or the API directly. Back up both the database and media volume before migrations and regularly afterward.

Configure `LABOR_RATES_JSON` with locally researched currency/room rates; included USD values are estimates, not Pakistan market quotes. Configure SMTP_HOST/PORT/USER/PASSWORD/FROM and run `docker compose exec api python -m app.mail_worker` periodically for account recovery. Keep ENABLE_AI_GENERATION and ENABLE_PROJECT_SALES false for this release.

## Required owner decisions/services

1. Hosting account and domain for public deployment.
2. Merchant payment provider / bank transfer method, settlement currency and exchange-rate rules. No live card gateway is connected.
3. Business tier prices, image allowances and commercial terms.
4. SMTP credentials and actual consultation operators.
5. Real sellers, professionals, inventory and local labor rates.
6. Privacy/terms/refund policies for the operating business before public launch.

## Verification boundaries

20 backend tests passed, including project privacy, seat enforcement, removed-member access, payment idempotence, quote lifecycle and inventory cancellation. React production build passed. Browser navigation and responsive layout checks are separate from backend lifecycle tests. Live card payment, SMTP delivery, PostgreSQL containers, public hosting and AI/video have not been verified in this environment.
