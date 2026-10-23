"""Course, Curriculum, and Learning Material models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, generate_uuid


class Course(Base, TimestampMixin, SoftDeleteMixin):
    """Generic curriculum-independent course container."""

    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_global: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    versions: Mapped[list[CourseVersion]] = relationship(
        "CourseVersion", back_populates="course", cascade="all, delete-orphan"
    )


class CourseVersion(Base, TimestampMixin):
    """Immutable versioned snapshot of course curriculum and material."""

    __tablename__ = "course_versions"
    __table_args__ = (UniqueConstraint("course_id", "version_tag", name="uq_course_version_tag"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    course_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_tag: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "v1.0.0"
    status: Mapped[str] = mapped_column(
        String(50), default="draft", nullable=False
    )  # draft, in_review, published, archived
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    course: Mapped[Course] = relationship("Course", back_populates="versions")
    sources: Mapped[list[ContentSource]] = relationship(
        "ContentSource", back_populates="course_version", cascade="all, delete-orphan"
    )


class CourseOffering(Base, TimestampMixin):
    """An active cohort or term deployment of a specific course version."""

    __tablename__ = "course_offerings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    course_version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("course_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    term: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)

    enrollments: Mapped[list[CourseEnrollment]] = relationship(
        "CourseEnrollment", back_populates="offering", cascade="all, delete-orphan"
    )
    classes: Mapped[list[ClassGroup]] = relationship(
        "ClassGroup", back_populates="offering", cascade="all, delete-orphan"
    )


class ClassGroup(Base, TimestampMixin):
    """Section or class within an offering."""

    __tablename__ = "class_groups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    offering_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("course_offerings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    offering: Mapped[CourseOffering] = relationship("CourseOffering", back_populates="classes")


class CourseEnrollment(Base, TimestampMixin):
    """Learner enrollment in an offering."""

    __tablename__ = "course_enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "offering_id", name="uq_student_offering_enrollment"),
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
    status: Mapped[str] = mapped_column(String(50), default="enrolled", nullable=False)

    offering: Mapped[CourseOffering] = relationship("CourseOffering", back_populates="enrollments")


class TeachingAssignment(Base, TimestampMixin):
    """Teacher assigned to an offering or class."""

    __tablename__ = "teaching_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    teacher_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    offering_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("course_offerings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    class_group_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("class_groups.id", ondelete="SET NULL"), nullable=True, index=True
    )


class TeacherInstruction(Base, TimestampMixin):
    """5-tier teacher directive influencing tutoring and pedagogical behavior."""

    __tablename__ = "teacher_instructions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    teacher_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    class_group_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=True, index=True
    )
    student_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=True, index=True
    )
    tier: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # ORG, COURSE, CLASS, STUDENT, SESSION
    priority: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )  # 1 (low) to 5 (urgent)
    directive_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ContentSource(Base, TimestampMixin):
    """Ingested curriculum file or document stored in private S3."""

    __tablename__ = "content_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    course_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("course_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    s3_uri: Mapped[str] = mapped_column(String(1000), nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    ingestion_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)

    course_version: Mapped[CourseVersion] = relationship("CourseVersion", back_populates="sources")
    chunks: Mapped[list[ContentChunk]] = relationship(
        "ContentChunk", back_populates="source", cascade="all, delete-orphan"
    )


class ContentChunk(Base, TimestampMixin):
    """Parsed, sanitized text chunk indexed for course-scoped RAG."""

    __tablename__ = "content_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("content_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_header: Mapped[str | None] = mapped_column(String(255), nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    source: Mapped[ContentSource] = relationship("ContentSource", back_populates="chunks")
