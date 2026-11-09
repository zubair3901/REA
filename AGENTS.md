# Repository workflow

The owner has authorized committing and pushing completed project changes to
`origin` after appropriate checks. Push future completed changes by default and
report the branch and commit. Never force-push or overwrite remote work.

Keep source code, lockfiles, migrations, documentation and licensed application
assets in Git. Never commit secrets, customer/seller uploads, databases, APKs,
reverse-engineering artifacts, virtual environments or installed dependencies.

Run backend tests for backend changes and the frontend production build for
frontend changes. Describe any unverified integrations honestly.

# Module ownership

See docs/ARCHITECTURE.md before changing a feature. Keep frontend/main.jsx and
backend/app/main.py as composition entrypoints. Put page presentation in
frontend/src/pages, feature state/forms in frontend/src/features, and reusable
transport/format helpers in frontend/src/lib. Backend HTTP handlers belong in
concern-specific routers; shared authorization/storage must not import main.py.
Keep document layout separate from booking persistence and mail delivery.
Preserve compatibility facades until callers are deliberately migrated. Avoid
combining behavior changes with structural refactors, and preserve CSS import
order when moving components.
