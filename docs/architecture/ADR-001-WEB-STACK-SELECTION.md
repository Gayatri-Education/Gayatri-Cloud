# ADR-001: Web Stack and Local Architecture Selection

**Status:** APPROVED (Confirmed via `gayatri_cloud_agent_goal.md` and owner baseline)  
**Date:** 2026-10-24  
**Context Phase:** P01 — Local project foundation and CI  
**Decisions Addressed:** DEC-001, DEC-002, DEC-003  

---

## 1. Context and Problem Statement

Gayatri is transitioning from an offline/desktop PySide6 architecture (`Gayatri AI - Godess of Knowledge`) to a cloud-first, course-independent educational web platform (`Gayatri Cloud`). The platform must deliver responsive web experiences for students, teachers, parents, and administrators across 8 UI languages, while maintaining high-assurance server-side AI execution, tenant isolation, and strict state validation.

We must select a unified, maintainable, and reproducible stack for:
1. Web frontend (portals, responsive design, streaming chat, offline caching).
2. Backend API and domain services (AI gateway, instruction cascade, SLR mastery engine, RAG).
3. Persistence and migration layer.
4. Testing and CI frameworks.

---

## 2. Decision Matrix and Alternatives Considered

### 2.1 Backend Framework
- **Option A: FastAPI (Python 3.12)** — **SELECTED**
  - *Pros:* Direct compatibility with tested Python algorithms from reference repository (`central_platform/teacher`, `slr`, `rag`, `ai`); native async/await for SSE streaming and concurrent AI gateway calls; automatic OpenAPI/Swagger generation; strict validation via Pydantic v2; excellent test ecosystem (`pytest`, `httpx`).
  - *Cons:* Slightly heavier memory footprint than Go/Rust; requires disciplined async architecture.
- **Option B: Node.js / Express or NestJS (TypeScript)**
  - *Cons:* Requires rewriting 100% of the proven pedagogical and mastery algorithms, RAG chunking logic, and prompt engineering from scratch; high regression risk.
- **Option C: Django / Django REST Framework**
  - *Cons:* Heavier ORM overhead, less natural streaming response paradigm than FastAPI.

### 2.2 Frontend Framework
- **Option A: Next.js (React 18+, TypeScript, Tailwind CSS)** — **SELECTED**
  - *Pros:* Modern responsive web support for desktop, tablet, and mobile; Server-Side Rendering (SSR) for fast initial loads of lesson content; built-in internationalization routing; rich ecosystem for accessible components; strong streaming fetch support.
  - *Cons:* Requires Node.js build tooling.
- **Option B: Vite + React SPA**
  - *Cons:* Less streamlined for SEO/SSR and server-cached lesson views.
- **Option C: PySide6 / PyQt (Legacy Reference)**
  - *REJECTED:* Desktop-only; fundamentally incompatible with multi-tenant browser cloud delivery.

### 2.3 Persistence & Migrations
- **Relational Store:** PostgreSQL 16+ with `pgvector` extension (AWS RDS for production, local PostgreSQL / container for development).
- **ORM / Query Builder:** SQLAlchemy 2.0 (async mode) for strict type safety and modular repository patterns.
- **Schema Migrations:** Alembic for version-controlled, forward/backward migrations.
- **Object Storage:** AWS S3 for production, local filesystem storage adapter with identical S3-compatible interface for local testing.

### 2.4 Testing & CI
- **Backend:** `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx` (async client), `ruff` for ultra-fast linting and formatting, `mypy` for static typing.
- **Frontend:** `vitest` / `@testing-library/react` / `eslint`.
- **CI:** GitHub Actions testing Python 3.12 and Node.js 20+ on clean checkouts with zero live cloud credentials.

---

## 3. Decision Outcome

We adopt a decoupled full-stack architecture within the `Gayatri Cloud` repository:
- **`backend/`**: FastAPI (Python 3.12), SQLAlchemy 2.0 async, Alembic, Pydantic v2, pytest.
- **`frontend/`**: Next.js, React, TypeScript, Tailwind CSS.
- **`docs/`**: Comprehensive control plane and architectural documentation.
- **Root**: Unified `.gitignore`, `.env.example`, and `.github/workflows/ci.yml`.

---

## 4. Consequences and Invariants

1. **Zero Secret Leakage:** The frontend communicates with the backend exclusively via HTTPS/WSS; no third-party AI keys or database credentials are ever delivered to the browser.
2. **Deterministic CI:** All tests in CI execute against local mocks, SQLite/Postgres in-memory or container fixtures, and synthetic data; no live AWS billing or AI API credits required.
3. **Domain Decoupling:** Core domain logic (instruction cascade, SLR calculation) is located in pure Python modules without framework dependencies, facilitating direct porting and unit testing.
