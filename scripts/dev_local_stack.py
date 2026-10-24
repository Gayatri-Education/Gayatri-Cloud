#!/usr/bin/env python3
"""Gayatri Cloud — Local Development & Verification Stack Orchestrator.

Spins up the complete Gayatri Cloud platform locally (FastAPI backend + Next.js frontend),
seeds pre-configured demo users across all roles (Student, Teacher, Parent, Admin),
and provides clickable URLs for browser verification.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"
LOCAL_DB_PATH = REPO_ROOT / "local_dev.db"


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


async def seed_local_database() -> None:
    """Seed local SQLite database with demo accounts, courses, and relationships."""
    print(
        f"{Colors.CYAN}[*] Initializing and seeding local database ({LOCAL_DB_PATH.name})...{Colors.RESET}"
    )
    sys.path.insert(0, str(BACKEND_DIR))

    from app.core.rbac import RoleEnum
    from app.core.security import hash_password
    from app.db.models import Base
    from app.db.models.billing import InstitutionFee, SubscriptionPlan
    from app.db.models.course import (
        ContentChunk,
        ContentSource,
        Course,
        CourseEnrollment,
        CourseOffering,
        CourseVersion,
        TeacherInstruction,
    )
    from app.db.models.identity import AuthIdentity, UserAccount
    from app.db.models.organization import (
        GuardianRelationship,
        Membership,
        Organization,
        RoleAssignment,
    )
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    db_url = f"sqlite+aiosqlite:///{LOCAL_DB_PATH.as_posix()}"
    engine = create_async_engine(db_url, connect_args={"check_same_thread": False})

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_maker() as session:
        # Check if already seeded
        from sqlalchemy import select

        res = await session.execute(select(UserAccount).limit(1))
        if res.scalar_one_or_none():
            print(
                f"{Colors.GREEN}[+] Database already seeded with demo records.{Colors.RESET}"
            )
            await engine.dispose()
            return

        # 1. Demo Users
        users = [
            (
                "superadmin@gayatri.internal",
                "Gayatri Super Admin",
                "DemoAdmin123!",
                RoleEnum.SUPER_ADMIN.value,
            ),
            (
                "admin@iitb.ac.in",
                "IITB Academy Admin",
                "DemoAdmin123!",
                RoleEnum.ORG_ADMIN.value,
            ),
            (
                "prof.sharma@iitb.ac.in",
                "Prof. Rajesh Sharma",
                "DemoTeacher123!",
                RoleEnum.TEACHER.value,
            ),
            (
                "ananya.roy@iitb.ac.in",
                "Ananya Roy",
                "DemoStudent123!",
                RoleEnum.STUDENT.value,
            ),
            (
                "sunita.roy@gmail.com",
                "Sunita Roy",
                "DemoParent123!",
                RoleEnum.PARENT.value,
            ),
        ]

        created_users = {}
        for email, name, pwd, _ in users:
            u = UserAccount(
                email=email, full_name=name, is_active=True, is_verified=True
            )
            session.add(u)
            await session.flush()
            auth = AuthIdentity(
                user_id=u.id, provider="email", credential_hash=hash_password(pwd)
            )
            session.add(auth)
            created_users[email] = u

        # 2. Organization & Memberships
        org = Organization(
            name="Indian Institute of Technology Bombay",
            slug="iitb-demo",
            status="active",
        )
        session.add(org)
        await session.flush()

        # Memberships
        for email, _, _, role in users:
            u = created_users[email]
            m = Membership(user_id=u.id, organization_id=org.id, status="active")
            session.add(m)
            await session.flush()
            r = RoleAssignment(membership_id=m.id, role=role)
            session.add(r)

        # 3. Parent-Student Guardian Link
        guardian_link = GuardianRelationship(
            guardian_id=created_users["sunita.roy@gmail.com"].id,
            student_id=created_users["ananya.roy@iitb.ac.in"].id,
            verification_status="verified",
            is_active=True,
        )
        session.add(guardian_link)

        # 4. Course, Published Version & Chunks
        course = Course(
            organization_id=org.id,
            code="CS-201",
            title="Distributed Systems & Consensus",
            description="Core principles of distributed state machines, Paxos, and Raft consensus.",
        )
        session.add(course)
        await session.flush()

        ver = CourseVersion(
            course_id=course.id,
            version_tag="v1.0.0",
            status="published",
            changelog="Initial syllabus release",
        )
        session.add(ver)
        await session.flush()

        src = ContentSource(
            course_version_id=ver.id,
            filename="raft_consensus.pdf",
            mime_type="application/pdf",
            file_size_bytes=1024000,
            s3_uri="s3://gayatri-demo/raft_consensus.pdf",
            checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            ingestion_status="completed",
        )
        session.add(src)
        await session.flush()

        chunks = [
            ContentChunk(
                source_id=src.id,
                chunk_index=0,
                text_content="Raft decomposes consensus into leader election, log replication, and safety.",
                token_count=13,
                section_header="Introduction to Raft",
            ),
            ContentChunk(
                source_id=src.id,
                chunk_index=1,
                text_content="Followers increment term and transition to candidate when election timeout elapses.",
                token_count=13,
                section_header="Leader Election Protocol",
            ),
        ]
        session.add_all(chunks)

        # 5. Offering & Student Enrollment
        offering = CourseOffering(
            organization_id=org.id,
            course_version_id=ver.id,
            term="Autumn 2026",
            status="active",
        )
        session.add(offering)
        await session.flush()

        enrollment = CourseEnrollment(
            student_id=created_users["ananya.roy@iitb.ac.in"].id,
            offering_id=offering.id,
            status="enrolled",
        )
        session.add(enrollment)

        # 6. Teacher 5-Tier Instruction
        instr = TeacherInstruction(
            organization_id=org.id,
            teacher_id=created_users["prof.sharma@iitb.ac.in"].id,
            course_id=course.id,
            tier="COURSE",
            priority=3,
            directive_text="Guide students using Socratic questions before revealing Paxos vs Raft tradeoffs.",
            is_active=True,
        )
        session.add(instr)

        # 7. Freemium Plans & Institutional Fee Schedule
        free_plan = SubscriptionPlan(
            name="Freemium Learner",
            code="free",
            description="Default free plan with standard tutoring limits",
            price_cents=0,
            currency="USD",
            features_json=json.dumps({"tutoring_turns_per_month": 100, "byok_enabled": True}),
            is_active=True,
        )
        session.add(free_plan)

        fee = InstitutionFee(
            organization_id=org.id,
            title="Lab & Cloud Computing Fee",
            description="Semester cluster compute allocation",
            amount_cents=15000,
            currency="USD",
            status="active",
        )
        session.add(fee)

        await session.commit()
        print(
            f"{Colors.GREEN}[+] Successfully seeded demo data across all portals.{Colors.RESET}"
        )

    await engine.dispose()


def print_banner():
    banner = f"""
{Colors.BOLD}{Colors.CYAN}========================================================================
       GAYATRI CLOUD — LOCAL FULL-STACK VERIFICATION DASHBOARD          
