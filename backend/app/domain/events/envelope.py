"""Canonical versioned event envelope definitions and category contracts."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class EventCategory(StrEnum):
    IDENTITY = "identity"
    COURSE = "course"
    TUTOR = "tutor"
    LEARNING = "learning"
    AI_EXECUTION = "ai_execution"
    ADMIN_PRIVACY = "admin_privacy"
    BILLING = "billing"
    OPERATIONS = "operations"


class SensitivityLevel(StrEnum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    PROTECTED = "PROTECTED"
    RESTRICTED = "RESTRICTED"


@dataclass
class EventEnvelope:
    """Canonical event envelope with audit provenance and security classification."""

    event_type: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    schema_version: str = "1.0.0"
    timestamp_utc: datetime = field(default_factory=lambda: datetime.now(UTC))
    actor_id: str | None = None
    actor_type: str = "user"
    organization_id: str | None = None
    session_id: str | None = None
    correlation_id: str | None = None
    idempotency_key: str | None = None
    sensitivity_level: SensitivityLevel = SensitivityLevel.PROTECTED

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["timestamp_utc"] = (
            self.timestamp_utc.isoformat()
            if isinstance(self.timestamp_utc, datetime)
            else str(self.timestamp_utc)
        )
        data["sensitivity_level"] = str(self.sensitivity_level)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EventEnvelope:
        ts = data.get("timestamp_utc")
        if isinstance(ts, str):
            dt = datetime.fromisoformat(ts)
        elif isinstance(ts, datetime):
            dt = ts
        else:
            dt = datetime.now(UTC)

        return cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            event_type=data.get("event_type", "unknown"),
            schema_version=data.get("schema_version", "1.0.0"),
            timestamp_utc=dt,
            actor_id=data.get("actor_id"),
            actor_type=data.get("actor_type", "user"),
            organization_id=data.get("organization_id"),
            session_id=data.get("session_id"),
            correlation_id=data.get("correlation_id"),
            idempotency_key=data.get("idempotency_key"),
            sensitivity_level=SensitivityLevel(
                data.get("sensitivity_level", SensitivityLevel.PROTECTED)
            ),
            payload=data.get("payload", {}),
        )
