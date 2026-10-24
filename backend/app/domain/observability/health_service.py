"""Deep Dependency Readiness and Component Health Checker.
Monitors database connectivity, storage accessibility, outbox lag, and circuit breaker health (RQ-031, DEC-C29).
"""

from __future__ import annotations

import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import EventOutbox
from app.domain.observability.circuit_breaker import CircuitBreakerRegistry
from app.domain.observability.metrics import metrics

logger = logging.getLogger(__name__)


class DeepHealthService:
    """Performs deep health and readiness checks across infrastructure dependencies."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def check_readiness(self) -> dict[str, Any]:
        """Inspect all critical system subsystems without leaking credentials."""
        now = datetime.now(UTC)
        components: dict[str, Any] = {}
        overall_healthy = True
        degraded = False

        # 1. Database Check
        db_start = time.perf_counter()
        try:
            res = await self.session.execute(text("SELECT 1"))
            val = res.scalar()
            db_latency_ms = (time.perf_counter() - db_start) * 1000.0
            components["database"] = {
                "status": "healthy" if val == 1 else "unhealthy",
                "latency_ms": round(db_latency_ms, 2),
                "type": "relational_sql",
            }
        except Exception as e:
            logger.error("Database health check failed: %s", e)
            components["database"] = {
                "status": "unhealthy",
                "error": "Database connection failed",
            }
            overall_healthy = False

        # 2. Storage System Check
        try:
            # Check local storage root writeability
            test_dir = os.path.join(os.getcwd(), "data")
            os.makedirs(test_dir, exist_ok=True)
            test_file = os.path.join(test_dir, ".health_probe")
            with open(test_file, "w") as f:
                f.write("ok")
            os.remove(test_file)
            components["storage"] = {
                "status": "healthy",
                "type": "local_or_s3_interface",
                "writeable": True,
            }
        except Exception as e:
            logger.error("Storage health check failed: %s", e)
            components["storage"] = {
                "status": "degraded",
                "error": "Storage volume write check failed",
            }
            degraded = True

        # 3. Outbox Event Queue Backlog
        try:
            stmt = select(func.count(EventOutbox.id)).where(EventOutbox.processed_at.is_(None))
            res = await self.session.execute(stmt)
            outbox_lag = res.scalar() or 0
            metrics.set_outbox_lag(outbox_lag)

            is_lag_high = outbox_lag > 500
            if is_lag_high:
                degraded = True

            components["event_outbox"] = {
                "status": "degraded" if is_lag_high else "healthy",
                "unprocessed_events_lag": outbox_lag,
                "high_backlog_alert": is_lag_high,
            }
        except Exception as e:
            logger.error("Outbox lag check failed: %s", e)
            components["event_outbox"] = {
                "status": "unknown",
                "error": "Unable to calculate outbox lag",
            }

        # 4. Circuit Breakers Status
        breakers = CircuitBreakerRegistry.get_all_statuses()
        open_breakers = [b for b in breakers if b["state"] == "OPEN"]
        metrics.set_circuit_trips(len(open_breakers))
        if open_breakers:
            degraded = True

        components["circuit_breakers"] = {
            "status": "degraded" if open_breakers else "healthy",
            "total_monitored": len(breakers),
            "tripped_count": len(open_breakers),
            "breakers": breakers,
        }

        # Determine overall state
        if not overall_healthy:
            system_status = "unhealthy"
        elif degraded:
            system_status = "degraded"
        else:
            system_status = "healthy"

        return {
            "status": system_status,
            "timestamp": now.isoformat(),
            "components": components,
        }
