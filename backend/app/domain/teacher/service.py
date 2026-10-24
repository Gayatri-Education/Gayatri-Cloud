"""Teacher and Academic Administration domain service.
Implements class rosters, 5-tier instruction cascade, class analytics,
intervention queues, and data-grounded copilot briefings with tenant isolation.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import TenantContext
from app.db.models.course import CourseEnrollment, CourseOffering, TeacherInstruction
from app.db.models.identity import UserAccount
from app.db.models.teacher import ClassAnnouncement, TeacherIntervention
from app.db.models.tutoring import (
    CanonicalLearningState,
    MisconceptionRecord,
)


class TeacherService:
    """Service orchestrating teacher capabilities and academic administration."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _verify_offering_access(
        self, context: TenantContext, offering_id: str
    ) -> CourseOffering:
        """Verify course offering exists and belongs to the caller's organization context."""
        stmt = select(CourseOffering).where(CourseOffering.id == offering_id)
        res = await self.session.execute(stmt)
        offering = res.scalar_one_or_none()

        if not offering:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course offering '{offering_id}' not found.",
            )

        if offering.organization_id != context.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied across tenant boundaries.",
            )

        return offering

    # =========================================================================
    # 1. Class Roster & Enrollment
    # =========================================================================

    async def get_roster(self, context: TenantContext, offering_id: str) -> list[dict[str, Any]]:
        """Retrieve class roster with student profiles and mastery progress."""
        offering = await self._verify_offering_access(context, offering_id)

        stmt = (
            select(CourseEnrollment, UserAccount)
            .join(UserAccount, CourseEnrollment.student_id == UserAccount.id)
            .where(
                CourseEnrollment.offering_id == offering.id,
                CourseEnrollment.status == "enrolled",
            )
            .order_by(UserAccount.full_name)
        )
        res = await self.session.execute(stmt)
        rows = res.all()

        roster = []
        for enrollment, student in rows:
            # Aggregate mastery for this student and offering
            mastery_stmt = select(func.avg(CanonicalLearningState.mastery_score)).where(
                CanonicalLearningState.student_id == student.id,
                CanonicalLearningState.offering_id == offering.id,
            )
            avg_mastery_res = await self.session.execute(mastery_stmt)
            avg_mastery = avg_mastery_res.scalar() or 0.0

            # Count unresolved misconceptions
            miscon_stmt = select(func.count(MisconceptionRecord.id)).where(
                MisconceptionRecord.student_id == student.id,
                MisconceptionRecord.offering_id == offering.id,
                MisconceptionRecord.status == "active",
            )
            miscon_res = await self.session.execute(miscon_stmt)
            miscon_count = miscon_res.scalar() or 0

            roster.append(
                {
                    "enrollment_id": enrollment.id,
                    "student_id": student.id,
                    "student_name": student.full_name,
                    "email": student.email,
                    "status": enrollment.status,
                    "enrolled_at": enrollment.created_at.isoformat(),
                    "average_mastery": round(float(avg_mastery), 2),
                    "active_misconceptions": miscon_count,
                }
            )

        return roster

    async def enroll_student(
        self, context: TenantContext, offering_id: str, student_id: str
    ) -> CourseEnrollment:
        """Enroll a student into a course offering."""
        offering = await self._verify_offering_access(context, offering_id)

        # Check student exists
        student_stmt = select(UserAccount).where(UserAccount.id == student_id)
        student_res = await self.session.execute(student_stmt)
        student = student_res.scalar_one_or_none()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student '{student_id}' not found.",
            )

        # Check existing enrollment
        existing_stmt = select(CourseEnrollment).where(
            CourseEnrollment.offering_id == offering.id,
            CourseEnrollment.student_id == student.id,
        )
        existing_res = await self.session.execute(existing_stmt)
        existing = existing_res.scalar_one_or_none()

        if existing:
            if existing.status == "enrolled":
                return existing
            existing.status = "enrolled"
            await self.session.commit()
            return existing

        enrollment = CourseEnrollment(
            offering_id=offering.id,
            student_id=student.id,
            status="enrolled",
        )
        self.session.add(enrollment)
        await self.session.commit()
        await self.session.refresh(enrollment)
        return enrollment

    async def unenroll_student(
        self, context: TenantContext, offering_id: str, student_id: str
    ) -> None:
        """Unenroll a student from a course offering."""
        offering = await self._verify_offering_access(context, offering_id)

        stmt = select(CourseEnrollment).where(
            CourseEnrollment.offering_id == offering.id,
            CourseEnrollment.student_id == student_id,
        )
        res = await self.session.execute(stmt)
        enrollment = res.scalar_one_or_none()

        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student enrollment record not found.",
            )

        enrollment.status = "dropped"
        await self.session.commit()

    # =========================================================================
    # 2. Class Analytics & Cohort Diagnostics
    # =========================================================================

    async def get_class_analytics(self, context: TenantContext, offering_id: str) -> dict[str, Any]:
        """Aggregate cohort mastery distribution, concept difficulty, and misconception clusters."""
        offering = await self._verify_offering_access(context, offering_id)

        # Get enrolled student IDs
        enrolled_stmt = select(CourseEnrollment.student_id).where(
            CourseEnrollment.offering_id == offering.id,
            CourseEnrollment.status == "enrolled",
        )
        enrolled_res = await self.session.execute(enrolled_stmt)
        student_ids = list(enrolled_res.scalars().all())

        total_students = len(student_ids)

        if total_students == 0:
            return {
                "total_students": 0,
                "average_mastery": 0.0,
                "mastery_distribution": {
                    "novice": 0,
                    "developing": 0,
                    "competent": 0,
                    "proficient": 0,
                    "master": 0,
                },
                "hardest_concepts": [],
                "misconception_clusters": [],
            }

        # Query all learning states for enrolled cohort
        states_stmt = select(CanonicalLearningState).where(
            CanonicalLearningState.student_id.in_(student_ids),
            CanonicalLearningState.offering_id == offering.id,
        )
        states_res = await self.session.execute(states_stmt)
        states = states_res.scalars().all()

        # Mastery Distribution
        distribution = {
            "novice": 0,
            "developing": 0,
            "competent": 0,
            "proficient": 0,
            "master": 0,
        }

        concept_scores: dict[str, list[float]] = {}
        student_masteries: dict[str, list[float]] = {s_id: [] for s_id in student_ids}

        for st in states:
            concept_scores.setdefault(st.concept_id, []).append(st.mastery_score)
            student_masteries[st.student_id].append(st.mastery_score)

        # Categorize each student by their mean score
        cohort_means = []
        for _s_id, scores in student_masteries.items():
            mean_score = sum(scores) / len(scores) if scores else 0.0
            cohort_means.append(mean_score)
            if mean_score >= 0.95:
                distribution["master"] += 1
            elif mean_score >= 0.80:
                distribution["proficient"] += 1
            elif mean_score >= 0.60:
                distribution["competent"] += 1
            elif mean_score >= 0.40:
                distribution["developing"] += 1
            else:
                distribution["novice"] += 1

        overall_avg = sum(cohort_means) / len(cohort_means) if cohort_means else 0.0

        # Hardest concepts (lowest average score)
        hardest = []
        for c_id, scores in concept_scores.items():
            avg_c = sum(scores) / len(scores) if scores else 0.0
            hardest.append(
                {
                    "concept_id": c_id,
                    "average_score": round(avg_c, 2),
                    "attempts": len(scores),
                }
            )
        hardest.sort(key=lambda x: x["average_score"])

        # Misconception clusters
        miscon_stmt = (
            select(
                MisconceptionRecord.concept_id,
                MisconceptionRecord.description,
                func.count(MisconceptionRecord.id).label("count"),
            )
            .where(
                MisconceptionRecord.student_id.in_(student_ids),
                MisconceptionRecord.offering_id == offering.id,
                MisconceptionRecord.status == "active",
            )
            .group_by(MisconceptionRecord.concept_id, MisconceptionRecord.description)
        )

        miscon_res = await self.session.execute(miscon_stmt)
        clusters = [
            {
                "concept_id": row[0],
                "description": row[1],
                "student_count": row[2],
            }
            for row in miscon_res.all()
        ]

        return {
            "total_students": total_students,
            "average_mastery": round(overall_avg, 2),
            "mastery_distribution": distribution,
            "hardest_concepts": hardest[:5],
            "misconception_clusters": clusters,
        }

    # =========================================================================
    # 3. Intervention Queue
    # =========================================================================

    async def get_intervention_queue(
        self, context: TenantContext, offering_id: str
    ) -> list[dict[str, Any]]:
        """Retrieve flagged learners requiring teacher intervention."""
        offering = await self._verify_offering_access(context, offering_id)

        stmt = (
            select(TeacherIntervention, UserAccount)
            .join(UserAccount, TeacherIntervention.student_id == UserAccount.id)
            .where(
                TeacherIntervention.offering_id == offering.id,
                TeacherIntervention.organization_id == context.organization_id,
                TeacherIntervention.status.in_(["PENDING", "ACKNOWLEDGED"]),
            )
            .order_by(TeacherIntervention.created_at.desc())
        )
        res = await self.session.execute(stmt)
        interventions = []

        for interv, student in res.all():
            interventions.append(
                {
                    "id": interv.id,
                    "student_id": student.id,
                    "student_name": student.full_name,
                    "concept_id": interv.concept_id,
                    "severity": interv.severity,
                    "reason": interv.reason,
                    "status": interv.status,
                    "created_at": interv.created_at.isoformat(),
                    "resolution_notes": interv.resolution_notes,
                }
            )

        return interventions

    async def acknowledge_intervention(
        self,
        context: TenantContext,
        intervention_id: str,
        resolution_notes: str | None = None,
        resolve: bool = False,
    ) -> TeacherIntervention:
        """Acknowledge or resolve an active student intervention."""
        stmt = select(TeacherIntervention).where(
            TeacherIntervention.id == intervention_id,
            TeacherIntervention.organization_id == context.organization_id,
        )
        res = await self.session.execute(stmt)
        interv = res.scalar_one_or_none()

        if not interv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Intervention record not found.",
            )

        interv.status = "RESOLVED" if resolve else "ACKNOWLEDGED"
        interv.acknowledged_by = context.user.id
        interv.acknowledged_at = datetime.now(UTC)
        if resolution_notes:
            interv.resolution_notes = resolution_notes

        await self.session.commit()
        await self.session.refresh(interv)
        return interv

    # =========================================================================
    # 4. Teacher Copilot Diagnostic Briefings
    # =========================================================================

    async def generate_copilot_briefing(
        self, context: TenantContext, offering_id: str
    ) -> dict[str, Any]:
        """Generate empirical, evidence-grounded instructional briefing citing uncertainty."""
        analytics = await self.get_class_analytics(context, offering_id)
        total = analytics["total_students"]

        if total == 0:
            return {
                "summary": "No active students enrolled in this offering yet.",
                "evidence_sources": ["0 enrolled learners"],
                "confidence_score": 1.0,
                "bottleneck_concepts": [],
                "suggested_actions": [
                    "Enroll students into offering to initiate learning tracking."
                ],
                "requires_teacher_confirmation": True,
            }

        hardest = analytics["hardest_concepts"]
        clusters = analytics["misconception_clusters"]

        top_struggle = hardest[0]["concept_id"] if hardest else "Core Concepts"
        struggle_count = (
            analytics["mastery_distribution"]["novice"]
            + analytics["mastery_distribution"]["developing"]
        )

        evidence = [
            f"{total} enrolled learners analyzed",
            f"{struggle_count} learners currently below 60% mastery threshold",
        ]
        if clusters:
            evidence.append(
                f"Cluster: {clusters[0]['student_count']} learners share misconception '{clusters[0]['description']}'"
            )

        actions = [
            f"Launch a targeted Socratic review on concept '{top_struggle}'.",
            "Set a teacher directive in the cascade prioritizing practice-first pedagogy.",
        ]
        if clusters:
            actions.append(
                f"Conduct group remediation for identified misconception '{clusters[0]['description']}'."
            )

        confidence = 0.88 if total >= 3 else 0.65

        return {
            "summary": f"{struggle_count} of {total} learners show learning gaps in '{top_struggle}'.",
            "evidence_sources": evidence,
            "confidence_score": confidence,
            "uncertainty_note": (
                "Based on available evaluation and mastery turns. Smaller sample sizes increase variance."
                if total < 5
                else "High confidence based on continuous turn evidence."
            ),
            "bottleneck_concepts": [h["concept_id"] for h in hardest[:3]],
            "suggested_actions": actions,
            "requires_teacher_confirmation": True,
        }

    # =========================================================================
    # 5. Teacher Directive Cascade Management
    # =========================================================================

    async def create_instruction(
        self,
        context: TenantContext,
        course_id: str,
        tier: str,
        directive_text: str,
        student_id: str | None = None,
        class_group_id: str | None = None,
        priority: int = 1,
        expires_at: datetime | None = None,
    ) -> TeacherInstruction:
        """Register a teacher instruction into the 5-tier cascade."""
        instruction = TeacherInstruction(
            organization_id=context.organization_id,
            teacher_id=context.user.id,
            course_id=course_id,
            tier=tier.upper(),
            directive_text=directive_text,
            student_id=student_id,
            class_group_id=class_group_id,
            priority=priority,
            expires_at=expires_at,
            is_active=True,
        )
        self.session.add(instruction)
        await self.session.commit()
        await self.session.refresh(instruction)
        return instruction

    async def list_instructions(
        self, context: TenantContext, course_id: str | None = None
    ) -> list[TeacherInstruction]:
        """List active teacher instructions ordered by priority descending."""
        filters = [
            TeacherInstruction.organization_id == context.organization_id,
            TeacherInstruction.is_active.is_(True),
        ]
        if course_id:
            filters.append(TeacherInstruction.course_id == course_id)
        stmt = (
            select(TeacherInstruction)
            .where(*filters)
            .order_by(TeacherInstruction.priority.desc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def deactivate_instruction(self, context: TenantContext, instruction_id: str) -> None:
        """Deactivate a teacher instruction."""
        stmt = select(TeacherInstruction).where(
            TeacherInstruction.id == instruction_id,
            TeacherInstruction.organization_id == context.organization_id,
        )
        res = await self.session.execute(stmt)
        inst = res.scalar_one_or_none()
        if not inst:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instruction not found.",
            )
        inst.is_active = False
        await self.session.commit()

    # =========================================================================
    # 6. Class Announcements
    # =========================================================================

    async def create_announcement(
        self,
        context: TenantContext,
        offering_id: str,
        title: str,
        content: str,
    ) -> ClassAnnouncement:
        """Publish a notice to a course offering."""
        offering = await self._verify_offering_access(context, offering_id)

        announcement = ClassAnnouncement(
            organization_id=context.organization_id,
            offering_id=offering.id,
            teacher_id=context.user.id,
            title=title,
            content=content,
        )
        self.session.add(announcement)
        await self.session.commit()
        await self.session.refresh(announcement)
        return announcement

    async def get_announcements(
        self, context: TenantContext, offering_id: str
    ) -> list[ClassAnnouncement]:
        """List announcements for a course offering."""
        offering = await self._verify_offering_access(context, offering_id)

        stmt = (
            select(ClassAnnouncement)
            .where(
                ClassAnnouncement.offering_id == offering.id,
                ClassAnnouncement.organization_id == context.organization_id,
            )
            .order_by(ClassAnnouncement.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