========================================================================{Colors.RESET}

{Colors.BOLD}Demo Accounts Pre-Seeded for Local Browser Testing:{Colors.RESET}
  * {Colors.YELLOW}Super-Admin:{Colors.RESET}   superadmin@gayatri.internal   (Password: DemoAdmin123!)
  * {Colors.YELLOW}Org-Admin:{Colors.RESET}     admin@iitb.ac.in              (Password: DemoAdmin123!)
  * {Colors.YELLOW}Teacher:{Colors.RESET}       prof.sharma@iitb.ac.in        (Password: DemoTeacher123!)
  * {Colors.YELLOW}Student:{Colors.RESET}       ananya.roy@iitb.ac.in         (Password: DemoStudent123!)
  * {Colors.YELLOW}Parent:{Colors.RESET}        sunita.roy@gmail.com          (Password: DemoParent123!)

{Colors.BOLD}Clickable Portal URLs:{Colors.RESET}
  * {Colors.GREEN}Student Learner Dashboard:{Colors.RESET}    http://localhost:3000/dashboard
  * {Colors.GREEN}Course Catalog & Ingestion:{Colors.RESET}   http://localhost:3000/courses
  * {Colors.GREEN}Interactive Socratic Tutor:{Colors.RESET}   http://localhost:3000/tutoring
  * {Colors.GREEN}Assessments & Timed Exams:{Colors.RESET}    http://localhost:3000/assessments
  * {Colors.GREEN}Teacher Roster & Cascade:{Colors.RESET}     http://localhost:3000/teacher/dashboard
  * {Colors.GREEN}Parent Progress Radar:{Colors.RESET}        http://localhost:3000/parent/dashboard
  * {Colors.GREEN}Admin Observability & Metrics:{Colors.RESET} http://localhost:3000/admin/observability
  * {Colors.GREEN}Billing & Fee Schedules:{Colors.RESET}       http://localhost:3000/billing
  * {Colors.GREEN}Offline Course Reader:{Colors.RESET}         http://localhost:3000/offline
  * {Colors.GREEN}Privacy & Data Export (GDPR):{Colors.RESET}  http://localhost:3000/settings/privacy
  * {Colors.GREEN}FastAPI Interactive Docs:{Colors.RESET}      http://127.0.0.1:8000/docs
  * {Colors.GREEN}Prometheus Metrics Feed:{Colors.RESET}       http://127.0.0.1:8000/api/v1/observability/metrics/prometheus

