# Gayatri Cloud — Local Pre-Flight Verification & Testing Guide

**Document Version:** 1.0.0  
**Effective Date:** 2026-10-24  
**Classification:** Operational Guide / Internal  
**Target:** Local Development & Pre-EC2 Deployment Certification  

---

## 1. Overview & Objective

Before uploading Gayatri Cloud code, docker configurations, or database migrations to an AWS EC2 instance, all application behaviors, security rules, and user journeys must be verified locally.

This guide provides two complementary verification workflows:
1. **Automated Pre-Flight Certification (`run_local_preflight.py`):** Runs a 7-phase automated pipeline that validates environments, container configurations, database schema integrity, executes all 132 backend pytest tests and 67 frontend vitest tests, launches a live API server to execute real HTTP smoke tests, and produces an auditable `local-preflight-report.json`.
2. **Interactive Developer Stack (`dev_local_stack.py`):** Spins up both the FastAPI backend (`http://127.0.0.1:8000`) and the Next.js frontend (`http://localhost:3000`) with pre-seeded demonstration accounts for interactive browser verification.

---

## 2. Automated One-Click Certification

Run the comprehensive pre-flight verification script from the repository root:

```powershell
python scripts/run_local_preflight.py
```

### The 7 Automated Verification Phases:

| Phase | Check Name | What It Validates |
|---|---|---|
| **Phase 1** | **Environment & Source Integrity** | Python >= 3.12, Node >= 18, clean git state, absence of unmasked secrets (`.pem`, `.key`, `id_rsa`, `.env.production`). |
| **Phase 2** | **Static Container & Config Audit** | `backend/Dockerfile` non-root (UID 10001) & healthcheck; `frontend/Dockerfile` non-root (UID 1001) & standalone; `docker-compose.prod.yml` service chaining; `nginx/nginx.conf` security headers. |
| **Phase 3** | **Relational Schema Parity** | Binds all SQLAlchemy models against a local engine, verifying that all 20+ database tables compile with valid foreign keys and zero column conflicts. |
| **Phase 4** | **Test Suites & Linters** | Runs `ruff check` (0 errors), `next lint` (0 warnings), 132 backend pytest tests (100% pass), and 67 frontend vitest tests (100% pass). |
| **Phase 5** | **Live API Smoke & Milestones** | Spawns a live background Uvicorn server, executes real HTTP requests to verify readiness probes, Prometheus metrics exposition, 8-language translations, user registration, JWT login, and circuit breaker trip/reset drills. |
| **Phase 6** | **Production Build Verification** | Confirms Next.js standalone production bundle (`.next/standalone/server.js`) and optimized static chunk assets. |
| **Phase 7** | **Certification Synthesis** | Compiles pass/fail records and outputs `local-preflight-report.json`. |

When all phases pass, the terminal will display:
```
######################################################################
### FINAL VERDICT: CERTIFIED_READY_FOR_DEPLOYMENT
### All local software layers verified with 100% test & runtime evidence!
### Report saved to: local-preflight-report.json
######################################################################
```

---

## 3. Interactive Browser Verification Harness

To visually inspect and interact with every portal in your web browser, execute:

```powershell
python scripts/dev_local_stack.py
```

This command automatically creates a local SQLite database (`local_dev.db`), seeds pre-configured demo users across every role, and launches both backend and frontend servers.

### Pre-Seeded Demo Credentials

| Role | Email | Password | Allowed Access |
|---|---|---|---|
| **Platform Super-Admin** | `superadmin@gayatri.internal` | `DemoAdmin123!` | System-wide observability, AI policy, tenant oversight |
| **Organization Admin** | `admin@iitb.ac.in` | `DemoAdmin123!` | IIT Bombay members, domain verification, audit logs, fee schedules |
| **Teacher** | `prof.sharma@iitb.ac.in` | `DemoTeacher123!` | Class rosters, 5-tier instruction cascade, student interventions |
| **Student** | `ananya.roy@iitb.ac.in` | `DemoStudent123!` | Course catalog, Socratic tutor, assessments, mastery radar |
| **Parent / Guardian** | `sunita.roy@gmail.com` | `DemoParent123!` | Linked child progress, completed assessments, class notices |

---

## 4. Manual Browser Verification Checklist

