"""Tutor, Conversation, Assessment, and Learning State models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, generate_uuid


class TutorSession(Base, TimestampMixin):
    """An interactive tutoring dialogue session."""

    __tablename__ = "tutor_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    offering_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("course_offerings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="active", nullable=False
    )  # active, completed, abandoned
    tutoring_mode: Mapped[str] = mapped_column(String(50), default="socratic", nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    turns: Mapped[list[ConversationTurn]] = relationship(
        "ConversationTurn", back_populates="session", cascade="all, delete-orphan"
    )


class ConversationTurn(Base, TimestampMixin):
    """Individual prompt or assistant response in a tutoring dialogue."""

    __tablename__ = "conversation_turns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tutor_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # user, assistant, system, tool
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    provider_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    token_usage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    session: Mapped[TutorSession] = relationship("TutorSession", back_populates="turns")


class Assessment(Base, TimestampMixin):
    """Exams, quizzes, and adaptive assessments."""

    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    offering_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("course_offerings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    assessment_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # MCQ, NUMERICAL, SUBJECTIVE, CODING, ADAPTIVE, TIMED_EXAM
    total_points: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    attempts: Mapped[list[AssessmentAttempt]] = relationship(
        "AssessmentAttempt", back_populates="assessment", cascade="all, delete-orphan"
    )


class AssessmentAttempt(Base, TimestampMixin):
    """Learner's submission attempt for an assessment."""

    __tablename__ = "assessment_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="in_progress", nullable=False
    )  # in_progress, submitted, graded
    total_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assessment: Mapped[Assessment] = relationship("Assessment", back_populates="attempts")
    responses: Mapped[list[AssessmentResponse]] = relationship(
        "AssessmentResponse", back_populates="attempt", cascade="all, delete-orphan"
    )


class AssessmentResponse(Base, TimestampMixin):
    """Answer provided for a question within an attempt."""

    __tablename__ = "assessment_responses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    attempt_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("assessment_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[str] = mapped_column(String(100), nullable=False)
    student_response: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluated_by: Mapped[str] = mapped_column(
        String(50), default="deterministic", nullable=False
    )  # deterministic, ai_evaluator, teacher

    attempt: Mapped[AssessmentAttempt] = relationship(
        "AssessmentAttempt", back_populates="responses"
    )


class LearningEvent(Base, TimestampMixin):
    """Append-only evidence log of student interactions and learning progress."""

    __tablename__ = "learning_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    offering_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("course_offerings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    concept_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # hint_requested, question_answered, concept_mastered
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class CanonicalLearningState(Base, TimestampMixin):
    """Authoritative Student Learning Record (SLR) concept mastery state."""

    __tablename__ = "canonical_learning_states"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "offering_id", "concept_id", name="uq_student_concept_state"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    offering_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("course_offerings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    concept_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    mastery_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0.0 to 1.0
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stability: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MisconceptionRecord(Base, TimestampMixin):
    """Identified misconception for intervention and review."""

    __tablename__ = "misconception_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    offering_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("course_offerings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    concept_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="active", nullable=False
    )  # active, remediated, dismissed
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
