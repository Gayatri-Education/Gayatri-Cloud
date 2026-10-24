/**
 * Observability, Reliability, and Recovery TypeScript contracts.
 */

export interface ComponentHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  latency_ms?: number;
  type?: string;
  writeable?: boolean;
  unprocessed_events_lag?: number;
  high_backlog_alert?: boolean;
  total_monitored?: number;
  tripped_count?: number;
  error?: string;
  breakers?: CircuitBreakerItem[];
}

export interface SystemHealthReport {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  components: {
    database?: ComponentHealth;
    storage?: ComponentHealth;
    event_outbox?: ComponentHealth;
    circuit_breakers?: ComponentHealth;
  };
}

export interface CircuitBreakerItem {
  name: string;
  state: 'CLOSED' | 'OPEN' | 'HALF_OPEN';
  consecutive_failures: number;
  consecutive_successes: number;
  is_manual_trip: boolean;
  manual_trip_reason: string | null;
  last_state_change: string;
}

export interface MetricsSummary {
  timestamp: string;
  total_http_requests: number;
  http_endpoints_breakdown: Record<string, number>;
  total_ai_calls: number;
  ai_calls_breakdown: Record<string, number>;
  ai_token_consumption: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  average_ai_latency_seconds: number;
  outbox_lag_gauge: number;
  active_circuit_trips: number;
}

export interface BackupSnapshot {
  snapshot_id: string;
  snapshot_label: string;
  created_at: string;
  engine: string;
  encryption: string;
  storage_target: string;
  inventory: Record<string, number>;
  checksum_sha256: string;
  status: string;
}

export interface RestoreReport {
  restore_simulation_id: string;
  snapshot_id: string;
  snapshot_label: string;
  checksum_verified: boolean;
  status: string;
  simulated_at: string;
  target_environment: string;
  restored_tables_count: number;
  restored_records_total: number;
  data_divergence_detected: boolean;
  recovery_readiness_score: number;
  message: string;
}
