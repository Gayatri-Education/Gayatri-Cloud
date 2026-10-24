"""Assessment and Evaluation service coordinating attempts, grading, and mastery updates."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import RoleEnum, TenantContext
from app.db.base import generate_uuid
from app.db.models.course import CourseEnrollment, CourseOffering
from app.db.models.tutoring import (
    Assessment,
    AssessmentAttempt,
    AssessmentResponse,
)
from app.domain.assessment.deterministic import DeterministicGrader
from app.domain.assessment.evaluators import CodingEvaluator, SubjectiveEvaluator
from app.domain.assessment.models import (
    AssessmentItem,
    AssessmentTypeEnum,
    ItemGradingResult,
    QuestionType,
    Rubric,
    RubricCriterion,
    SubmissionSummary,
)
from app.domain.assessment.sanitizer import AssessmentSanitizer
from app.domain.tutoring.mastery import CanonicalMasteryService


class CreateAssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    offering_id: str
    title: str
    assessment_type: AssessmentTypeEnum = AssessmentTypeEnum.MCQ
    total_points: float = 100.0
    time_limit_minutes: int | None = None
    passing_score: float = 70.0
    items: list[dict[str, Any]] = Field(default_factory=list)


class AutosaveAttemptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft_answers: dict[str, Any] = Field(default_factory=dict)


class SubmitAttemptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answers: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None


class TeacherOverrideItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    response_id: str
    override_score: float
    comment: str | None = None


class TeacherOverrideRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overrides: list[TeacherOverrideItem] = Field(default_factory=list)


class AssessmentService:
    """Coordinates assessment authoring, student attempts, automated evaluation, and mastery."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_assessment(
        self, context: TenantContext, req: CreateAssessmentRequest
    ) -> Assessment:
        """Create a new course assessment (Teacher or Admin only)."""
        if not context.has_role(
            RoleEnum.TEACHER.value, RoleEnum.ORG_ADMIN.value, RoleEnum.SUPER_ADMIN.value
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers and administrators can create assessments.",
            )

        # Verify offering belongs to tenant if org is bound
        offering = await self.db.get(CourseOffering, req.offering_id)
        if not offering:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course offering not found.",
            )

        assessment = Assessment(
            id=generate_uuid(),
            offering_id=req.offering_id,
            title=req.title,
            assessment_type=req.assessment_type.value,
            total_points=req.total_points,
            time_limit_minutes=req.time_limit_minutes,
            passing_score=req.passing_score,
            content_json=json.dumps(req.items),
            is_published=False,
        )
        self.db.add(assessment)
        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    async def publish_assessment(self, context: TenantContext, assessment_id: str) -> Assessment:
        """Publish an assessment to make it available to enrolled students."""
        if not context.has_role(
            RoleEnum.TEACHER.value, RoleEnum.ORG_ADMIN.value, RoleEnum.SUPER_ADMIN.value
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers and administrators can publish assessments.",
            )

        assessment = await self.db.get(Assessment, assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found.",
            )

        offering = await self.db.get(CourseOffering, assessment.offering_id)
        if (
            offering
            and offering.organization_id
            and offering.organization_id != context.organization_id
            and not context.user.is_super_admin
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: assessment belongs to another organization.",
            )

        assessment.is_published = True
        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    async def get_assessment(self, context: TenantContext, assessment_id: str) -> dict[str, Any]:
        """Retrieve assessment payload. Enforces anti-leakage sanitization for students."""
        assessment = await self.db.get(Assessment, assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found.",
            )

        offering = await self.db.get(CourseOffering, assessment.offering_id)
        if (
            offering
            and offering.organization_id
            and offering.organization_id != context.organization_id
            and not context.user.is_super_admin
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: assessment belongs to another organization.",
            )

        is_teacher_or_admin = context.has_role(
            RoleEnum.TEACHER.value, RoleEnum.ORG_ADMIN.value, RoleEnum.SUPER_ADMIN.value
        )

        items_raw = json.loads(assessment.content_json or "[]")

        if is_teacher_or_admin:
            return {
                "id": assessment.id,
                "offering_id": assessment.offering_id,
                "title": assessment.title,
                "assessment_type": assessment.assessment_type,
                "total_points": assessment.total_points,
                "time_limit_minutes": assessment.time_limit_minutes,
                "passing_score": assessment.passing_score,
                "is_published": assessment.is_published,
                "items": items_raw,
            }

        # Student access verification
        if not assessment.is_published:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Assessment is not published.",
            )

        # Verify student enrollment
        stmt = select(CourseEnrollment).where(
            CourseEnrollment.offering_id == assessment.offering_id,
            CourseEnrollment.student_id == context.user.id,
            CourseEnrollment.status.in_(["enrolled", "active"]),
        )
        res = await self.db.execute(stmt)
        if not res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be actively enrolled in this course to view this assessment.",
            )

        # Sanitize items to ensure ZERO answer leakage
        sanitized = AssessmentSanitizer.sanitize_assessment_for_student(
            {
                "id": assessment.id,
                "offering_id": assessment.offering_id,
                "title": assessment.title,
                "assessment_type": assessment.assessment_type,
                "total_points": assessment.total_points,
                "time_limit_minutes": assessment.time_limit_minutes,
                "passing_score": assessment.passing_score,
                "is_published": assessment.is_published,
            },
            items_raw,
        )

        # Absolute verification of anti-leakage
        if not AssessmentSanitizer.verify_no_leakage(sanitized):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Anti-leakage sanitization check failed.",
            )

        return sanitized

    async def start_attempt(
        self,
        context: TenantContext,
        assessment_id: str,
        time_limit_minutes: int | None = None,
    ) -> AssessmentAttempt:
        """Start a new assessment attempt for the current student."""
        assessment = await self.db.get(Assessment, assessment_id)
        if not assessment or not assessment.is_published:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found or not published.",
            )

        offering = await self.db.get(CourseOffering, assessment.offering_id)
        if (
            offering
            and offering.organization_id
            and offering.organization_id != context.organization_id
            and not context.user.is_super_admin
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: assessment belongs to another organization.",
            )

        # Verify enrollment
        stmt = select(CourseEnrollment).where(
            CourseEnrollment.offering_id == assessment.offering_id,
            CourseEnrollment.student_id == context.user.id,
            CourseEnrollment.status.in_(["enrolled", "active"]),
        )
        res = await self.db.execute(stmt)
        if not res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Must be enrolled in course offering to attempt assessment.",
            )

        # Determine effective time limit
        effective_limit = (
            time_limit_minutes if time_limit_minutes is not None else assessment.time_limit_minutes
        )

        attempt = AssessmentAttempt(
            id=generate_uuid(),
            assessment_id=assessment.id,
            student_id=context.user.id,
            status="in_progress",
            started_at=datetime.now(UTC),
            time_limit_minutes=effective_limit,
        )
        self.db.add(attempt)
        await self.db.commit()
        await self.db.refresh(attempt)
        return attempt

    async def autosave_attempt(
        self,
        context: TenantContext,
        attempt_id: str,
        draft_answers: dict[str, Any],
    ) -> dict[str, Any]:
        """Autosave intermediate student answers while attempt is in-progress."""
        attempt = await self.db.get(AssessmentAttempt, attempt_id)
        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attempt not found.",
            )

        assessment = await self.db.get(Assessment, attempt.assessment_id)
        if assessment:
            offering = await self.db.get(CourseOffering, assessment.offering_id)
            if (
                offering
                and offering.organization_id
                and offering.organization_id != context.organization_id
                and not context.user.is_super_admin
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: attempt belongs to another organization.",
                )

        if attempt.student_id != context.user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this attempt.",
            )

        if attempt.status != "in_progress":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot autosave attempt in '{attempt.status}' state.",
            )

        # Check time expiration (with 2-minute grace period)
        if attempt.time_limit_minutes and attempt.started_at:
            started = (
                attempt.started_at
                if attempt.started_at.tzinfo
                else attempt.started_at.replace(tzinfo=UTC)
            )
            deadline = started + timedelta(minutes=attempt.time_limit_minutes + 2)
            if datetime.now(UTC) > deadline:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assessment time limit has expired.",
                )

        attempt.draft_answers_json = json.dumps(draft_answers)
        await self.db.commit()
        return {"status": "saved", "attempt_id": attempt.id}

    async def submit_attempt(
        self,
        context: TenantContext,
        attempt_id: str,
        answers: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> SubmissionSummary:
        """Submit assessment attempt, execute evaluators, and update canonical mastery."""
        attempt = await self.db.get(AssessmentAttempt, attempt_id)
        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attempt not found.",
            )

        assessment = await self.db.get(Assessment, attempt.assessment_id)
        if assessment:
            offering = await self.db.get(CourseOffering, assessment.offering_id)
            if (
                offering
                and offering.organization_id
                and offering.organization_id != context.organization_id
                and not context.user.is_super_admin
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: attempt belongs to another organization.",
                )

        if attempt.student_id != context.user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this attempt.",
            )

        # Idempotency check: if already submitted or graded, return cached summary
        if attempt.status in ("submitted", "graded"):
            if attempt.grading_summary_json:
                data = json.loads(attempt.grading_summary_json)
                return SubmissionSummary(
                    total_score=data["total_score"],
                    max_score=data["max_score"],
                    percentage=data["percentage"],
                    passed=data["passed"],
                    item_results={
                        k: ItemGradingResult(**v) for k, v in data.get("item_results", {}).items()
                    },
                    weak_concepts=data.get("weak_concepts", []),
                    misconceptions_flagged=data.get("misconceptions_flagged", []),
                    overall_feedback=data.get("overall_feedback", ""),
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Attempt has already been submitted.",
            )

        assessment = await self.db.get(Assessment, attempt.assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment definition missing.",
            )

        offering = await self.db.get(CourseOffering, assessment.offering_id)
        if (
            offering
            and offering.organization_id
            and offering.organization_id != context.organization_id
            and not context.user.is_super_admin
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: attempt belongs to another organization.",
            )

        # Parse raw assessment items
        items_raw = json.loads(assessment.content_json or "[]")
        items: list[AssessmentItem] = []
        for raw in items_raw:
            rubric_obj = None
            if raw.get("rubric"):
                rub_data = raw["rubric"]
                crit_list = [RubricCriterion(**c) for c in rub_data.get("criteria", [])]
                rubric_obj = Rubric(
                    rubric_id=rub_data.get("rubric_id", "rubric_custom"),
                    title=rub_data.get("title", "Rubric"),
                    description=rub_data.get("description", ""),
                    criteria=crit_list,
                )

            item = AssessmentItem(
                id=raw["id"],
                item_type=QuestionType(raw.get("item_type", "MCQ")),
                question_text=raw.get("question_text", ""),
                concept_id=raw.get("concept_id", "general"),
                max_marks=float(raw.get("max_marks", 4.0)),
                difficulty=int(raw.get("difficulty", 1)),
                options=raw.get("options"),
                correct_answer=raw.get("correct_answer"),
                expected_unit=raw.get("expected_unit"),
                tolerance_pct=float(raw.get("tolerance_pct", 2.0)),
                rubric=rubric_obj,
                test_cases=raw.get("test_cases"),
                solution_code=raw.get("solution_code"),
                explanation=raw.get("explanation"),
            )
            items.append(item)

        total_score = 0.0
        total_max_score = 0.0
        item_results: dict[str, ItemGradingResult] = {}
        concept_scores: dict[str, list[float]] = {}
        flagged_misconceptions: list[str] = []

        # Evaluate each question
        for item in items:
            student_ans = answers.get(item.id)
            if item.item_type == QuestionType.MCQ:
                is_corr, frac, fb = DeterministicGrader.grade_mcq(
                    student_ans, str(item.correct_answer or ""), item.options
                )
                sc = round(frac * item.max_marks, 2)
                res = ItemGradingResult(
                    item_id=item.id,
                    student_answer=student_ans,
                    is_correct=is_corr,
                    score=sc,
                    max_marks=item.max_marks,
                    percentage=round(frac * 100.0, 2),
                    feedback=fb,
                    ai_graded=False,
                )
            elif item.item_type == QuestionType.BOOLEAN:
                is_corr, frac, fb = DeterministicGrader.grade_boolean(
                    student_ans, item.correct_answer
                )
                sc = round(frac * item.max_marks, 2)
                res = ItemGradingResult(
                    item_id=item.id,
                    student_answer=student_ans,
                    is_correct=is_corr,
                    score=sc,
                    max_marks=item.max_marks,
                    percentage=round(frac * 100.0, 2),
                    feedback=fb,
                    ai_graded=False,
                )
            elif item.item_type == QuestionType.NUMERICAL:
                is_corr, frac, fb = DeterministicGrader.grade_numerical(
                    student_ans,
                    item.correct_answer,
                    item.tolerance_pct,
                    item.expected_unit,
                )
                sc = round(frac * item.max_marks, 2)
                res = ItemGradingResult(
                    item_id=item.id,
                    student_answer=student_ans,
                    is_correct=is_corr,
                    score=sc,
                    max_marks=item.max_marks,
                    percentage=round(frac * 100.0, 2),
                    feedback=fb,
                    ai_graded=False,
                )
            elif item.item_type == QuestionType.CODING:
                res = CodingEvaluator.evaluate(item, str(student_ans or ""))
            else:
                # Subjective rubric evaluation
                res = SubjectiveEvaluator.evaluate(item, student_ans, item.rubric)

            item_results[item.id] = res
            total_score += res.score
            total_max_score += res.max_marks

            concept_scores.setdefault(item.concept_id, []).append(
                res.score / max(res.max_marks, 1e-4)
            )
            if res.misconception_code:
                flagged_misconceptions.append(res.misconception_code)

            # Persist AssessmentResponse record
            resp_record = AssessmentResponse(
                id=generate_uuid(),
                attempt_id=attempt.id,
                question_id=item.id,
                student_response=str(student_ans or ""),
                score=res.score,
                max_score=res.max_marks,
                is_correct=res.is_correct,
                feedback_text=res.feedback,
                evaluated_by="ai_evaluator" if res.ai_graded else "deterministic",
                criterion_scores_json=json.dumps(res.criterion_scores)
                if res.criterion_scores
                else None,
            )
            self.db.add(resp_record)

        overall_percentage = (
            (total_score / max(total_max_score, 1e-4)) * 100.0 if total_max_score > 0 else 0.0
        )
        passed = overall_percentage >= assessment.passing_score

        weak_concepts = [
            cid for cid, sc_list in concept_scores.items() if (sum(sc_list) / len(sc_list)) < 0.70
        ]

        summary = SubmissionSummary(
            total_score=round(total_score, 2),
            max_score=round(total_max_score, 2),
            percentage=round(overall_percentage, 2),
            passed=passed,
            item_results=item_results,
            weak_concepts=weak_concepts,
            misconceptions_flagged=list(set(flagged_misconceptions)),
            overall_feedback="Assessment passed with strong proficiency."
            if passed
            else "Assessment completed. Focus review on weak concepts identified.",
        )

        # Update attempt record
        attempt.status = "graded"
        attempt.total_score = total_score
        attempt.submitted_at = datetime.now(UTC)
        attempt.idempotency_key = idempotency_key
        attempt.grading_summary_json = json.dumps(summary.to_dict())

        # Update canonical student mastery for each tested concept
        for cid, sc_list in concept_scores.items():
            avg_fraction = sum(sc_list) / len(sc_list)
            is_concept_passed = avg_fraction >= 0.70
            await CanonicalMasteryService.record_evidence(
                session=self.db,
                student_id=attempt.student_id,
                offering_id=assessment.offering_id,
                concept_id=cid,
                is_correct=is_concept_passed,
                event_type="assessment_submitted",
                details={"attempt_id": attempt.id, "score_fraction": avg_fraction},
            )

        await self.db.commit()
        await self.db.refresh(attempt)
        return summary

    async def teacher_override(
        self,
        context: TenantContext,
        attempt_id: str,
        req: TeacherOverrideRequest,
    ) -> AssessmentAttempt:
        """Allow a teacher or admin to manually adjust question scores and comments."""
        if not context.has_role(
            RoleEnum.TEACHER.value, RoleEnum.ORG_ADMIN.value, RoleEnum.SUPER_ADMIN.value
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers and administrators can override grades.",
            )

        attempt = await self.db.get(AssessmentAttempt, attempt_id)
        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attempt not found.",
            )

        assessment = await self.db.get(Assessment, attempt.assessment_id)
        if assessment:
            offering = await self.db.get(CourseOffering, assessment.offering_id)
            if (
                offering
                and offering.organization_id
                and offering.organization_id != context.organization_id
                and not context.user.is_super_admin
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: attempt belongs to another organization.",
                )

        # Apply overrides
        stmt = select(AssessmentResponse).where(AssessmentResponse.attempt_id == attempt.id)
        res = await self.db.execute(stmt)
        responses = {r.id: r for r in res.scalars().all()}

        total_adjusted_score = 0.0
        for ovr in req.overrides:
            resp = responses.get(ovr.response_id)
            if resp:
                resp.teacher_override_score = ovr.override_score
                resp.teacher_override_comment = ovr.comment
                resp.score = ovr.override_score
                resp.is_correct = ovr.override_score >= (resp.max_score * 0.70)
                resp.evaluated_by = "teacher"

        # Recalculate total score
        for resp in responses.values():
            total_adjusted_score += resp.score or 0.0

        attempt.total_score = total_adjusted_score
        await self.db.commit()
        await self.db.refresh(attempt)
        return attempt
