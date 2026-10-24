"""Circuit Breaker Pattern and Emergency Kill-Switch for AI Providers.
Prevents cascading failures, protects downstream rate limits, and stops retry storms (RQ-020, DEC-C17).
"""

from __future__ import annotations

import logging
import threading
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class CircuitState(StrEnum):
    CLOSED = "CLOSED"  # Healthy, requests flow through
    OPEN = "OPEN"  # Tripped, requests fail fast
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class CircuitBreaker:
    """State machine guarding an external dependency from retry storms."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout_seconds: float = 30.0,
        half_open_success_threshold: int = 2,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(seconds=recovery_timeout_seconds)
        self.half_open_success_threshold = half_open_success_threshold

        self.state: CircuitState = CircuitState.CLOSED
        self.consecutive_failures: int = 0
        self.consecutive_successes: int = 0
        self.last_failure_time: datetime | None = None
        self.last_state_change: datetime = datetime.now(UTC)
        self.is_manual_trip: bool = False
        self.manual_trip_reason: str | None = None
        self.lock = threading.Lock()

    def can_execute(self) -> bool:
        """Determines if a request is allowed through or should fast-fail."""
        with self.lock:
            now = datetime.now(UTC)

            if self.is_manual_trip:
                return False

            if self.state == CircuitState.CLOSED:
                return True

            if self.state == CircuitState.OPEN:
                if (
                    self.last_failure_time
                    and (now - self.last_failure_time) >= self.recovery_timeout
                ):
                    logger.info(
                        "CircuitBreaker '%s': cooldown elapsed, entering HALF_OPEN probe state.",
                        self.name,
                    )
                    self.state = CircuitState.HALF_OPEN
                    self.consecutive_successes = 0
                    self.last_state_change = now
                    return True
                return False

            if self.state == CircuitState.HALF_OPEN:
                return True

            return False

    def require_execution_permission(self) -> None:
        """Raises HTTPException(503) immediately if circuit is open."""
        if not self.can_execute():
            reason = self.manual_trip_reason or "excessive consecutive failures"
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Circuit breaker for provider '{self.name}' is OPEN ({reason}). Request fast-failed.",
            )

    def record_success(self) -> None:
        """Signals that an operation succeeded."""
        with self.lock:
            now = datetime.now(UTC)
            self.consecutive_failures = 0

            if self.state == CircuitState.HALF_OPEN:
                self.consecutive_successes += 1
                if self.consecutive_successes >= self.half_open_success_threshold:
                    logger.info(
                        "CircuitBreaker '%s': probe succeeded, recovering to CLOSED state.",
                        self.name,
                    )
                    self.state = CircuitState.CLOSED
                    self.consecutive_successes = 0
                    self.last_state_change = now

    def record_failure(self, error_message: str | None = None) -> None:
        """Signals that an operation failed."""
        with self.lock:
            now = datetime.now(UTC)
            self.consecutive_failures += 1
            self.last_failure_time = now

            if self.state == CircuitState.HALF_OPEN:
                logger.warning(
                    "CircuitBreaker '%s': probe failed, tripping back to OPEN state.", self.name
                )
                self.state = CircuitState.OPEN
                self.last_state_change = now
            elif (
                self.state == CircuitState.CLOSED
                and self.consecutive_failures >= self.failure_threshold
            ):
                logger.warning(
                    "CircuitBreaker '%s': reached %d consecutive failures, tripping to OPEN state. Error: %s",
                    self.name,
                    self.consecutive_failures,
                    error_message,
                )
                self.state = CircuitState.OPEN
                self.last_state_change = now

    def manual_trip(self, reason: str = "Admin emergency kill-switch") -> None:
        """Immediately trips the breaker manually."""
        with self.lock:
            self.state = CircuitState.OPEN
            self.is_manual_trip = True
            self.manual_trip_reason = reason
            self.last_state_change = datetime.now(UTC)
            logger.warning(
                "CircuitBreaker '%s': manually tripped by administrator (%s).", self.name, reason
            )

    def manual_reset(self) -> None:
        """Resets the breaker to healthy CLOSED state."""
        with self.lock:
            self.state = CircuitState.CLOSED
            self.is_manual_trip = False
            self.manual_trip_reason = None
            self.consecutive_failures = 0
            self.consecutive_successes = 0
            self.last_state_change = datetime.now(UTC)
            logger.info("CircuitBreaker '%s': manually reset to CLOSED.", self.name)

    def get_status(self) -> dict[str, Any]:
        with self.lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "consecutive_failures": self.consecutive_failures,
                "consecutive_successes": self.consecutive_successes,
                "is_manual_trip": self.is_manual_trip,
                "manual_trip_reason": self.manual_trip_reason,
                "last_state_change": self.last_state_change.isoformat(),
            }


class CircuitBreakerRegistry:
    """Global registry managing breakers for all external providers."""

    _breakers: dict[str, CircuitBreaker] = {}
    _lock = threading.Lock()

    @classmethod
    def get(cls, provider_name: str) -> CircuitBreaker:
        name = provider_name.lower().strip()
        with cls._lock:
            if name not in cls._breakers:
                cls._breakers[name] = CircuitBreaker(name=name)
            return cls._breakers[name]

    @classmethod
    def get_all_statuses(cls) -> list[dict[str, Any]]:
        with cls._lock:
            # Ensure standard providers are seeded
            for default_p in ("openai", "gemini", "anthropic", "grok", "openrouter", "mock"):
                if default_p not in cls._breakers:
                    cls._breakers[default_p] = CircuitBreaker(name=default_p)
            return [b.get_status() for b in cls._breakers.values()]
