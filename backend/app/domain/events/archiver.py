"""Durable event archiver persisting immutable event batches to S3/LocalStorage with checksums."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import StorageService
from app.db.base import generate_uuid
from app.db.models.events import EventArchiveBatch
from app.domain.events.outbox import OutboxService


class ArchiveService:
    """Orchestrates batch archival from transactional outbox to immutable object storage."""

    @classmethod
    async def process_pending_outbox(
        cls,
        session: AsyncSession,
        storage_service: StorageService,
        batch_size: int = 50,
    ) -> EventArchiveBatch | None:
        """Read pending outbox items, pack into immutable archive manifest, upload to storage, and mark archived."""
        pending_records = await OutboxService.get_pending_batch(session, limit=batch_size)
        if not pending_records:
            return None

        outbox_ids = [outbox.id for outbox, _ in pending_records]
        events = [event for _, event in pending_records]

        now = datetime.now(UTC)
        batch_id = f"batch_{now.strftime('%Y%m%d_%H%M%S')}_{generate_uuid()[:8]}"
        date_prefix = now.strftime("%Y/%m/%d")
        storage_path = f"archives/events/{date_prefix}/{batch_id}.json"

        events_data: list[dict[str, Any]] = []
        for ev in events:
            events_data.append(
                {
                    "event_id": ev.id,
                    "event_type": ev.event_type,
                    "schema_version": ev.schema_version,
                    "actor_id": ev.actor_id,
                    "actor_type": ev.actor_type,
                    "organization_id": ev.organization_id,
                    "session_id": ev.session_id,
                    "correlation_id": ev.correlation_id,
                    "idempotency_key": ev.idempotency_key,
                    "sensitivity_level": ev.sensitivity_level,
                    "created_at": ev.created_at.isoformat() if ev.created_at else now.isoformat(),
                    "payload": json.loads(ev.payload_json),
                }
            )

        batch_manifest = {
            "batch_id": batch_id,
            "generated_at_utc": now.isoformat(),
            "event_count": len(events_data),
            "storage_path": storage_path,
            "events": events_data,
        }

        manifest_bytes = json.dumps(batch_manifest, indent=2).encode("utf-8")
        checksum = hashlib.sha256(manifest_bytes).hexdigest()

        # Persist to private object storage
        storage_service.upload_file(
            content=manifest_bytes,
            storage_path=storage_path,
            content_type="application/json",
        )

        # Record archive batch
        archive_batch = EventArchiveBatch(
            id=generate_uuid(),
            batch_id=batch_id,
            storage_path=storage_path,
            sha256_checksum=checksum,
            event_count=len(events_data),
            manifest_json=json.dumps(
                {
                    "batch_id": batch_id,
                    "event_count": len(events_data),
                    "sha256": checksum,
                    "storage_path": storage_path,
                }
            ),
        )
        session.add(archive_batch)

        # Mark outbox entries as archived
        await OutboxService.mark_archived(session, outbox_ids)

        await session.commit()
        await session.refresh(archive_batch)
        return archive_batch

    @classmethod
    async def verify_batch_integrity(
        cls,
        session: AsyncSession,
        storage_service: StorageService,
        batch_id: str,
    ) -> bool:
        """Verify that the stored archive object matches its recorded SHA-256 checksum."""
        stmt = select(EventArchiveBatch).where(EventArchiveBatch.batch_id == batch_id)
        res = await session.execute(stmt)
        batch = res.scalar_one_or_none()
        if not batch:
            return False

        try:
            content = storage_service.download_file(batch.storage_path)
            calculated = hashlib.sha256(content).hexdigest()
            return calculated == batch.sha256_checksum
        except Exception:
            return False
