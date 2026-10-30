# Private staging handoff

## Implemented in this security pass

Named administrator accounts with required TOTP, replay protection, 30-minute HttpOnly sessions and logout; legacy operator keys disabled by default. Run `python -m app.create_admin` interactively on a trusted server after migration; never publish the authenticator URI.

Email verification with hashed, expiring tokens, single-use confirmation and a resend cooldown. Secure staging blocks customer changes before verification. Configure SMTP and schedule `python -m app.mail_worker` to deliver queued mail. Verification is exposed in My projects. Seller accounts have a separate email verification flow in their order panel; both verification and operator approval are required on secure staging.

Existing team project access now rejects expired subscriptions. Account throttling uses atomic database counters shared by workers. The private deployment does not expose the API directly; its trusted proxy forwards client IPs. Runtime dependency updates remove the known Python advisories found during this pass. npm audit also returned zero findings at scan time. Scans are not independent penetration tests.

## Payments

Optional Stripe hosted card checkout adapter and signed webhook handling are implemented, including amount/currency validation, timestamp tolerance, event deduplication and one-time credit granting. Browser return URLs never grant credits. Staging rejects live Stripe keys/events. Google Pay is conditional on provider eligibility, merchant configuration, browser/device and domain requirements; it is not independently activated by a button. No raw card numbers pass through Roomform.

Bank transfer references can be submitted for independent operator verification. This is not an integration with every bank. Pakistan local wallet/bank APIs require a selected approved local merchant provider; none is currently configured. No live transactions were made. Project AI package sales remain disabled until AI fulfillment exists.

## Required deployment inputs

Supply the hosting target and domain, business country/legal entity, approved merchant provider(s), SMTP provider, and staging reviewer access policy. Store credentials in hosting secret settings; do not send secret values in chat. Business location determines which card, Google Pay, bank and wallet services can actually be offered.

Use the production Compose stack with `docker compose -f compose.yaml -f compose.staging.yaml up --build -d`. Set APP_URL/CORS_ORIGINS to the HTTPS staging origin and COOKIE_SECURE=true. Set STAGING_DOMAIN, STAGING_USER and a Caddy-generated STAGING_PASSWORD_HASH. Both frontend and API remain behind HTTPS basic authentication; only the signed Stripe webhook bypasses browser authentication. Caddy needs domain DNS pointing to the host and ports 80/443 reachable to obtain a public certificate.

Back up database and media volumes, migrate before serving traffic, provision a named admin, run the SMTP worker, and verify backup restoration. No public/private hosted staging URL has been created because a domain and hosting account have not been supplied.

## Still required before claiming all gaps closed

Actual HTTPS deployment and proxy/throttle verification, SMTP delivery, independent security assessment, operational retention/deletion procedures, backup restoration, approved local provider integration and live-provider sandbox acceptance tests. The current automated checks cover application workflows and security controls; they cannot certify third-party services that are not configured.

## Final validation

25 automated tests passed against disposable PostgreSQL 16, covering customer/seller verification, admin TOTP replay rejection, expired-team access denial, buyer orders and inventory restoration, professional quotes, and signed payment webhook idempotency. Production frontend build and staging Compose configuration validation passed. Python and npm advisory scans reported no known findings at scan time. No externally hosted staging, live mail or merchant sandbox checkout has been verified.