### 4.1 Student Portal Journey (`/dashboard`)
1. Open `http://localhost:3000/dashboard` and log in as `ananya.roy@iitb.ac.in`.
2. **Course Catalog (`/courses`):** Verify "CS-201: Distributed Systems & Consensus" appears with version `v1.0.0` pinned.
3. **Interactive Socratic Tutor (`/tutoring`):**
   - Click **Start Session**.
   - Type `"Explain Raft leader election"`.
   - Verify server-side AI responds with a pedagogical Socratic hint rather than an immediate answer.
4. **Assessment Taking (`/assessments`):**
   - Take an assessment attempt.
   - Verify autosave indicator triggers and timer updates.
5. **Mastery Radar (`/mastery`):** Verify mastery score bar reflects concept progress.

### 4.2 Teacher Portal Journey (`/teacher/dashboard`)
1. Open `http://localhost:3000/teacher/dashboard` and log in as `prof.sharma@iitb.ac.in`.
2. **Class Roster (`/teacher/roster`):** Verify student "Ananya Roy" is listed as enrolled.
3. **5-Tier Instruction Cascade (`/teacher/instructions`):**
   - View active directive: `"Guide students using Socratic questions before revealing Paxos vs Raft tradeoffs"`.
   - Add a new assignment-tier instruction and verify priority ordering.
4. **Intervention Queue:** Acknowledge or resolve any flagged student concepts.

### 4.3 Parent Portal Journey (`/parent/dashboard`)
1. Open `http://localhost:3000/parent/dashboard` and log in as `sunita.roy@gmail.com`.
2. **Linked Children (`/parent/children`):** Verify "Ananya Roy" appears with `verified` status.
3. **Privacy Filter Verification:** Verify mastery summary is visible, but raw chat transcripts are omitted to preserve student privacy.

### 4.4 Admin & Observability Journey (`/admin/dashboard`)
1. Open `http://localhost:3000/admin/dashboard` and log in as `admin@iitb.ac.in`.
2. **Member Role Invariant (RQ-003):** Attempt to assign `TEACHER` role to `ananya.roy@iitb.ac.in` -> Verify UI rejects request with HTTP 400 bad request error.
3. **Observability & Health (`/admin/observability`):**
   - Verify deep health status cards (Database, Storage, Outbox backlog, Circuit breakers).
   - In **Circuit Breaker Controls**, click **Trip Breaker** on OpenAI -> Verify state switches to `OPEN`.
   - Click **Reset Breaker** -> Verify state returns to `CLOSED`.
   - Click **Run Backup Snapshot** -> Verify SHA-256 snapshot manifest generates.

### 4.5 Multilingual & Accessibility Controls
1. Use the **Language Dropdown** in the navbar:
   - Switch language to **हिन्दी (Hindi)** -> Verify navigation links change (`पाठ्यक्रम`, `डैशबोर्ड`, `मूल्यांकन`).
   - Switch language to **संस्कृतम् (Sanskrit)** -> Verify AI tutor label changes to `एआई गुरुः`.
   - Test remaining verified languages: தமிழ் (Tamil), తెలుగు (Telugu), ಕನ್ನಡ (Kannada), मराठी (Marathi), বাংলা (Bengali).
2. **Accessibility Controls:**
   - Toggle **High Contrast Mode** -> Verify dark/light contrast elements adapt.
   - Adjust **Font Size** (A- / A+) -> Verify UI typography scales dynamically.

### 4.6 Offline Reading Reader (`/offline`)
1. Open `http://localhost:3000/offline`.
2. Click **Download Course for Offline Reading** on CS-201.
3. Verify lesson chunks are cached into local storage with SHA-256 integrity verification.
4. Disconnect your internet connection (or disable network in Chrome DevTools) -> Refresh `/offline`.
5. Verify course syllabus and lesson reading mode remain accessible with sticky offline indicator active.

### 4.7 Privacy & GDPR Data Export (`/settings/privacy`)
1. Open `http://localhost:3000/settings/privacy`.
2. Click **Download My Data Archive (GDPR Art. 20)** -> Verify JSON archive downloads with SHA-256 verification hash.
3. Click **Request Account Deletion** -> Verify 7-day grace period is scheduled and statutory financial records note is displayed.

---

## 5. Local Diagnostics & Troubleshooting

- **Port Conflict (8000 or 3000 already in use):**
  Check active ports:
  ```powershell
  Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess
  ```
  Terminate conflicting process:
  ```powershell
  Stop-Process -Id <PID> -Force
  ```
- **Reset Local Database:**
  Simply delete `local_dev.db`:
  ```powershell
  Remove-Item local_dev.db
  python scripts/dev_local_stack.py
  ```
  The script will automatically re-create and re-seed clean baseline demo records.
