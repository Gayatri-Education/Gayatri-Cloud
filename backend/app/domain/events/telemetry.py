"""Operational Telemetry Plane ensuring segregation and redaction of diagnostic logs."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("gayatri.operational_telemetry")


class OperationalTelemetry:
    """Enforces segregation of technical operational logs from protected student interaction content."""

    SENSITIVE_KEYS = {
        "password",
        "secret",
        "api_key",
        "token",
        "prompt",
        "message_text",
        "student_response",
        "correct_answer",
        "solution",
        "rubric",
        "raw_text",
    }

    @classmethod
    def redact_data(cls, data: Any) -> Any:
        """Recursively redact sensitive keys and PII from telemetry dictionaries."""
        if isinstance(data, dict):
            cleaned: dict[str, Any] = {}
            for k, v in data.items():
                if any(sk in k.lower() for sk in cls.SENSITIVE_KEYS):
                    cleaned[k] = "[REDACTED]"
                else:
                    cleaned[k] = cls.redact_data(v)
            return cleaned
        elif isinstance(data, list):
            return [cls.redact_data(item) for item in data]
        return data

    @classmethod
    def format_telemetry_entry(
        cls,
        component: str,
        event_type: str,
        correlation_id: str | None = None,
        actor_id: str | None = None,
        organization_id: str | None = None,
        latency_ms: float | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Construct safe, redacted operational log payload."""
        safe_meta = cls.redact_data(extra_metadata or {})
        entry = {
            "component": component,
            "event_type": event_type,
            "correlation_id": correlation_id,
            "actor_id": actor_id,
            "organization_id": organization_id,
            "latency_ms": latency_ms,
            "metadata": safe_meta,
        }
        return entry
