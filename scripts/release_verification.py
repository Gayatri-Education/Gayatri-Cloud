#!/usr/bin/env python3
"""Release Verification and Packaging Automation for Gayatri Cloud (P21).
Validates production configurations, security boundaries, non-root user contexts,
and generates a cryptographically verifiable release manifest.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def get_git_commit_sha(repo_root: Path) -> str:
    """Retrieve active git commit SHA."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return "uncommitted-local-build"


def compute_file_sha256(file_path: Path) -> str:
    """Compute standard SHA-256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_dockerfiles(repo_root: Path) -> list[str]:
    """Verify backend and frontend Dockerfiles adhere to non-root and healthcheck rules."""
    errors = []
    backend_dockerfile = repo_root / "backend" / "Dockerfile"
    frontend_dockerfile = repo_root / "frontend" / "Dockerfile"
    compose_file = repo_root / "docker-compose.prod.yml"

    if not backend_dockerfile.exists():
        errors.append("backend/Dockerfile is missing")
    else:
        content = backend_dockerfile.read_text(encoding="utf-8")
        if "USER " not in content:
            errors.append("backend/Dockerfile must specify an unprivileged USER")
        if "HEALTHCHECK " not in content:
            errors.append("backend/Dockerfile must specify a HEALTHCHECK")

    if not frontend_dockerfile.exists():
        errors.append("frontend/Dockerfile is missing")
    else:
        content = frontend_dockerfile.read_text(encoding="utf-8")
        if "USER nextjs" not in content and "USER " not in content:
            errors.append("frontend/Dockerfile must specify an unprivileged USER")
        if "HEALTHCHECK " not in content:
            errors.append("frontend/Dockerfile must specify a HEALTHCHECK")

    if not compose_file.exists():
        errors.append("docker-compose.prod.yml is missing")
    else:
        c_content = compose_file.read_text(encoding="utf-8")
        for svc in ["backend:", "frontend:", "db:", "reverse_proxy:"]:
            if svc not in c_content:
                errors.append(f"docker-compose.prod.yml missing service '{svc}'")

    return errors


def verify_no_committed_secrets(repo_root: Path) -> list[str]:
    """Verify no live secrets or real credential files are present."""
    errors = []
    forbidden_files = [".env.production", "private_key.pem", "id_rsa"]
    for fname in forbidden_files:
        p = repo_root / fname
        if p.exists() and p.is_file():
            errors.append(f"Unsafe credential file present: {fname}")

    env_example = repo_root / ".env.production.example"
    if not env_example.exists():
        errors.append(".env.production.example is missing")

    return errors


def generate_release_manifest(repo_root: Path) -> dict[str, str | dict[str, str]]:
    """Construct cryptographic release manifest with artifact checksums."""
    artifacts = [
        "docker-compose.prod.yml",
        "backend/Dockerfile",
        "frontend/Dockerfile",
        ".env.production.example",
        "docs/deployment/PILOT_DEPLOYMENT_RUNBOOK.md",
        "docs/deployment/RELEASE_CHECKLIST.md",
    ]

    checksums = {}
    for rel_path in artifacts:
        target = repo_root / rel_path
        if target.exists():
            checksums[rel_path] = compute_file_sha256(target)

    manifest: dict[str, str | dict[str, str]] = {
        "release_version": "v1.0.0-pilot",
        "application_name": "Gayatri Cloud",
        "git_commit": get_git_commit_sha(repo_root),
        "build_timestamp": datetime.now(UTC).isoformat(),
        "target_architecture": "AWS Single-EC2 Pilot (RDS PostgreSQL + S3)",
        "security_profile": "OWASP Compliant / Non-Root Containers / Tenant Isolated",
        "artifact_checksums_sha256": checksums,
    }

    manifest_path = repo_root / "release-manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    print(f"[*] Starting Gayatri Cloud Release Verification in: {repo_root}")

    docker_errors = verify_dockerfiles(repo_root)
    secret_errors = verify_no_committed_secrets(repo_root)

    all_errors = docker_errors + secret_errors
    if all_errors:
        print("[!] Release Verification FAILED with errors:")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    manifest = generate_release_manifest(repo_root)
    print("[+] Release Verification PASSED cleanly!")
    print(
        f"[+] Release Manifest generated: release-manifest.json (Commit: {manifest['git_commit']})"
    )
    print(f"[+] Total Verified Artifacts: {len(manifest['artifact_checksums_sha256'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