{Colors.YELLOW}[!] Press Ctrl+C at any time to gracefully shut down the local stack.{Colors.RESET}
"""
    print(banner)


def main():
    asyncio.run(seed_local_database())

    # Environment settings for local execution
    backend_env = {
        **os.environ,
        "ENVIRONMENT": "development",
        "DATABASE_URL": f"sqlite+aiosqlite:///{LOCAL_DB_PATH.as_posix()}",
        "STORAGE_BACKEND": "local",
        "LOCAL_STORAGE_PATH": str(REPO_ROOT / "local_storage" / "uploads"),
        "DEFAULT_AI_PROVIDER": "mock",
        "SECRET_KEY": "dev-insecure-secret-key-change-in-production-min-32-chars-long",
        "PORT": "8000",
        "PYTHONPATH": str(BACKEND_DIR),
    }

    frontend_env = {
        **os.environ,
        "PORT": "3000",
        "NEXT_PUBLIC_API_URL": "http://127.0.0.1:8000",
    }

    print(
        f"{Colors.CYAN}[*] Starting Backend API Server on http://127.0.0.1:8000...{Colors.RESET}"
    )
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=BACKEND_DIR,
        env=backend_env,
        shell=False,
    )

    print(
        f"{Colors.CYAN}[*] Starting Frontend Web Server on http://localhost:3000...{Colors.RESET}"
    )
    frontend_proc = subprocess.Popen(
        ["npm.cmd" if sys.platform == "win32" else "npm", "run", "dev"],
        cwd=FRONTEND_DIR,
        env=frontend_env,
        shell=False,
    )

    time.sleep(3)
    print_banner()

    try:
        while True:
            time.sleep(1)
            # Check if any child process crashed
            if backend_proc.poll() is not None:
                print(
                    f"{Colors.RED}[!] Backend process exited unexpectedly.{Colors.RESET}"
                )
                break
            if frontend_proc.poll() is not None:
                print(
                    f"{Colors.RED}[!] Frontend process exited unexpectedly.{Colors.RESET}"
                )
                break
    except KeyboardInterrupt:
        print(
            f"\n{Colors.YELLOW}[*] Shutting down Gayatri Cloud local stack...{Colors.RESET}"
        )
    finally:
        for proc, name in [(backend_proc, "Backend"), (frontend_proc, "Frontend")]:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
            print(f"{Colors.GREEN}[+] {name} terminated cleanly.{Colors.RESET}")
        print(
            f"{Colors.BOLD}{Colors.GREEN}[+] Local stack teardown complete.{Colors.RESET}"
        )


if __name__ == "__main__":
    main()
