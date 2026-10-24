"""Export all database models for SQLAlchemy metadata and Alembic."""

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, generate_uuid
from app.db.models.ai import (
    AIExecutionUsage,
    ModelBenchmarkRun,
    ModelPolicy,
    ProviderConnection,
    ProviderModelSnapshot,
)
from app.db.models.billing import (
    FeePayment,
    InstitutionFee,
    InvoiceReceipt,
    PaymentTransaction,
    Subscription,
    SubscriptionPlan,
)
from app.db.models.course import (
    ClassGroup,
    ContentChunk,
    ContentSource,
    Course,
    CourseEnrollment,
    CourseOffering,
    CourseVersion,
    TeacherInstruction,
    TeachingAssignment,
)
from app.db.models.events import ApplicationEvent, EventOutbox
from app.db.models.identity import AuthIdentity, SessionDevice, UserAccount
from app.db.models.organization import (
    GuardianRelationship,
    Invitation,
    Membership,
    Organization,
    OrganizationDomain,
    RoleAssignment,
)
from app.db.models.teacher import ClassAnnouncement, TeacherIntervention
from app.db.models.tutoring import (
    Assessment,
    AssessmentAttempt,
    AssessmentResponse,
    CanonicalLearningState,
    ConversationTurn,
    LearningEvent,
    MisconceptionRecord,
    TutorSession,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
    "generate_uuid",
    "UserAccount",
    "AuthIdentity",
    "SessionDevice",
    "Organization",
    "OrganizationDomain",
    "Membership",
    "RoleAssignment",
    "Invitation",
    "GuardianRelationship",
    "Course",
    "CourseVersion",
    "CourseOffering",
    "ClassGroup",
    "CourseEnrollment",
    "TeachingAssignment",
    "TeacherInstruction",
    "ClassAnnouncement",
    "TeacherIntervention",
    "ContentSource",
    "ContentChunk",
    "TutorSession",
    "ConversationTurn",
    "Assessment",
    "AssessmentAttempt",
    "AssessmentResponse",
    "LearningEvent",
    "CanonicalLearningState",
    "MisconceptionRecord",
    "ProviderConnection",
    "ProviderModelSnapshot",
    "ModelPolicy",
    "ModelBenchmarkRun",
    "AIExecutionUsage",
    "ApplicationEvent",
    "EventOutbox",
    "SubscriptionPlan",
    "Subscription",
    "InstitutionFee",
    "FeePayment",
    "PaymentTransaction",
    "InvoiceReceipt",
]
