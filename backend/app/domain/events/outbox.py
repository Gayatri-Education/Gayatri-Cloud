"""Transactional Outbox service ensuring reliable event dispatching and quarantine."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import generate_uuid
from app.db.models.events import (
    ApplicationEvent,
    EventOutbox,
    TrainingEligibilityRecord,
)
from app.domain.events.envelope import EventEnvelope


class OutboxService:
    """Manages transactional outbox recording, retry mechanics, and poison event quarantine."""

    @classmethod
    async def record_event(
        cls,
        session: AsyncSession,
        envelope: EventEnvelope,
    ) -> ApplicationEvent:
        """Write an application event and its outbox dispatch record atomically."""
        app_event = ApplicationEvent(
            id=envelope.event_id,
            event_type=envelope.event_type,
            schema_version=envelope.schema_version,
            actor_id=envelope.actor_id,
            actor_type=envelope.actor_type,
            organization_id=envelope.organization_id,
            session_id=envelope.session_id,
            correlation_id=envelope.correlation_id,
            idempotency_key=envelope.idempotency_key,
            sensitivity_level=str(envelope.sensitivity_level),
            payload_json=json.dumps(envelope.payload),
        )
        session.add(app_event)

        outbox_entry = EventOutbox(
            id=generate_uuid(),
            event_id=app_event.id,
            status="pending",
            retry_count=0,
        )
        session.add(outbox_entry)

        # Initialize Deny-by-default training governance record
        eligibility = TrainingEligibilityRecord(
            id=generate_uuid(),
            event_id=app_event.id,
            status="NOT_REVIEWED",
            purpose_scope="GENERAL_MODEL_TRAINING",
            pii_redacted=False,
        )
        session.add(eligibility)

        return app_event

    @classmethod
    async def get_pending_batch(
        cls,
        session: AsyncSession,
        limit: int = 50,
    ) -> list[tuple[EventOutbox, ApplicationEvent]]:
        """Fetch oldest pending outbox items and their parent event models."""
        stmt = (
            select(EventOutbox, ApplicationEvent)
            .join(ApplicationEvent, EventOutbox.event_id == ApplicationEvent.id)
            .where(EventOutbox.status == "pending")
            .order_by(EventOutbox.created_at.asc())
            .limit(limit)
        )
        res = await session.execute(stmt)
        return list(res.tuples().all())

    @classmethod
    async def mark_archived(
        cls,
        session: AsyncSession,
        outbox_ids: list[str],
    ) -> int:
        """Mark outbox items as successfully archived."""
        if not outbox_ids:
            return 0

        stmt = select(EventOutbox).where(EventOutbox.id.in_(outbox_ids))
        res = await session.execute(stmt)
        items = res.scalars().all()
        now = datetime.now(UTC)
        for itm in items:
            itm.status = "archived"
            itm.processed_at = now

        return len(items)

    @classmethod
    async def record_failure(
        cls,
        session: AsyncSession,
        outbox_id: str,
        error_message: str,
        max_retries: int = 3,
    ) -> EventOutbox | None:
        """Increment retry count or quarantine the outbox item if limit is exceeded."""
        itm = await session.get(EventOutbox, outbox_id)
        if not itm:
            return None

        itm.retry_count += 1
        itm.last_error = error_message
        if itm.retry_count >= max_retries:
            itm.status = "quarantined"
        else:
            itm.status = "failed"

        return itm

    @classmethod
    async def get_queue_stats(cls, session: AsyncSession) -> dict[str, Any]:
        """Return breakdown of outbox status counts and lag."""
        stmt = select(EventOutbox.status, func.count(EventOutbox.id)).group_by(EventOutbox.status)
        res = await session.execute(stmt)
        counts = dict(res.all())

        # Find oldest pending event timestamp for lag calculation
        lag_stmt = select(func.min(EventOutbox.created_at)).where(EventOutbox.status == "pending")
        oldest_ts = (await session.execute(lag_stmt)).scalar()
        lag_seconds = 0.0
        if oldest_ts:
            aware_oldest = oldest_ts if oldest_ts.tzinfo else oldest_ts.replace(tzinfo=UTC)
            lag_seconds = (datetime.now(UTC) - aware_oldest).total_seconds()

        return {
            "pending": counts.get("pending", 0),
            "archived": counts.get("archived", 0),
            "failed": counts.get("failed", 0),
            "quarantined": counts.get("quarantined", 0),
            "oldest_pending_lag_seconds": round(lag_seconds, 2),
        }
