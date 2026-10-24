"""Automated Release Packaging and Deployment Readiness Tests for Gayatri Cloud (P21).
Validates production manifests, Docker specifications, non-root user contexts,
and deployment runbooks.
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def repo_root() -> Path:
    """Path to repository root."""
    return Path(__file__).resolve().parent.parent.parent


def test_release_manifest_integrity(repo_root: Path):
    """Verifies release-manifest.json exists, is valid JSON, and contains 64-char SHA256 hashes."""
    manifest_path = repo_root / "release-manifest.json"
    assert manifest_path.exists(), "release-manifest.json must exist"

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["application_name"] == "Gayatri Cloud"
    assert manifest["release_version"] == "v1.0.0-pilot"
    assert len(manifest["git_commit"]) > 0
    assert "artifact_checksums_sha256" in manifest

    checksums = manifest["artifact_checksums_sha256"]
    assert len(checksums) >= 6
    for path, sha256_hash in checksums.items():
        assert len(sha256_hash) == 64, f"Invalid SHA-256 for {path}"


def test_backend_dockerfile_security_and_healthcheck(repo_root: Path):
    """Verifies backend/Dockerfile runs as non-root (UID 10001) and includes healthcheck."""
    dockerfile = repo_root / "backend" / "Dockerfile"
    assert dockerfile.exists()

    content = dockerfile.read_text(encoding="utf-8")
    assert "USER 10001" in content or "USER backenduser" in content
    assert "HEALTHCHECK " in content
    assert "uvicorn" in content
    assert "workers" in content


def test_frontend_dockerfile_security_and_healthcheck(repo_root: Path):
    """Verifies frontend/Dockerfile runs as non-root nextjs user and exposes healthcheck."""
    dockerfile = repo_root / "frontend" / "Dockerfile"
    assert dockerfile.exists()

    content = dockerfile.read_text(encoding="utf-8")
    assert "USER nextjs" in content
    assert "HEALTHCHECK " in content
    assert "server.js" in content


def test_docker_compose_production_architecture(repo_root: Path):
    """Verifies docker-compose.prod.yml defines db, backend, frontend, and reverse proxy with healthcheck ordering."""
    compose_path = repo_root / "docker-compose.prod.yml"
    assert compose_path.exists()

    content = compose_path.read_text(encoding="utf-8")
    assert "db:" in content
    assert "backend:" in content
    assert "frontend:" in content
    assert "reverse_proxy:" in content
    assert "condition: service_healthy" in content
    assert "gayatri_internal" in content


def test_environment_configuration_template_safety(repo_root: Path):
    """Verifies .env.production.example exists and contains no committed secrets."""
    env_example = repo_root / ".env.production.example"
    assert env_example.exists()

    content = env_example.read_text(encoding="utf-8")
    assert "REPLACE_WITH_" in content
    assert "APP_ENV=production" in content
    # Ensure real keys are not in the template
    assert "sk-" not in content


def test_deployment_runbook_ssm_and_no_port_22(repo_root: Path):
    """Verifies deployment runbook prohibits open SSH port 22 and requires AWS SSM Session Manager."""
    runbook_path = repo_root / "docs" / "deployment" / "PILOT_DEPLOYMENT_RUNBOOK.md"
    assert runbook_path.exists()

    content = runbook_path.read_text(encoding="utf-8")
    assert "PROHIBITED" in content
    assert "ssm start-session" in content
    assert "alembic upgrade head" in content
    assert "alembic downgrade -1" in content


def test_owner_release_checklist_governance(repo_root: Path):
    """Verifies owner release checklist documents cloud cost estimates and approval gate."""
    checklist_path = repo_root / "docs" / "deployment" / "RELEASE_CHECKLIST.md"
    assert checklist_path.exists()

    content = checklist_path.read_text(encoding="utf-8")
    assert "Monthly Est." in content
    assert "DEC-011" in content
    assert "AWAITING_OWNER" in content
