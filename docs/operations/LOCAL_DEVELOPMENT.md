# Local Development and Agent Setup

**Status:** Environment contract; actual commands are filled in during P01 after framework decisions and repository inspection. No application stack is assumed here.

## 1. Local development objectives

- Build and test without provisioning paid AWS infrastructure.
- Use reproducible dependency versions and documented setup scripts.
- Provide deterministic fake providers for all normal automated tests.
- Support a local relational database compatible with the approved production schema.
- Keep secrets outside version control.
- Permit an AI agent to reconstruct project state from this directory after context loss.

## 2. Required local services (final selection pending)

Expected local equivalents:
- frontend development server and backend/API process;
- local PostgreSQL or disposable PostgreSQL container after database approval;
- local file/object-storage adapter or S3-compatible development service for integration tests where useful;
- test runner, formatter, linter, type checker and dependency/secret scanner;
- optional local queue/cache/vector capabilities only when selected in architecture.

Do not require real AWS S3/RDS or paid AI credentials to run unit tests. A dedicated optional integration-test profile may use isolated resources after explicit setup.

## 3. Setup document must be completed in P01

After stack selection, record:
1. Supported OS/shell and exact runtime versions.
2. Clone/bootstrap instructions.
3. Dependency install/lockfile policy.
4. Local configuration creation from safe example files.
5. Database start, migrate, seed and reset commands.
6. Start frontend/API/worker commands.
7. Unit/integration/lint/type/test commands.
8. Test-only provider and storage configuration.
9. Common errors and recovery.
10. Shutdown/cleanup commands that do not delete user data unexpectedly.

Do not fill these with guessed commands before repository inspection.

## 4. Environment files and secrets

Commit only sanitized examples such as `.env.example` with placeholder values. Real `.env`, private keys, provider secrets, cloud credentials, student datasets, generated exports and logs containing restricted data must be ignored by version control. Check ignores with `git check-ignore` and run secret scanning before commit.

Environment variables should be validated at startup. A missing optional provider credential should disable that provider with a clear status rather than breaking unrelated development; missing required production secrets must fail closed with actionable but redacted diagnostics.

## 5. Local test data

Use synthetic tenant A/tenant B, fictional users, course materials licensed for development or generated fixtures, fake provider models and mock billing events. Seed data must be reproducible and not include real school/student records.

## 6. Agent working procedure

- Before work, inspect `git status`; do not overwrite uncommitted changes.
- Work in the active phase branch/worktree if that convention is approved.
- Keep a focused diff; run relevant tests before committing.
- Never use `git reset --hard`, force push, delete large directories or rewrite history unless explicitly authorized and verified safe.
- Keep tests and docs synchronized with behavior.
- Record setup command failures in the current phase log.

## 7. Local command inventory

### 7.1 Backend API (Python 3.12 + FastAPI)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (optional/recommended)
python -m venv .venv
# Activate on Windows: .venv\Scripts\Activate.ps1
# Activate on Linux/macOS: source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Copy environment template
cp ../.env.example ../.env

# Run unit and contract tests
$env:PYTHONPATH="backend"
python -m pytest backend/tests -v

# Run Ruff linter and formatter
ruff check backend/app backend/tests
ruff format --check backend/app backend/tests

# Start FastAPI development server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
# Access API Docs: http://127.0.0.1:8000/docs
# Access Health: http://127.0.0.1:8000/health
```

### 7.2 Frontend Web Portal (Next.js + React + TypeScript)

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Run frontend unit tests
npm test

# Start Next.js development server
npm run dev
# Access Web App: http://localhost:3000
```

### 7.3 End-to-End Verification

```bash
# Check backend health probe
curl http://127.0.0.1:8000/health

# Check backend readiness probe
curl http://127.0.0.1:8000/ready
```

| Task | Command | Verified? |
|---|---|---|
| Bootstrap | Pending P01 | No |
| Start database | Pending P01 | No |
| Apply migrations | Pending P01 | No |
| Start application | Pending P01 | No |
| Unit tests | Pending P01 | No |
| Integration tests | Pending P01 | No |
| Lint/format/type checks | Pending P01 | No |
| Secret/dependency scan | Pending P01 | No |

Do not claim the project is locally reproducible until a clean setup has been performed using these documented steps.
