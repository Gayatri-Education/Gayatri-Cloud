"""Deterministic Mastery State Machine and Misconception Lifecycle."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import generate_uuid
from app.db.models.tutoring import CanonicalLearningState, LearningEvent, MisconceptionRecord


class CanonicalMasteryService:
    """Deterministic, rules-based student learning state and misconception manager."""

    @classmethod
    async def get_or_create_state(
        cls,
        session: AsyncSession,
        student_id: str,
        offering_id: str,
        concept_id: str,
    ) -> CanonicalLearningState:
        """Fetch existing concept mastery state or initialize a zero baseline."""
        stmt = select(CanonicalLearningState).where(
            CanonicalLearningState.student_id == student_id,
            CanonicalLearningState.offering_id == offering_id,
            CanonicalLearningState.concept_id == concept_id,
        )
        res = await session.execute(stmt)
        state = res.scalar_one_or_none()
        if not state:
            state = CanonicalLearningState(
                id=generate_uuid(),
                student_id=student_id,
                offering_id=offering_id,
                concept_id=concept_id,
                mastery_score=0.0,
                review_count=0,
                stability=1.0,
                last_tested_at=None,
            )
            session.add(state)
            await session.flush()
        return state

    @classmethod
    async def record_evidence(
        cls,
        session: AsyncSession,
        student_id: str,
        offering_id: str,
        concept_id: str,
        is_correct: bool,
        event_type: str = "comprehension_check",
        details: dict | None = None,
    ) -> CanonicalLearningState:
        """Deterministically update concept mastery score based on validated educational evidence."""
        state = await cls.get_or_create_state(session, student_id, offering_id, concept_id)
        now = datetime.now(UTC)

        # Deterministic formula: updates cannot be unilaterally forced by unvalidated LLM output
        if is_correct:
            increment = 0.20 * state.stability
            state.mastery_score = min(1.0, round(state.mastery_score + increment, 2))
            state.stability = min(2.5, round(state.stability * 1.1, 2))
        else:
            state.mastery_score = max(0.0, round(state.mastery_score - 0.15, 2))
            state.stability = max(0.5, round(state.stability * 0.8, 2))

        state.review_count += 1
        state.last_tested_at = now

        # Append-only Learning Event Audit Trail
        event = LearningEvent(
            id=generate_uuid(),
            student_id=student_id,
            offering_id=offering_id,
            concept_id=concept_id,
            event_type=event_type,
            payload_json=json.dumps(
                {
                    "is_correct": is_correct,
                    "new_mastery_score": state.mastery_score,
                    "stability": state.stability,
                    "review_count": state.review_count,
                    "details": details or {},
                }
            ),
        )
        session.add(event)

        # Automatic remediation of active misconceptions upon reaching mastery threshold (>= 0.70)
        if is_correct and state.mastery_score >= 0.70:
            m_stmt = select(MisconceptionRecord).where(
                MisconceptionRecord.student_id == student_id,
                MisconceptionRecord.offering_id == offering_id,
                MisconceptionRecord.concept_id == concept_id,
                MisconceptionRecord.status == "active",
            )
            misconceptions = list((await session.execute(m_stmt)).scalars().all())
            for m in misconceptions:
                m.status = "remediated"
                m.resolved_at = now

        await session.commit()
        await session.refresh(state)
        return state

    @classmethod
    async def log_misconception(
        cls,
        session: AsyncSession,
        student_id: str,
        offering_id: str,
        concept_id: str,
        description: str,
    ) -> MisconceptionRecord:
        """Record an active misconception diagnosed during tutoring dialogue."""
        now = datetime.now(UTC)
        record = MisconceptionRecord(
            id=generate_uuid(),
            student_id=student_id,
            offering_id=offering_id,
            concept_id=concept_id,
            description=description,
            status="active",
            detected_at=now,
            resolved_at=None,
        )
        session.add(record)

        event = LearningEvent(
            id=generate_uuid(),
            student_id=student_id,
            offering_id=offering_id,
            concept_id=concept_id,
            event_type="misconception_diagnosed",
            payload_json=json.dumps({"description": description}),
        )
        session.add(event)

        await session.commit()
        await session.refresh(record)
        return record

    @classmethod
    async def get_student_mastery_matrix(
        cls,
        session: AsyncSession,
        student_id: str,
        offering_id: str,
    ) -> list[CanonicalLearningState]:
        """Retrieve student's concept mastery vector for a given offering."""
        stmt = (
            select(CanonicalLearningState)
            .where(
                CanonicalLearningState.student_id == student_id,
                CanonicalLearningState.offering_id == offering_id,
            )
            .order_by(CanonicalLearningState.concept_id.asc())
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())
