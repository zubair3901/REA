# Deployment boundary

This is a running vertical slice, not a completed production launch.

Implemented: scoped merchant API keys, approved seller ownership, bounded raster uploads, fixed SKU compositing, server-priced quote snapshots, geographic catalog filtering, consented lead persistence and transactional webhook outbox. No customer-supplied price is trusted. Quote snapshots are estimates; no inventory reservation, payment, order, tax or delivery purchase occurs. Outbox receiver must deduplicate `Idempotency-Key`. Schedule `python -m app.worker` with HTTPS webhook credentials. Failed deliveries retry up to ten scheduled runs; monitor undelivered rows. No leads are sent unless the worker is configured and run.

The default renderer places exact product pixels with approximate scale and soft shadows. It does NOT infer depth or perspective, recolor walls, or run Stable Diffusion/ControlNet. Style is recorded, not used to hallucinate replacement furniture. Integrating a model requires a GPU/inference endpoint, consent for sending room images, segmentation/depth estimation, and a background-only mask that excludes product pixels. Keep the SKU placement manifest authoritative and verify outputs against it; generative models do not guarantee SKU identity. No model credentials or photorealism are implied here.

Before public traffic: add customer authentication, private object storage with signed image URLs and owner authorization, deletion/retention controls, edge body limits and per-user quotas/rate limits, malware scanning as appropriate, merchant credential rotation, audit/monitoring, durable async render jobs, backups and tested restore, payment provider checkout with verified webhooks, tax/local pricing configuration, booking availability reconciliation, anti-spam and request deduplication. Current `/media` uses unguessable file URLs but is public and is suitable only for controlled demonstrations with non-sensitive images. Do not use personal room photos in a public deployment until private storage is implemented.

`CONSULTATION_URL` can point to an operator-created paid Calendly event; the app does not create events, query Calendly or collect payment. Without it leads remain pending consultation. Merchant catalog illustrations are explicitly demo data and are not saleable stock.

Vercel can host the static frontend (root `frontend`, build `npm run build`, output `dist`). Set `VITE_API_URL` to your HTTPS backend. Run FastAPI on a persistent container host with PostgreSQL and a media volume; ephemeral sandbox/Vercel filesystems are not durable storage. SQLite is for single-process local development. PostgreSQL migration is provided but Docker/PostgreSQL deployment must be validated on the target host.

## Implemented multi-model adapters (supersedes the earlier compositor-only description)

backend/app/generation.py now integrates OpenAI image edits and Gemini multimodal image generation. These hosted adapters are separate from the optional local Diffusers CLI. Keys: ROOM_OPENAI_API_KEY / ROOM_GEMINI_API_KEY. External generation requires explicit image-sharing consent. Only local compositing was exercised without simulated provider transport; live paid AI quality, SKU fidelity, provider access and billing remain unverified. Provider failures are reported and never replaced with composite output. Quoted SKUs remain requested references, not vision-verified products.

Do not expose a configured paid adapter publicly until customer authentication, spending/usage caps and durable queued jobs are implemented. The current application remains for controlled demonstrations.

## Account implementation update

Merchant/individual signup, salted scrypt password authentication, hashed 24-hour sessions, logout, operator approval and owner-scoped listing management now exist. These supersede the earlier operator-key-only seller workflow. Add email verification/recovery, login/signup rate limits and moderation before public signup. Operator API keys remain available for integrations. There is still no customer authentication/ownership layer for room images, nor a completed payment/order/stock reservation system; avoid a public production-ready claim.
