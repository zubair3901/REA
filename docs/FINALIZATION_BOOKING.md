# Finalization bookings

A customer can explore design versions using their available image allowance, then select one saved design for finalization. Booking and document downloads do not require another image generation. Credits and image allowance enforcement remain separate from this booking feature.

The booking captures a fixed design version and item codes, current item prices/stock, project budget, labor estimate, configured finalization fee, seller preparation/delivery ranges, and installation allowance. Subsequent catalog changes do not rewrite an existing snapshot. A booking is a request for finalization with draft agreement terms, not a paid order, inventory reservation or guaranteed appointment confirmation.

Configure FINALIZATION_SERVICE_FEES_JSON with your actual flat fee by currency, for example `{"USD":25,"PKR":5000}`. Configure FINALIZATION_EMAIL with the operational inbox, and SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD and SMTP_FROM for mail. Run `python -m app.mail_worker` regularly. Never place actual credentials in source control. Without recipient/mail configuration the app must not claim email was delivered.

Sellers provide preparation and delivery minimum/maximum calendar days per product. The slowest item's preparation plus delivery forms the procurement range; installation allowance is added for the estimated whole project. Timelines start after stock, scope and order confirmation, not immediately on appointment submission. Supplier capacity, local delivery coverage and professional scheduling still need confirmation. Taxes, shipping charges and structural work stay excluded unless explicitly costed; the PDF must show these exclusions.

Use additive migration `python -m app.migrate` before starting an existing deployment. Back up the database first. PDFs and customer contacts are private operational records and must not be served from public static storage.

Validation should cover item codes, Decimal totals, missing fee/timing configuration, stock changes, authorization, immutable snapshots, duplicate submit protection, PDF responses and email attachment generation. Live SMTP delivery needs configured credentials and a real inbox test.

API: seller GET/PUT `/api/assets/{asset_id}/fulfillment`; customer POST `/api/workspace/projects/{project_id}/finalizations/preview`, POST/GET `/api/workspace/projects/{project_id}/finalizations`, and authorized GET `/api/workspace/finalizations/{booking_id}/pdf`. Booking uses a customer-scoped idempotency key; reused keys with changed inputs are rejected. Missing stock, timing or fee configuration blocks finalization. Downloading or booking does not consume AI credits.

Email statuses: `not_configured` means no FINALIZATION_EMAIL recipient; `pending` means durably queued, including when SMTP is not yet configured; `sent` means the SMTP server accepted the message, not proof of inbox receipt; `failed` means retries were exhausted. The mail worker requires SMTP_HOST and SMTP_FROM.
