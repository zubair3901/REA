# Superseding security update

See [staging handoff](STAGING_HANDOFF.md) for the latest hardening, dependency audit evidence, PostgreSQL verification and remaining deployment/service requirements. The historical review below predates these changes.

# Security review — 2026-10-26

Code review and 20 automated backend tests passed. This is not an independent penetration test or production security certification.

Implemented: salted scrypt password hashing, constant-time password comparison, hashed expiring session tokens, HttpOnly/SameSite customer cookies, configurable Secure flag, logout revocation, private project/image authorization, removed-member access denial, server-side seat enforcement, origin checks on browser mutations, image decoding/re-encoding and size limits, per-process account throttling, operator-only approvals, atomic payment credit reconciliation, conditional stock reservation, and audit records for sensitive decisions. Password reset code uses expiring single-use tokens and revokes sessions; real SMTP delivery has not been verified.

Before public launch:

- Replace shared operator-key access with named administrator roles and MFA.
- Enforce expired team subscriptions consistently on existing project mutations; current expiry checks cover project creation and member addition but not every existing-project action.
- Add email verification and production abuse controls; validate proxy IP/rate-limit behavior across workers.
- Enforce HTTPS and Secure cookies in deployment. Local defaults intentionally support HTTP.
- Test PostgreSQL concurrent writes, backup restoration, container configuration and migration on staging.
- Audit dependency advisories and arrange an independent security test.
- Complete privacy/retention/deletion policy and restrict production operator access.
- Integrate verified payment-provider events before offering automated card checkout or recurring billing.

No live payment, email, public-hosting, AI or video security assessment has been performed. Public catalog photos are intentionally public; saved project output is access-controlled. Original uploaded room photos are not persistently stored by the local preview workflow.
