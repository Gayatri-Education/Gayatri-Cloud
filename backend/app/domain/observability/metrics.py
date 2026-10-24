"""Observability Metrics Engine with Prometheus Exposition.
Collects HTTP request rates, AI provider latencies, token consumption, and outbox lag.
"""

from __future__ import annotations

import threading
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any


class MetricsCollector:
    """Thread-safe application metrics accumulator."""

    _instance: MetricsCollector | None = None
    _lock = threading.Lock()

    def __new__(cls) -> MetricsCollector:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_metrics()
            return cls._instance

    def _init_metrics(self) -> None:
        self.lock = threading.Lock()
        self.http_requests_total: dict[str, int] = defaultdict(int)
        self.http_request_durations: dict[str, list[float]] = defaultdict(list)
        self.ai_calls_total: dict[str, int] = defaultdict(int)
        self.ai_tokens_total: dict[str, int] = defaultdict(int)
        self.ai_latencies: dict[str, list[float]] = defaultdict(list)
        self.outbox_lag_gauge: int = 0
        self.active_circuit_trips: int = 0

    def record_http_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        key = f"{method.upper()}:{path}:{status_code}"
        path_key = f"{method.upper()}:{path}"
        with self.lock:
            self.http_requests_total[key] += 1
            if len(self.http_request_durations[path_key]) < 1000:
                self.http_request_durations[path_key].append(duration_seconds)

    def record_ai_call(
        self,
        provider: str,
        model: str,
        status_str: str,
        latency_seconds: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> None:
        key = f"{provider}:{model}:{status_str}"
        prov_key = provider
        with self.lock:
            self.ai_calls_total[key] += 1
            self.ai_tokens_total[f"{provider}:prompt"] += prompt_tokens
            self.ai_tokens_total[f"{provider}:completion"] += completion_tokens
            if len(self.ai_latencies[prov_key]) < 1000:
                self.ai_latencies[prov_key].append(latency_seconds)

    def set_outbox_lag(self, lag: int) -> None:
        with self.lock:
            self.outbox_lag_gauge = max(0, lag)

    def set_circuit_trips(self, count: int) -> None:
        with self.lock:
            self.active_circuit_trips = max(0, count)

    def get_summary(self) -> dict[str, Any]:
        with self.lock:
            total_requests = sum(self.http_requests_total.values())
            total_ai = sum(self.ai_calls_total.values())
            total_prompt_tokens = sum(
                v for k, v in self.ai_tokens_total.items() if k.endswith(":prompt")
            )
            total_completion_tokens = sum(
                v for k, v in self.ai_tokens_total.items() if k.endswith(":completion")
            )

            avg_ai_latency = 0.0
            all_ai_latencies = [lat for l_list in self.ai_latencies.values() for lat in l_list]
            if all_ai_latencies:
                avg_ai_latency = sum(all_ai_latencies) / len(all_ai_latencies)

            return {
                "timestamp": datetime.now(UTC).isoformat(),
                "total_http_requests": total_requests,
                "http_endpoints_breakdown": dict(self.http_requests_total),
                "total_ai_calls": total_ai,
                "ai_calls_breakdown": dict(self.ai_calls_total),
                "ai_token_consumption": {
                    "prompt_tokens": total_prompt_tokens,
                    "completion_tokens": total_completion_tokens,
                    "total_tokens": total_prompt_tokens + total_completion_tokens,
                },
                "average_ai_latency_seconds": round(avg_ai_latency, 3),
                "outbox_lag_gauge": self.outbox_lag_gauge,
                "active_circuit_trips": self.active_circuit_trips,
            }

    def generate_prometheus(self) -> str:
        """Format metrics into standard Prometheus exposition format."""
        lines = [
            "# HELP gayatri_http_requests_total Total number of HTTP requests processed.",
            "# TYPE gayatri_http_requests_total counter",
        ]
        with self.lock:
            for key, count in self.http_requests_total.items():
                parts = key.split(":")
                if len(parts) == 3:
                    m, p, s = parts
                    lines.append(
                        f'gayatri_http_requests_total{{method="{m}",path="{p}",status="{s}"}} {count}'
                    )

            lines.extend(
                [
                    "# HELP gayatri_ai_calls_total Total external AI provider calls.",
                    "# TYPE gayatri_ai_calls_total counter",
                ]
            )
            for key, count in self.ai_calls_total.items():
                parts = key.split(":")
                if len(parts) == 3:
                    prov, mdl, st = parts
                    lines.append(
                        f'gayatri_ai_calls_total{{provider="{prov}",model="{mdl}",status="{st}"}} {count}'
                    )

            lines.extend(
                [
                    "# HELP gayatri_ai_tokens_total Total tokens processed across AI providers.",
                    "# TYPE gayatri_ai_tokens_total counter",
                ]
            )
            for key, count in self.ai_tokens_total.items():
                parts = key.split(":")
                if len(parts) == 2:
                    prov, t_type = parts
                    lines.append(
                        f'gayatri_ai_tokens_total{{provider="{prov}",type="{t_type}"}} {count}'
                    )

            lines.extend(
                [
                    "# HELP gayatri_outbox_lag_gauge Current unprocessed event outbox lag count.",
                    "# TYPE gayatri_outbox_lag_gauge gauge",
                    f"gayatri_outbox_lag_gauge {self.outbox_lag_gauge}",
                    "# HELP gayatri_circuit_trips_gauge Count of currently tripped open circuit breakers.",
                    "# TYPE gayatri_circuit_trips_gauge gauge",
                    f"gayatri_circuit_trips_gauge {self.active_circuit_trips}",
                ]
            )

        return "\n".join(lines) + "\n"


# Global singleton instance
metrics = MetricsCollector()
