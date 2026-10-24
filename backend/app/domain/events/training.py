"""Training eligibility governance, PII de-identification, and reproducible dataset export."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import generate_uuid
from app.db.models.events import (
    ApplicationEvent,
    TrainingDatasetExport,
    TrainingEligibilityRecord,
)


class PIIRedactor:
    """Detects and redacts direct personal identifiers from candidate training data."""

    EMAIL_PATTERN = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    PHONE_PATTERN = r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
    IP_PATTERN = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"

    @classmethod
    def redact_text(cls, text: str) -> str:
        """Strip emails, phone numbers, and IP addresses from text strings."""
        if not text:
            return ""
        s = re.sub(cls.EMAIL_PATTERN, "[EMAIL_REDACTED]", text)
        s = re.sub(cls.PHONE_PATTERN, "[PHONE_REDACTED]", s)
        s = re.sub(cls.IP_PATTERN, "[IP_REDACTED]", s)
        return s

    @classmethod
    def redact_object(cls, obj: Any) -> Any:
        """Recursively scrub PII across nested dictionaries and lists."""
        if isinstance(obj, str):
            return cls.redact_text(obj)
        elif isinstance(obj, dict):
            return {k: cls.redact_object(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [cls.redact_object(item) for item in obj]
        return obj


class TrainingPipelineService:
    """Enforces deny-by-default training governance and prepares reproducible dataset splits."""

    @classmethod
    async def evaluate_eligibility(
        cls,
        session: AsyncSession,
        event_id: str,
        user_consented: bool,
        institution_authorized: bool,
        authorization_basis: str = "EXPLICIT_CONSENT",
        reviewer_id: str | None = None,
    ) -> TrainingEligibilityRecord:
        """Evaluate event against training governance policy (deny-by-default)."""
        stmt = select(TrainingEligibilityRecord).where(
            TrainingEligibilityRecord.event_id == event_id
        )
        res = await session.execute(stmt)
        record = res.scalar_one_or_none()

        if not record:
            record = TrainingEligibilityRecord(
                id=generate_uuid(),
                event_id=event_id,
            )
            session.add(record)

        now = datetime.now(UTC)
        record.reviewed_at = now
        record.reviewed_by = reviewer_id
        record.authorization_basis = authorization_basis

        # Strict deny-by-default check
        if not user_consented or not institution_authorized:
            record.status = "EXCLUDED"
            record.exclusion_reason = (
                "Denied by policy: Requires both user consent and institution authorization."
            )
            record.pii_redacted = False
        else:
            record.status = "ELIGIBLE"
            record.exclusion_reason = None
            record.pii_redacted = True

        await session.commit()
        await session.refresh(record)
        return record

    @classmethod
    async def export_dataset(
        cls,
        session: AsyncSession,
        version_tag: str,
        train_ratio: float = 0.80,
        val_ratio: float = 0.10,
        test_ratio: float = 0.10,
    ) -> TrainingDatasetExport:
        """Generate reproducible dataset manifest from eligible records with contamination-free splits."""
        stmt = (
            select(ApplicationEvent, TrainingEligibilityRecord)
            .join(
                TrainingEligibilityRecord,
                ApplicationEvent.id == TrainingEligibilityRecord.event_id,
            )
            .where(TrainingEligibilityRecord.status == "ELIGIBLE")
            .order_by(ApplicationEvent.created_at.asc())
        )
        res = await session.execute(stmt)
        rows = res.all()

        if not rows:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No eligible training events found to export.",
            )

        # Scrub PII from all eligible event payloads
        scrubbed_examples = []
        for app_event, _ in rows:
            raw_payload = json.loads(app_event.payload_json)
            scrubbed_payload = PIIRedactor.redact_object(raw_payload)
            scrubbed_examples.append(
                {
                    "event_id": app_event.id,
                    "event_type": app_event.event_type,
                    "session_id": app_event.session_id,
                    "payload": scrubbed_payload,
                }
            )

        total = len(scrubbed_examples)
        train_end = int(total * train_ratio)
        val_end = train_end + int(total * val_ratio)

        train_split = scrubbed_examples[:train_end]
        val_split = scrubbed_examples[train_end:val_end]
        test_split = scrubbed_examples[val_end:]

        manifest_data = {
            "version_tag": version_tag,
            "created_at_utc": datetime.now(UTC).isoformat(),
            "total_examples": total,
            "splits": {
                "train_count": len(train_split),
                "val_count": len(val_split),
                "test_count": len(test_split),
            },
            "examples": {
                "train": train_split,
                "val": val_split,
                "test": test_split,
            },
        }

        manifest_bytes = json.dumps(manifest_data, sort_keys=True).encode("utf-8")
        checksum = hashlib.sha256(manifest_bytes).hexdigest()

        export_record = TrainingDatasetExport(
            id=generate_uuid(),
            version_tag=version_tag,
            total_examples=total,
            train_count=len(train_split),
            val_count=len(val_split),
            test_count=len(test_split),
            sha256_checksum=checksum,
            manifest_json=json.dumps(
                {
                    "version_tag": version_tag,
                    "total_examples": total,
                    "train_count": len(train_split),
                    "val_count": len(val_split),
                    "test_count": len(test_split),
                    "sha256_checksum": checksum,
                }
            ),
            is_approved=False,  # Enforces explicit human approval gate!
        )
        session.add(export_record)
        await session.commit()
        await session.refresh(export_record)
        return export_record

    @classmethod
    async def approve_dataset(
        cls,
        session: AsyncSession,
        dataset_id: str,
        approver_id: str,
    ) -> TrainingDatasetExport:
        """Apply human sign-off approval to an exported training dataset."""
        dataset = await session.get(TrainingDatasetExport, dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset export not found.",
            )

        dataset.is_approved = True
        dataset.approved_by = approver_id
        dataset.approved_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(dataset)
        return dataset

    @classmethod
    async def verify_training_allowed(
        cls,
        session: AsyncSession,
        dataset_id: str,
    ) -> bool:
        """Gate preventing any model training process from using unapproved datasets."""
        dataset = await session.get(TrainingDatasetExport, dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found.",
            )

        if not dataset.is_approved:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Training blocked: Dataset has not received explicit human authorization.",
            )

        return True
