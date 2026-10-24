"""Data Subject Rights: Export, Retention and Account Deletion Hardening.
Enforces GDPR / FERPA compliance, cascading session invalidation, and statutory accounting legal holds (RQ-027, DEC-C27).
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import TenantContext
from app.db.models.billing import FeePayment, Subscription
from app.db.models.course import CourseEnrollment
from app.db.models.identity import SessionDevice, UserAccount
from app.db.models.organization import Membership, RoleAssignment
from app.db.models.security import AccountDeletionRequest, SecurityAuditLog
from app.db.models.tutoring import AssessmentAttempt, TutorSession

logger = logging.getLogger(__name__)


class DeletionService:
    """Handles personal data export, deletion requests, cascading revocation, and statutory retention."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log_security_event(
        self,
        user_id: str,
        action: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        status_code: str = "success",
        details: str | None = None,
    ) -> SecurityAuditLog:
        """Record an immutable security and privacy audit log."""
        log_entry = SecurityAuditLog(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status_code,
            details=details,
        )
        self.session.add(log_entry)
        await self.session.flush()
        return log_entry

    async def generate_user_data_export(
        self,
        context: TenantContext,
        target_user_id: str,
    ) -> dict[str, Any]:
        """Generate a complete, machine-readable JSON archive of user account data (GDPR Art. 20)."""
        # Authorization: user themselves or super admin
        if context.user.id != target_user_id and "SUPER_ADMIN" not in context.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: cannot export another user's private data.",
            )

        user_stmt = select(UserAccount).where(UserAccount.id == target_user_id)
        u_res = await self.session.execute(user_stmt)
        user = u_res.scalar_one_or_none()
        if not user or user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{target_user_id}' not found.",
            )

        # 1. Memberships and Roles
        m_stmt = (
            select(Membership, RoleAssignment)
            .outerjoin(RoleAssignment, Membership.id == RoleAssignment.membership_id)
            .where(Membership.user_id == target_user_id)
        )
        m_res = await self.session.execute(m_stmt)
        memberships_data = []
        for row in m_res.all():
            m = row[0]
            r = row[1]
            memberships_data.append(
                {
                    "organization_id": m.organization_id,
                    "membership_id": m.id,
                    "status": m.status,
                    "role": r.role if r else "MEMBER",
                    "joined_at": m.created_at.isoformat(),
                }
            )

        # 2. Course Enrollments
        e_stmt = select(CourseEnrollment).where(CourseEnrollment.student_id == target_user_id)
        e_res = await self.session.execute(e_stmt)
        enrollments_data = [
            {
                "enrollment_id": e.id,
                "offering_id": e.offering_id,
                "status": e.status,
                "enrolled_at": e.created_at.isoformat(),
            }
            for e in e_res.scalars().all()
        ]

        # 3. Assessment Attempts
        a_stmt = select(AssessmentAttempt).where(AssessmentAttempt.student_id == target_user_id)
        a_res = await self.session.execute(a_stmt)
        attempts_data = [
            {
                "attempt_id": a.id,
                "assessment_id": a.assessment_id,
                "status": a.status,
                "score": float(a.score) if a.score is not None else None,
                "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
            }
            for a in a_res.scalars().all()
        ]

        # 4. Tutoring Sessions
        t_stmt = select(TutorSession).where(TutorSession.student_id == target_user_id)
        t_res = await self.session.execute(t_stmt)
        sessions_data = [
            {
                "session_id": t.id,
                "course_id": t.course_id,
                "status": t.status,
                "created_at": t.created_at.isoformat(),
            }
            for t in t_res.scalars().all()
        ]

        now = datetime.now(UTC)
        export_payload = {
            "export_version": "1.0",
            "exported_at": now.isoformat(),
            "user_profile": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "created_at": user.created_at.isoformat(),
                "is_verified": user.is_verified,
            },
            "memberships": memberships_data,
            "enrollments": enrollments_data,
            "assessment_attempts": attempts_data,
            "tutoring_sessions": sessions_data,
        }

        # SHA-256 Checksum
        serialized = json.dumps(export_payload, sort_keys=True)
        export_payload["checksum_sha256"] = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        await self.log_security_event(
            user_id=target_user_id,
            action="EXPORT_DOWNLOAD",
            details="User generated machine-readable data export archive.",
        )
        return export_payload

    async def request_account_deletion(
        self,
        context: TenantContext,
        target_user_id: str,
        reason: str | None = None,
        immediate: bool = False,
    ) -> dict[str, Any]:
        """File an account deletion request with grace period and immediate session invalidation."""
        if context.user.id != target_user_id and "SUPER_ADMIN" not in context.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: cannot request deletion for another account.",
            )

        u_stmt = select(UserAccount).where(UserAccount.id == target_user_id)
        u_res = await self.session.execute(u_stmt)
        user = u_res.scalar_one_or_none()
        if not user or user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{target_user_id}' not found.",
            )

        # Check existing pending request
        r_stmt = select(AccountDeletionRequest).where(
            AccountDeletionRequest.user_id == target_user_id,
            AccountDeletionRequest.status == "pending",
        )
        r_res = await self.session.execute(r_stmt)
        existing = r_res.scalars().first()
        if existing:
            return {
                "request_id": existing.id,
                "status": "pending",
                "message": "A deletion request is already pending for this account.",
                "grace_period_expires_at": existing.grace_period_expires_at.isoformat(),
            }

        now = datetime.now(UTC)
        grace_expires = now if immediate else now + timedelta(days=7)

        req = AccountDeletionRequest(
            user_id=target_user_id,
            status="pending",
            reason=reason,
            grace_period_expires_at=grace_expires,
        )
        self.session.add(req)
        await self.session.flush()

        # Invalidate active login sessions immediately
        session_stmt = select(SessionDevice).where(SessionDevice.user_id == target_user_id)
        s_res = await self.session.execute(session_stmt)
        for s in s_res.scalars().all():
            await self.session.delete(s)

        # Deactivate user login during grace period
        user.is_active = False

        if immediate:
            await self._finalize_deletion(user, req)

        await self.log_security_event(
            user_id=target_user_id,
            action="DELETION_REQUEST",
            details=f"Account deletion initiated (immediate={immediate}). Reason: {reason}",
        )
        await self.session.commit()

        return {
            "request_id": req.id,
            "status": req.status,
            "message": (
                "Account permanently deleted and statutory financial records preserved."
                if immediate
                else "Deletion request scheduled. You have a 7-day grace period to cancel."
            ),
            "grace_period_expires_at": req.grace_period_expires_at.isoformat(),
            "legal_hold_retained_records": req.legal_hold_retained_records,
        }

    async def cancel_deletion_request(
        self,
        context: TenantContext,
        target_user_id: str,
    ) -> dict[str, Any]:
        """Cancel a pending deletion request during the grace period."""
        if context.user.id != target_user_id and "SUPER_ADMIN" not in context.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: cannot cancel deletion for another user.",
            )

        u_stmt = select(UserAccount).where(UserAccount.id == target_user_id)
        u_res = await self.session.execute(u_stmt)
        user = u_res.scalar_one_or_none()
        if not user or user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{target_user_id}' not found.",
            )

        r_stmt = select(AccountDeletionRequest).where(
            AccountDeletionRequest.user_id == target_user_id,
            AccountDeletionRequest.status == "pending",
        )
        r_res = await self.session.execute(r_stmt)
        req = r_res.scalars().first()
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No pending deletion request found to cancel.",
            )

        req.status = "cancelled"
        user.is_active = True

        await self.log_security_event(
            user_id=target_user_id,
            action="DELETION_CANCEL",
            details="User cancelled pending account deletion request.",
        )
        await self.session.commit()

        return {
            "request_id": req.id,
            "status": "cancelled",
            "message": "Deletion request cancelled. Account access restored.",
        }

    async def get_deletion_status(
        self,
        context: TenantContext,
        target_user_id: str,
    ) -> dict[str, Any]:
        """Retrieve current deletion status for user."""
        if context.user.id != target_user_id and "SUPER_ADMIN" not in context.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied.",
            )

        r_stmt = (
            select(AccountDeletionRequest)
            .where(AccountDeletionRequest.user_id == target_user_id)
            .order_by(AccountDeletionRequest.created_at.desc())
        )
        r_res = await self.session.execute(r_stmt)
        req = r_res.scalars().first()

        if not req:
            return {
                "has_active_request": False,
                "status": "none",
                "message": "No deletion requests on file.",
            }

        return {
            "has_active_request": req.status == "pending",
            "request_id": req.id,
            "status": req.status,
            "grace_period_expires_at": req.grace_period_expires_at.isoformat(),
            "completed_at": req.completed_at.isoformat() if req.completed_at else None,
            "legal_hold_retained_records": req.legal_hold_retained_records,
        }

    async def _finalize_deletion(
        self,
        user: UserAccount,
        req: AccountDeletionRequest,
    ) -> None:
        """Executes deletion or statutory pseudonymization if financial records exist (RQ-027, P16)."""
        now = datetime.now(UTC)

        # Check for financial records (statutory retention requirement)
        fee_stmt = select(FeePayment).where(FeePayment.student_id == user.id)
        fee_res = await self.session.execute(fee_stmt)
        has_fees = len(fee_res.scalars().all()) > 0

        sub_stmt = select(Subscription).where(Subscription.user_id == user.id)
        sub_res = await self.session.execute(sub_stmt)
        has_subscriptions = len(sub_res.scalars().all()) > 0

        anon_id = f"deleted_{user.id[:8]}"

        if has_fees or has_subscriptions:
            # Statutory financial hold: retain transaction tables, but scrub personal PII
            retained = []
            if has_fees:
                retained.append("fee_payments")
            if has_subscriptions:
                retained.append("subscriptions")

            req.legal_hold_retained_records = json.dumps(retained)
            req.anonymized_identifier = anon_id
            logger.info(
                "Statutory legal hold active for user %s: retaining %s with pseudonymization.",
                user.id,
                retained,
            )

        # Anonymize UserAccount PII and mark soft-deleted
        user.email = f"{anon_id}@anonymized.internal"
        user.full_name = "Anonymized Former Learner"
        user.is_active = False
        user.is_deleted = True
        user.deleted_at = now

        req.status = "completed"
        req.completed_at = now

    async def get_user_security_audit(
        self,
        context: TenantContext,
        target_user_id: str,
    ) -> list[dict[str, Any]]:
        """Retrieve user's security events for transparency."""
        if context.user.id != target_user_id and "SUPER_ADMIN" not in context.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied.",
            )

        stmt = (
            select(SecurityAuditLog)
            .where(SecurityAuditLog.user_id == target_user_id)
            .order_by(SecurityAuditLog.created_at.desc())
            .limit(50)
        )
        res = await self.session.execute(stmt)
        logs = res.scalars().all()

        return [
            {
                "id": item.id,
                "action": item.action,
                "ip_address": item.ip_address,
                "status": item.status,
                "details": item.details,
                "timestamp": item.created_at.isoformat(),
            }
            for item in logs
        ]
