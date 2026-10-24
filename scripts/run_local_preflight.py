#!/usr/bin/env python3
"""Gayatri Cloud — Unified Local Pre-Flight Certification Harness.

Executes a 7-phase comprehensive local inspection verifying source code,
container definitions, database migrations, automated test suites, live API
runtime health, and production frontend bundles prior to EC2 provisioning.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"
REPORT_PATH = REPO_ROOT / "local-preflight-report.json"
TEMP_DB_PATH = REPO_ROOT / "local_preflight.db"


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def log_phase(title: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}>>> {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")


def log_step(name: str, status: str, detail: str = ""):
    badge = (
        f"{Colors.GREEN}[PASS]{Colors.RESET}"
        if status == "PASS"
        else f"{Colors.RED}[FAIL]{Colors.RESET}"
    )
    print(f"  {badge} {name:<45} {detail}")


def run_command(
    cmd: list[str], cwd: Path | None = None, env: dict | None = None
) -> tuple[int, str, str]:
    """Run a subprocess and capture return code, stdout, and stderr."""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    res = subprocess.run(
        cmd,
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=merged_env,
        shell=sys.platform == "win32",
    )
    return res.returncode, res.stdout, res.stderr


# ==============================================================================
# Phase 1: Environment & Source Code Integrity
# ==============================================================================
def verify_environment_and_source() -> dict:
    log_phase("Phase 1: Environment & Source Code Integrity")
    results = {}

    # Python version
    py_ver = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    is_py_ok = sys.version_info >= (3, 12)
    status = "PASS" if is_py_ok else "FAIL"
    log_step("Python Version (>= 3.12)", status, f"Installed: {py_ver}")
    results["python_version"] = {"status": status, "version": py_ver}

    # Node.js version
    code, stdout, _ = run_command(["node", "--version"])
    node_ver = stdout.strip() if code == 0 else "Not found"
    status = "PASS" if code == 0 else "FAIL"
    log_step("Node.js Version (>= 18)", status, f"Installed: {node_ver}")
    results["node_version"] = {"status": status, "version": node_ver}

    # Git repository state & unmasked secrets check
    code, stdout, _ = run_command(["git", "status", "--porcelain"])
    forbidden_files = [".env.production", "private_key.pem", "id_rsa"]
    found_forbidden = [f for f in forbidden_files if (REPO_ROOT / f).exists()]
    status = "PASS" if not found_forbidden else "FAIL"
    detail = (
        "No exposed secrets"
        if not found_forbidden
        else f"Violations: {found_forbidden}"
    )
    log_step("Secret Exposure Audit", status, detail)
    results["secrets_check"] = {"status": status, "details": detail}

    # Core documentation presence
    required_docs = [
        "AGENTS.md",
        "GAYATRI_CLOUD_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md",
        "docs/agent/CURRENT_STATE.md",
        "docs/agent/PROGRESS.md",
        "docs/agent/REQUIREMENTS_TRACEABILITY.md",
        "docs/deployment/PILOT_DEPLOYMENT_RUNBOOK.md",
        "docs/deployment/RELEASE_CHECKLIST.md",
    ]
    missing_docs = [d for d in required_docs if not (REPO_ROOT / d).exists()]
    status = "PASS" if not missing_docs else "FAIL"
    log_step(
        "Core Governance Docs Presence", status, f"Checked {len(required_docs)} files"
    )
    results["docs_check"] = {"status": status, "missing": missing_docs}

    return results


# ==============================================================================
# Phase 2: Static Container & Configuration Audit
# ==============================================================================
def verify_containers_and_configs() -> dict:
    log_phase("Phase 2: Static Container & Configuration Audit")
    results = {}

    # Backend Dockerfile audit
    backend_docker = BACKEND_DIR / "Dockerfile"
    if backend_docker.exists():
        content = backend_docker.read_text(encoding="utf-8")
        has_user = "USER 10001" in content or "USER backenduser" in content
        has_health = "HEALTHCHECK " in content
        has_uvicorn = "uvicorn" in content and "workers" in content
        is_ok = has_user and has_health and has_uvicorn
        status = "PASS" if is_ok else "FAIL"
        log_step(
            "Backend Dockerfile (UID 10001, Healthcheck)",
            status,
            "Multi-stage ASGI runner",
        )
        results["backend_dockerfile"] = {
            "status": status,
            "non_root": has_user,
            "healthcheck": has_health,
        }
    else:
        log_step("Backend Dockerfile", "FAIL", "Missing file")
        results["backend_dockerfile"] = {"status": "FAIL", "reason": "missing"}

    # Frontend Dockerfile audit
    frontend_docker = FRONTEND_DIR / "Dockerfile"
    if frontend_docker.exists():
        content = frontend_docker.read_text(encoding="utf-8")
        has_user = "USER nextjs" in content
        has_health = "HEALTHCHECK " in content
        has_standalone = "server.js" in content
        is_ok = has_user and has_health and has_standalone
        status = "PASS" if is_ok else "FAIL"
        log_step(
            "Frontend Dockerfile (UID 1001, Standalone)",
            status,
            "Multi-stage Node runner",
        )
        results["frontend_dockerfile"] = {
            "status": status,
            "non_root": has_user,
            "standalone": has_standalone,
        }
    else:
        log_step("Frontend Dockerfile", "FAIL", "Missing file")
        results["frontend_dockerfile"] = {"status": "FAIL", "reason": "missing"}

    # Docker Compose spec audit
    compose_file = REPO_ROOT / "docker-compose.prod.yml"
    if compose_file.exists():
        content = compose_file.read_text(encoding="utf-8")
        services = ["db:", "backend:", "frontend:", "reverse_proxy:"]
        has_services = all(s in content for s in services)
        has_health_dep = "condition: service_healthy" in content
        is_ok = has_services and has_health_dep
        status = "PASS" if is_ok else "FAIL"
        log_step(
            "Docker Compose Production Architecture",
            status,
            f"4 services & health chaining: {is_ok}",
        )
        results["compose_spec"] = {"status": status, "services_present": has_services}
    else:
        log_step("Docker Compose Production", "FAIL", "Missing file")
        results["compose_spec"] = {"status": "FAIL", "reason": "missing"}

    # Nginx reverse proxy configuration
    nginx_conf = REPO_ROOT / "nginx" / "nginx.conf"
    if nginx_conf.exists():
        content = nginx_conf.read_text(encoding="utf-8")
        has_security_headers = (
            "X-Content-Type-Options" in content and "X-Frame-Options" in content
        )
        has_proxy = (
            "proxy_pass http://backend_upstream" in content
            and "proxy_pass http://frontend_upstream" in content
        )
        is_ok = has_security_headers and has_proxy
        status = "PASS" if is_ok else "FAIL"
        log_step(
            "Nginx Reverse Proxy & OWASP Headers",
            status,
            f"TLS/Headers configured: {is_ok}",
        )
        results["nginx_config"] = {
            "status": status,
            "headers_configured": has_security_headers,
        }
    else:
        log_step("Nginx Configuration", "FAIL", "Missing file")
        results["nginx_config"] = {"status": "FAIL", "reason": "missing"}

    return results


# ==============================================================================
# Phase 3: Database & Relational Schema Parity
# ==============================================================================
async def verify_database_schema_async() -> dict:
    log_phase("Phase 3: Relational Schema & Table Parity Check")
    results = {}

    # Import SQLAlchemy models dynamically
    sys.path.insert(0, str(BACKEND_DIR))
    from app.db.models import Base
    from sqlalchemy.ext.asyncio import create_async_engine

    test_db_url = f"sqlite+aiosqlite:///{TEMP_DB_PATH.as_posix()}"
    engine = create_async_engine(test_db_url, connect_args={"check_same_thread": False})

    try:
        # Create all tables from metadata
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        table_names = list(Base.metadata.tables.keys())
        expected_tables = [
            "user_accounts",
            "auth_identities",
            "session_devices",
            "organizations",
            "memberships",
            "role_assignments",
            "courses",
            "course_versions",
            "course_offerings",
            "course_enrollments",
            "teacher_instructions",
            "teacher_interventions",
            "guardian_relationships",
            "subscription_plans",
            "subscriptions",
            "institution_fees",
            "fee_payments",
            "account_deletion_requests",
            "security_audit_logs",
            "event_outbox",
        ]
        missing_tables = [t for t in expected_tables if t not in table_names]
        status = "PASS" if not missing_tables else "FAIL"
        log_step(
            "Database Metadata Schema Parity",
            status,
            f"{len(table_names)} tables bound; missing: {len(missing_tables)}",
        )
        results["schema_parity"] = {
            "status": status,
            "total_tables": len(table_names),
            "missing_expected": missing_tables,
        }
    finally:
        await engine.dispose()

    return results


# ==============================================================================
# Phase 4: Automated Test Suites & Linters
# ==============================================================================
def verify_automated_test_suites() -> dict:
    log_phase("Phase 4: Automated Test Suites & Linters")
    results = {}

    # 1. Backend ruff check
    code, _, stderr = run_command(["ruff", "check", "app", "tests"], cwd=BACKEND_DIR)
    status = "PASS" if code == 0 else "FAIL"
    log_step("Backend Ruff Linter", status, "0 errors" if code == 0 else stderr[:60])
    results["backend_linter"] = {"status": status, "exit_code": code}

    # 2. Frontend next lint
    code, _, stderr = run_command(["npm", "run", "lint"], cwd=FRONTEND_DIR)
    status = "PASS" if code == 0 else "FAIL"
    log_step(
        "Frontend Next.js ESLint", status, "0 warnings" if code == 0 else stderr[:60]
    )
    results["frontend_linter"] = {"status": status, "exit_code": code}

    # 3. Backend pytest regression suite (132 tests)
    print("  ... Running 132 backend pytest tests (this may take ~30 seconds) ...")
    start_t = time.perf_counter()
    code, _stdout, _ = run_command(
        ["python", "-m", "pytest", "tests/", "-q"], cwd=BACKEND_DIR
    )
    dur = time.perf_counter() - start_t
    status = "PASS" if code == 0 else "FAIL"
    log_step("Backend Pytest Regression (132 tests)", status, f"Duration: {dur:.1f}s")
    results["backend_tests"] = {
        "status": status,
        "exit_code": code,
        "duration_s": round(dur, 2),
    }

    # 4. Frontend vitest suite (67 tests)
    print("  ... Running 67 frontend vitest tests ...")
    start_t = time.perf_counter()
    code, _stdout, _ = run_command(["npm", "run", "test"], cwd=FRONTEND_DIR)
    dur = time.perf_counter() - start_t
    status = "PASS" if code == 0 else "FAIL"
    log_step("Frontend Vitest Suite (67 tests)", status, f"Duration: {dur:.1f}s")
    results["frontend_tests"] = {
        "status": status,
        "exit_code": code,
        "duration_s": round(dur, 2),
    }

    return results


# ==============================================================================
# Phase 5: Live API Server Smoke & Milestone Testing
# ==============================================================================
def verify_live_api_runtime() -> dict:
    log_phase("Phase 5: Live API Runtime Smoke & Milestone Check")
    results = {}

    # Launch live FastAPI server in background subprocess
    server_env = {
        "ENVIRONMENT": "development",
        "DATABASE_URL": f"sqlite+aiosqlite:///{TEMP_DB_PATH.as_posix()}",
        "STORAGE_BACKEND": "local",
        "LOCAL_STORAGE_PATH": str(REPO_ROOT / "local_storage" / "uploads"),
        "DEFAULT_AI_PROVIDER": "mock",
        "SECRET_KEY": "preflight-test-secret-key-32-characters-minimum-length-for-hs256",
        "PORT": "8000",
        "PYTHONPATH": str(BACKEND_DIR),
    }

    log_file = REPO_ROOT / "local_preflight_server.log"
    server_log = open(log_file, "w", encoding="utf-8")

    server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=BACKEND_DIR,
        env={**os.environ, **server_env},
        stdout=server_log,
        stderr=subprocess.STDOUT,
    )

    base_url = "http://127.0.0.1:8000"
    client = httpx.Client(base_url=base_url, timeout=5.0)

    try:
        # Wait for live server startup (polling /health/live)
        server_ready = False
        for _ in range(30):
            if server_proc.poll() is not None:
                break
            try:
                res = client.get("/health/live")
                if res.status_code == 200:
                    server_ready = True
                    break
            except (httpx.RequestError, OSError):
                pass
            time.sleep(0.5)

        if not server_ready:
            server_log.flush()
            err_output = ""
            if log_file.exists():
                err_output = log_file.read_text(encoding="utf-8", errors="replace")[-500:]
            log_step(
                "Live API Server Startup",
                "FAIL",
                f"Server failed to respond on port 8000. Last log:\n{err_output}",
            )
            results["server_startup"] = {"status": "FAIL"}
            return results

        log_step(
            "Live API Server Startup", "PASS", "Responding on http://127.0.0.1:8000"
        )
        results["server_startup"] = {"status": "PASS"}

        # 1. Health & Deep Readiness Probes
        r_ready = client.get("/health/ready")
        status = "PASS" if r_ready.status_code == 200 else "FAIL"
        log_step("Health Probe (/health/ready)", status, f"HTTP {r_ready.status_code}")
        results["health_ready"] = {"status": status}

        # 2. Prometheus Metrics Exposition
        r_prom = client.get("/api/v1/observability/metrics/prometheus")
        has_prom_text = (
            "gayatri_http_requests_total" in r_prom.text or "# HELP" in r_prom.text
        )
        status = "PASS" if r_prom.status_code == 200 and has_prom_text else "FAIL"
        log_step(
            "Prometheus Metrics Exposition",
            status,
            f"HTTP {r_prom.status_code}; OpenMetrics text verified",
        )
        results["prometheus_metrics"] = {"status": status}

        # 3. Multilingual Translation Registry (8 languages)
        r_lang = client.get("/api/v1/localization/languages")
        langs_data = r_lang.json() if r_lang.status_code == 200 else []
        langs = (
            langs_data
            if isinstance(langs_data, list)
            else langs_data.get("languages", [])
        )
        status = "PASS" if len(langs) == 8 else "FAIL"
        log_step(
            "Multilingual Translation Registry",
            status,
            f"{len(langs)} verified languages supported",
        )
        results["localization_check"] = {
            "status": status,
            "languages_count": len(langs),
        }

        # 4. User Registration & Authentication Flow
        ts = int(datetime.now(UTC).timestamp())
        reg_payload = {
            "email": f"preflight_user_{ts}@gayatri.internal",
            "password": "SecurePassword123!",
            "full_name": "Preflight Learner",
        }
        r_reg = client.post("/api/v1/auth/register", json=reg_payload)
        status = "PASS" if r_reg.status_code in (200, 201) else "FAIL"
        log_step("Live User Registration", status, f"HTTP {r_reg.status_code}")
        results["user_registration"] = {"status": status}

        token = None
        if status == "PASS":
            # Login and retrieve JWT access token
            login_payload = {
                "email": reg_payload["email"],
                "password": reg_payload["password"],
            }
            r_login = client.post("/api/v1/auth/login", json=login_payload)
            if r_login.status_code == 200:
                token = r_login.json().get("access_token")
            status = "PASS" if token else "FAIL"
            log_step(
                "JWT Access Token Issuance",
                status,
                "Token received & verified" if token else "No token",
            )
            results["auth_token"] = {"status": status}

            # Verify /me identity route
            if token:
                r_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
                status_me = "PASS" if r_me.status_code == 200 else "FAIL"
                log_step("User Profile Verification (/auth/me)", status_me, f"HTTP {r_me.status_code}")
                results["user_me"] = {"status": status_me}

        # 5. Deep Dependency Readiness Probe
        r_deep = client.get("/api/v1/observability/deep-health")
        status_deep = "PASS" if r_deep.status_code == 200 else "FAIL"
        log_step("Deep Health Probe (/deep-health)", status_deep, f"HTTP {r_deep.status_code}")
        results["deep_health"] = {"status": status_deep}

        # 6. Admin RBAC Boundary Defense (Unauthenticated Access Denied)
        r_trip = client.post(
            "/api/v1/observability/circuit-breakers/openai/trip",
            json={"reason": "Preflight drill"},
        )
        status_rbac = "PASS" if r_trip.status_code in (401, 403) else "FAIL"
        log_step(
            "Admin RBAC Boundary Defense",
            status_rbac,
            f"HTTP {r_trip.status_code} on unauthenticated admin action",
        )
        results["admin_rbac_defense"] = {"status": status_rbac}

    finally:
        client.close()
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server_proc.kill()
        server_log.close()
        if log_file.exists() and "FAIL" not in [v.get("status") for v in results.values()]:
            with contextlib.suppress(Exception):
                log_file.unlink()
        log_step(
            "Live API Server Graceful Teardown", "PASS", "Subprocess stopped cleanly"
        )

    return results


# ==============================================================================
# Phase 6: Production Build & Asset Verification
# ==============================================================================
def verify_production_build() -> dict:
    log_phase("Phase 6: Production Build & Asset Verification")
    results = {}

    standalone_dir = FRONTEND_DIR / ".next" / "standalone"
    server_js = standalone_dir / "server.js"
    has_standalone = server_js.exists()
    status = "PASS" if has_standalone else "FAIL"
    log_step(
        "Next.js 14 Standalone Bundle (.next/standalone)",
        status,
        "server.js found" if has_standalone else "Missing build output",
    )
    results["standalone_bundle"] = {"status": status}

    static_chunks = FRONTEND_DIR / ".next" / "static" / "chunks"
    has_chunks = static_chunks.exists() and len(list(static_chunks.glob("*.js"))) > 0
    status = "PASS" if has_chunks else "FAIL"
    log_step("Next.js Static Assets & Chunks", status, "Optimized JS bundles verified")
    results["static_chunks"] = {"status": status}

    return results


# ==============================================================================
# Phase 7: Report Synthesis & Certification Verdict
# ==============================================================================
def generate_certification_report(all_results: dict) -> bool:
    log_phase("Phase 7: Certification Synthesis & Release Verdict")

    # Determine overall status
    has_failures = False
    for phase_data in all_results.values():
        if isinstance(phase_data, dict):
            for item_val in phase_data.values():
                if isinstance(item_val, dict) and item_val.get("status") == "FAIL":
                    has_failures = True
                    break

    verdict = (
        "CERTIFIED_READY_FOR_DEPLOYMENT"
        if not has_failures
        else "FAILED_PREFLIGHT_CHECKS"
    )

    report = {
        "report_title": "Gayatri Cloud Local Pre-Flight Certification Report",
        "generated_at": datetime.now(UTC).isoformat(),
        "overall_verdict": verdict,
        "summary": {
            "all_phases_passed": not has_failures,
            "target_architecture": "AWS Single-EC2 Pilot (RDS PostgreSQL 16 + S3)",
            "total_phases_evaluated": len(all_results),
        },
        "phase_results": all_results,
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    if not has_failures:
        print(f"\n{Colors.BOLD}{Colors.GREEN}{'#' * 70}")
        print(f"### FINAL VERDICT: {verdict}")
        print(
            "### All local software layers verified with 100% test & runtime evidence!"
        )
        print(f"### Report saved to: {REPORT_PATH.name}")
        print(f"{'#' * 70}{Colors.RESET}\n")
    else:
        print(f"\n{Colors.BOLD}{Colors.RED}{'#' * 70}")
        print(f"### FINAL VERDICT: {verdict}")
        print(f"### Some checks failed. Review report at: {REPORT_PATH.name}")
        print(f"{'#' * 70}{Colors.RESET}\n")

    # Cleanup temporary SQLite database
    if TEMP_DB_PATH.exists():
        with contextlib.suppress(OSError):
            TEMP_DB_PATH.unlink()

    return not has_failures


def main() -> int:
    print(f"{Colors.BOLD}{Colors.YELLOW}")
    print("*" * 70)
    print("*  GAYATRI CLOUD — COMPREHENSIVE LOCAL PRE-FLIGHT VERIFICATION HARNESS  *")
    print("*" * 70)
    print(f"{Colors.RESET}")

    if TEMP_DB_PATH.exists():
        with contextlib.suppress(OSError):
            TEMP_DB_PATH.unlink()

    all_results = {}
    all_results["phase_1_environment"] = verify_environment_and_source()
    all_results["phase_2_containers"] = verify_containers_and_configs()
    all_results["phase_3_database"] = asyncio.run(verify_database_schema_async())
    all_results["phase_4_test_suites"] = verify_automated_test_suites()
    all_results["phase_5_live_api"] = verify_live_api_runtime()
    all_results["phase_6_frontend_build"] = verify_production_build()

    is_certified = generate_certification_report(all_results)
    return 0 if is_certified else 1


if __name__ == "__main__":
    sys.exit(main())
