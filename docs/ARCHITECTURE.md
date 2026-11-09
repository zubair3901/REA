# Separation of concerns

This refactor changes module ownership, not product behavior. URLs, API contracts, storage formats, authorization, environment settings and CSS class names remain stable. Existing domain modules continue to own their feature; not every small function requires a service class.

## Frontend

- `src/main.jsx`: React bootstrap and top-level providers only.
- `src/app/App.jsx`: application orchestration, shared design/session state, navigation and action wiring.
- `src/app/routing.js`: route names and query-string route interpretation.
- `src/app/AppHeader.jsx`, `AppFooter.jsx`: application chrome.
- `src/pages/HomePage.jsx`, `MarketplacePage.jsx`, `StudioPage.jsx`: page presentation with explicit inputs and event callbacks. Studio state/action orchestration stays above presentation.
- `src/features/seller/`: seller authentication, inventory rows, catalog attributes, location, listing forms, photos and editor focus lifecycle. `SellerPortal.jsx` composes these and owns seller session/actions.
- `src/features/workspace/WorkspaceContext.jsx`: buyer identity, project selection and shared workspace state.
- `src/features/workspace/`: account gate, project dashboard, consultation, packages, checkout, email verification and notice presentation.
- `src/lib/http.js`: shared JSON transport; endpoint selection belongs in feature modules.
- `src/lib/format.js`: pure formatting helpers.
- `src/app/api.js`: legacy application request adapter supporting FormData and its existing error behavior. Its contract deliberately differs from the shared JSON adapter.
- `Workspace.jsx` and `workspace-api.js`: compatibility facades. Keep existing consumer imports working; new modules may import focused implementations directly.

Existing independent product gallery, photography, result rendering, finalization and operations components remain feature modules. Styles and licensed public assets stay separate from application logic. CSS cascade order is intentionally preserved; this refactor does not change the visual theme.

## Backend

- `app/main.py`: `create_app()`, ASGI instance, lifecycle, middleware and router composition.
- `app/*_routes.py`: HTTP endpoints for catalog, designs, media, photos, leads, product models, seller orders and system capabilities.
- `app/schemas.py`: extracted request validation models.
- `app/dependencies.py`: shared seller authorization dependency.
- `app/storage.py`: media directory configuration.
- Existing `planning`, `generation`, `protected_placement`, `rendering`, `quotes`, `photography`: feature/domain processing, separate from application composition.
- `app/services/finalization_pdf.py`: print layout from a saved snapshot. Booking authorization, persistence and delivery queue stay in `finalization.py`; SMTP delivery stays in `mail_worker.py`.
- `models.py`, `workspace_models.py`, `database.py`: persistence definitions and sessions.

Feature modules must not import the ASGI composition root to obtain authorization or storage paths. `main.MEDIA` is retained only as an existing compatibility export. Imports flow from composition into features, then shared dependencies/services and persistence, rather than back into composition.

## Where to change a feature

| Change | Owner |
|---|---|
| Seller stock/form presentation | `features/seller/` |
| Seller listing validation/API | `schemas.py`, `catalog_routes.py` |
| Product photo preparation | `photo_routes.py`, `photography.py` |
| Buyer project state | `features/workspace/WorkspaceContext.jsx` |
| Studio layout | `pages/StudioPage.jsx` |
| Room generation orchestration | `design_routes.py` and generation services |
| Booking workflow | `finalization.py`, `FinalizationBooking.jsx` |
| PDF appearance | `services/finalization_pdf.py` |
| Security policy | `security.py`, relevant authentication dependencies |

## Verification

Backend: `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -q`.
Frontend: `npm --prefix frontend run build`.
Browser regressions with Vite on localhost5173: `check:webapp`, `check:curated`, `check:vendor`, `check:finalization`, `check:protected` as applicable. Mock-contract browser tests do not exercise live AI, email, payments or production PostgreSQL.

Keep feature API shapes and CSS class contracts stable during structural refactors. For new behavior, add tests at the domain or user-workflow boundary rather than asserting source-file layout. No database migration is required for this module-only change.

Refactor verification:52backendtests passed; frontend production build passed; webapp navigation, curated collection, vendor100listing edit workflow and finalization mock-contract browser checks passed. Authenticated studio render was also smoke-tested with a mocked account/provider configuration. No live AI inference, payments or email delivery was asserted by these checks.
