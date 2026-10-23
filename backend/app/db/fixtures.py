"""Synthetic test data fixtures for reproducible local development and testing."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    ClassGroup,
    Course,
    CourseEnrollment,
    CourseOffering,
    CourseVersion,
    Membership,
    Organization,
    RoleAssignment,
    UserAccount,
)


async def seed_synthetic_tenants(session: AsyncSession) -> dict[str, object]:
    """Seed synthetic organizations, users, and courses for testing isolation."""
    # 1. Organization Alpha (School A)
    org_alpha = Organization(
        name="Alpha Academy",
        slug="alpha-academy",
        status="active",
    )
    # 2. Organization Beta (School B)
    org_beta = Organization(
        name="Beta High School",
        slug="beta-high",
        status="active",
    )
    session.add_all([org_alpha, org_beta])
    await session.flush()

    # 3. Users: Student Alpha, Student Beta, Teacher Alpha
    student_alpha = UserAccount(
        email="student.alpha@example.internal",
        full_name="Alice Alpha",
        is_active=True,
        is_verified=True,
    )
    student_beta = UserAccount(
        email="student.beta@example.internal",
        full_name="Bob Beta",
        is_active=True,
        is_verified=True,
    )
    teacher_alpha = UserAccount(
        email="teacher.alpha@example.internal",
        full_name="Dr. Taylor Alpha",
        is_active=True,
        is_verified=True,
    )
    session.add_all([student_alpha, student_beta, teacher_alpha])
    await session.flush()

    # 4. Memberships & Roles
    mem_student_a = Membership(
        user_id=student_alpha.id, organization_id=org_alpha.id, status="active"
    )
    mem_teacher_a = Membership(
        user_id=teacher_alpha.id, organization_id=org_alpha.id, status="active"
    )
    mem_student_b = Membership(
        user_id=student_beta.id, organization_id=org_beta.id, status="active"
    )
    session.add_all([mem_student_a, mem_teacher_a, mem_student_b])
    await session.flush()

    role_s_a = RoleAssignment(membership_id=mem_student_a.id, role="STUDENT")
    role_t_a = RoleAssignment(membership_id=mem_teacher_a.id, role="TEACHER")
    role_s_b = RoleAssignment(membership_id=mem_student_b.id, role="STUDENT")
    session.add_all([role_s_a, role_t_a, role_s_b])
    await session.flush()

    # 5. Course for Alpha
    course_alpha = Course(
        organization_id=org_alpha.id,
        code="PHYS-101",
        title="Introductory Mechanics",
        is_global=False,
    )
    session.add(course_alpha)
    await session.flush()

    v_alpha = CourseVersion(
        course_id=course_alpha.id,
        version_tag="v1.0.0",
        status="published",
    )
    session.add(v_alpha)
    await session.flush()

    offering_alpha = CourseOffering(
        course_version_id=v_alpha.id,
        organization_id=org_alpha.id,
        term="Fall 2026",
    )
    session.add(offering_alpha)
    await session.flush()

    class_alpha = ClassGroup(
        organization_id=org_alpha.id,
        offering_id=offering_alpha.id,
        name="Section 1A",
    )
    session.add(class_alpha)
    await session.flush()

    enrollment_alpha = CourseEnrollment(
        student_id=student_alpha.id,
        offering_id=offering_alpha.id,
        status="enrolled",
    )
    session.add(enrollment_alpha)
    await session.commit()

    return {
        "org_alpha": org_alpha,
        "org_beta": org_beta,
        "student_alpha": student_alpha,
        "student_beta": student_beta,
        "teacher_alpha": teacher_alpha,
        "course_alpha": course_alpha,
        "offering_alpha": offering_alpha,
    }
