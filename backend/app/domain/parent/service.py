"""Parent and Guardian domain service.
Implements verified guardian relationships, multi-child overview,
privacy-filtered progress metrics (preventing raw tutoring dialogue leaks),
and sensitive record access audit logging.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import TenantContext
from app.db.models.course import Course, CourseEnrollment, CourseOffering, CourseVersion
from app.db.models.identity import UserAccount
from app.db.models.organization import GuardianRelationship
from app.db.models.teacher import ClassAnnouncement
from app.db.models.tutoring import (
    Assessment,
    AssessmentAttempt,
    CanonicalLearningState,
    MisconceptionRecord,
    TutorSession,
)

logger = logging.getLogger(__name__)


class ParentService:
    """Service managing parent/guardian relationships and privacy-controlled child views."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _verify_guardian_link(
        self, context: TenantContext, student_id: str
    ) -> GuardianRelationship:
        """Verify active and verified relationship exists between caller and student."""
        stmt = select(GuardianRelationship).where(
            GuardianRelationship.guardian_id == context.user.id,
            GuardianRelationship.student_id == student_id,
            GuardianRelationship.is_active.is_(True),
            GuardianRelationship.verification_status == "verified",
        )
        res = await self.session.execute(stmt)
        relationship = res.scalar_one_or_none()

        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: No verified guardian relationship for this student.",
            )

        return relationship

    # =========================================================================
    # 1. Guardian Link Management
    # =========================================================================

    async def list_linked_children(self, context: TenantContext) -> list[dict[str, Any]]:
        """List all children linked to this guardian with verification status and mastery summaries."""
        stmt = (
            select(GuardianRelationship, UserAccount)
            .join(UserAccount, GuardianRelationship.student_id == UserAccount.id)
            .where(GuardianRelationship.guardian_id == context.user.id)
            .order_by(GuardianRelationship.created_at.desc())
        )
        res = await self.session.execute(stmt)
        rows = res.all()

        children = []
        for rel, student in rows:
            # Quick mastery metric
            mastery_stmt = select(func.avg(CanonicalLearningState.mastery_score)).where(
                CanonicalLearningState.student_id == student.id
            )
            mastery_res = await self.session.execute(mastery_stmt)
            avg_mastery = mastery_res.scalar() or 0.0

            # Active courses count
            course_stmt = select(func.count(CourseEnrollment.id)).where(
                CourseEnrollment.student_id == student.id,
                CourseEnrollment.status == "enrolled",
            )
            course_res = await self.session.execute(course_stmt)
            course_count = course_res.scalar() or 0

            children.append(
                {
                    "relationship_id": rel.id,
                    "student_id": student.id,
                    "student_name": student.full_name,
                    "email": student.email,
                    "verification_status": rel.verification_status,
                    "is_active": rel.is_active,
                    "average_mastery": round(float(avg_mastery), 2),
                    "active_courses_count": course_count,
                    "linked_at": rel.created_at.isoformat(),
                }
            )

        return children

    async def request_link(
        self, context: TenantContext, student_identifier: str
    ) -> GuardianRelationship:
        """Submit a guardian link request for a student by ID or email."""
        # Find student
        stmt = select(UserAccount).where(
            (UserAccount.id == student_identifier) | (UserAccount.email == student_identifier)
        )
        res = await self.session.execute(stmt)
        student = res.scalar_one_or_none()

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student account '{student_identifier}' not found.",
            )

        if student.id == context.user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A guardian cannot link to their own account as a student.",
            )

        # Check existing relationship
        rel_stmt = select(GuardianRelationship).where(
            GuardianRelationship.guardian_id == context.user.id,
            GuardianRelationship.student_id == student.id,
        )
        rel_res = await self.session.execute(rel_stmt)
        existing = rel_res.scalar_one_or_none()

        if existing:
            if existing.is_active and existing.verification_status == "verified":
                return existing
            existing.is_active = True
            existing.verification_status = "pending"
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        relationship = GuardianRelationship(
            guardian_id=context.user.id,
            student_id=student.id,
            verification_status="pending",
            is_active=True,
        )
        self.session.add(relationship)
        await self.session.commit()
        await self.session.refresh(relationship)
        return relationship

    async def verify_link(
        self, context: TenantContext, relationship_id: str
    ) -> GuardianRelationship:
        """Verify and approve a guardian relationship."""
        stmt = select(GuardianRelationship).where(GuardianRelationship.id == relationship_id)
        res = await self.session.execute(stmt)
        rel = res.scalar_one_or_none()

        if not rel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guardian relationship not found.",
            )

        rel.verification_status = "verified"
        rel.is_active = True
        await self.session.commit()
        await self.session.refresh(rel)
        return rel

    async def revoke_link(self, context: TenantContext, relationship_id: str) -> None:
        """Immediately revoke a guardian relationship."""
        stmt = select(GuardianRelationship).where(GuardianRelationship.id == relationship_id)
        res = await self.session.execute(stmt)
        rel = res.scalar_one_or_none()

        if not rel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guardian relationship not found.",
            )

        # Ensure caller is guardian or authorized admin
        if (
            rel.guardian_id != context.user.id
            and "SUPER_ADMIN" not in context.roles
            and "ORG_ADMIN" not in context.roles
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to revoke this relationship.",
            )

        rel.is_active = False
        rel.verification_status = "revoked"
        await self.session.commit()

    # =========================================================================
    # 2. Privacy-Filtered Learning Progress
    # =========================================================================

    async def get_child_progress(self, context: TenantContext, student_id: str) -> dict[str, Any]:
        """Retrieve privacy-filtered learning progress for a linked child.
        PRIVACY GUARANTEE: Raw tutoring transcripts (ConversationTurns) are strictly
        redacted from this API. Only high-level competency scores, study duration,
        and concept topics are provided.
        """
        await self._verify_guardian_link(context, student_id)

        # Audit access to sensitive child records
        logger.info(
            "AUDIT_CHILD_RECORD_ACCESS: guardian_id=%s accessed student_id=%s progress",
            context.user.id,
            student_id,
        )

        # 1. Concept masteries
        mastery_stmt = (
            select(CanonicalLearningState)
            .where(CanonicalLearningState.student_id == student_id)
            .order_by(CanonicalLearningState.mastery_score.desc())
        )
        mastery_res = await self.session.execute(mastery_stmt)
        masteries = mastery_res.scalars().all()

        total_score = sum(m.mastery_score for m in masteries)
        overall_mastery = round(total_score / len(masteries), 2) if masteries else 0.0

        concept_summaries = [
            {
                "concept_id": m.concept_id,
                "mastery_score": round(m.mastery_score, 2),
                "stability_days": m.stability,
            }
            for m in masteries[:10]
        ]

        # 2. Tutoring activity minutes (aggregate without exposing raw conversation dialogue)
        session_stmt = select(func.count(TutorSession.id)).where(
            TutorSession.student_id == student_id
        )
        session_count_res = await self.session.execute(session_stmt)
        total_sessions = session_count_res.scalar() or 0

        # 3. Misconceptions count (high-level count, no raw prompts)
        miscon_stmt = select(func.count(MisconceptionRecord.id)).where(
            MisconceptionRecord.student_id == student_id,
            MisconceptionRecord.status == "active",
        )
        miscon_res = await self.session.execute(miscon_stmt)
        active_misconceptions = miscon_res.scalar() or 0

        # 4. Enrolled courses
        enroll_stmt = (
            select(Course.title, CourseOffering.term)
            .select_from(CourseEnrollment)
            .join(CourseOffering, CourseEnrollment.offering_id == CourseOffering.id)
            .join(CourseVersion, CourseOffering.course_version_id == CourseVersion.id)
            .join(Course, CourseVersion.course_id == Course.id)
            .where(
                CourseEnrollment.student_id == student_id,
                CourseEnrollment.status == "enrolled",
            )
        )
        enroll_res = await self.session.execute(enroll_stmt)
        courses = [{"title": title, "term": term} for title, term in enroll_res.all()]

        return {
            "student_id": student_id,
            "overall_mastery": overall_mastery,
            "total_tutoring_sessions": total_sessions,
            "estimated_study_minutes": total_sessions * 25,
            "active_misconceptions_count": active_misconceptions,
            "top_concepts": concept_summaries,
            "enrolled_courses": courses,
            "privacy_disclosure": "Parent Portal Privacy Protocol: Raw conversational turns are excluded from parent views to maintain learner safe-space and autonomous Socratic inquiry.",
        }

    # =========================================================================
    # 3. Child Assessment Results & Reports
    # =========================================================================

    async def get_child_assessments(
        self, context: TenantContext, student_id: str
    ) -> list[dict[str, Any]]:
        """Retrieve completed assessment reports and teacher feedback for a linked child."""
        await self._verify_guardian_link(context, student_id)

        logger.info(
            "AUDIT_CHILD_RECORD_ACCESS: guardian_id=%s accessed student_id=%s assessments",
            context.user.id,
            student_id,
        )

        stmt = (
            select(AssessmentAttempt, Assessment)
            .join(Assessment, AssessmentAttempt.assessment_id == Assessment.id)
            .where(
                AssessmentAttempt.student_id == student_id,
                AssessmentAttempt.status.in_(["completed", "graded", "submitted"]),
            )
            .order_by(AssessmentAttempt.submitted_at.desc())
        )
        res = await self.session.execute(stmt)
        rows = res.all()

        reports = []
        for attempt, assessment in rows:
            pct = (
                round((attempt.total_score / assessment.total_points) * 100, 1)
                if assessment.total_points and attempt.total_score is not None
                else 0.0
            )
            reports.append(
                {
                    "attempt_id": attempt.id,
                    "assessment_id": assessment.id,
                    "title": assessment.title,
                    "score": attempt.total_score or 0.0,
                    "max_points": assessment.total_points,
                    "percentage": pct,
                    "submitted_at": (
                        attempt.submitted_at.isoformat()
                        if attempt.submitted_at
                        else attempt.created_at.isoformat()
                    ),
                    "status": attempt.status,
                }
            )

        return reports

    # =========================================================================
    # 4. Teacher & School Communications
    # =========================================================================

    async def get_child_communications(
        self, context: TenantContext, student_id: str
    ) -> list[dict[str, Any]]:
        """Retrieve class and course announcements relevant to a linked child."""
        await self._verify_guardian_link(context, student_id)

        # Get offering IDs the student is enrolled in
        offering_stmt = select(CourseEnrollment.offering_id).where(
            CourseEnrollment.student_id == student_id,
            CourseEnrollment.status == "enrolled",
        )
        offering_res = await self.session.execute(offering_stmt)
        offering_ids = offering_res.scalars().all()

        if not offering_ids:
            return []

        ann_stmt = (
            select(ClassAnnouncement, UserAccount)
            .join(UserAccount, ClassAnnouncement.teacher_id == UserAccount.id)
            .where(ClassAnnouncement.offering_id.in_(offering_ids))
            .order_by(ClassAnnouncement.created_at.desc())
        )
        ann_res = await self.session.execute(ann_stmt)
        rows = ann_res.all()

        announcements = []
        for ann, teacher in rows:
            announcements.append(
                {
                    "id": ann.id,
                    "offering_id": ann.offering_id,
                    "title": ann.title,
                    "content": ann.content,
                    "teacher_name": teacher.full_name,
                    "posted_at": ann.created_at.isoformat(),
                }
            )

        return announcements
