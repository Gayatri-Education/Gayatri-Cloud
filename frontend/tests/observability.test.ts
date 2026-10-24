import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiClient } from '../src/lib/api-client';
import {
  SystemHealthReport,
  MetricsSummary,
  BackupSnapshot,
  RestoreReport,
} from '../src/lib/types/observability';

describe('P19 Observability, Reliability & Recovery — Frontend Tests', () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient('http://localhost:8000');
    vi.restoreAllMocks();
  });

  describe('1. Deep Health & Component Readiness', () => {
    it('retrieves multi-component health report', async () => {
      const mockHealth: SystemHealthReport = {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        components: {
          database: { status: 'healthy', latency_ms: 1.45, type: 'relational_sql' },
          storage: { status: 'healthy', type: 'local_or_s3_interface', writeable: true },
          event_outbox: { status: 'healthy', unprocessed_events_lag: 0, high_backlog_alert: false },
          circuit_breakers: {
            status: 'healthy',
            total_monitored: 6,
            tripped_count: 0,
            breakers: [
              {
                name: 'openai',
                state: 'CLOSED',
                consecutive_failures: 0,
                consecutive_successes: 10,
                is_manual_trip: false,
                manual_trip_reason: null,
                last_state_change: new Date().toISOString(),
              },
            ],
          },
        },
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockHealth,
      } as any);

      const res = await client.getDeepHealth();
      expect(res.status).toBe('healthy');
      expect(res.components.database?.latency_ms).toBe(1.45);
      expect(res.components.circuit_breakers?.total_monitored).toBe(6);
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/observability/deep-health',
        expect.anything()
      );
    });
  });

  describe('2. Operational Metrics & Token Telemetry', () => {
    it('retrieves aggregated telemetry metrics', async () => {
      const mockMetrics: MetricsSummary = {
        timestamp: new Date().toISOString(),
        total_http_requests: 1500,
        http_endpoints_breakdown: { 'GET:/health:200': 1200, 'POST:/api/v1/tutoring/turn:200': 300 },
        total_ai_calls: 320,
        ai_calls_breakdown: { 'openai:gpt-4o:success': 320 },
        ai_token_consumption: {
          prompt_tokens: 15000,
          completion_tokens: 8500,
          total_tokens: 23500,
        },
        average_ai_latency_seconds: 0.425,
        outbox_lag_gauge: 3,
        active_circuit_trips: 0,
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockMetrics,
      } as any);

      const res = await client.getObservabilityMetrics();
      expect(res.total_http_requests).toBe(1500);
      expect(res.ai_token_consumption.total_tokens).toBe(23500);
      expect(res.average_ai_latency_seconds).toBe(0.425);
    });
  });

  describe('3. Circuit Breaker Emergency Kill-Switch', () => {
    it('trips provider circuit breaker with emergency reason', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          provider: 'openai',
          action: 'tripped',
          status: { state: 'OPEN', is_manual_trip: true },
        }),
      } as any);

      const res = await client.tripCircuitBreaker('openai', 'Token spike anomaly');
      expect(res.action).toBe('tripped');
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/observability/circuit-breakers/openai/trip',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ reason: 'Token spike anomaly' }),
        })
      );
    });

    it('resets tripped circuit breaker back to healthy state', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          provider: 'openai',
          action: 'reset',
          status: { state: 'CLOSED', is_manual_trip: false },
        }),
      } as any);

      const res = await client.resetCircuitBreaker('openai');
      expect(res.action).toBe('reset');
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/observability/circuit-breakers/openai/reset',
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  describe('4. Backup Snapshot & Restore Verification', () => {
    it('generates snapshot and verifies restore simulation with zero data loss', async () => {
      const mockSnapshot: BackupSnapshot = {
        snapshot_id: 'snap-123456',
        snapshot_label: 'manual_drill',
        created_at: new Date().toISOString(),
        engine: 'postgresql_rds_spec',
        encryption: 'AES-256-GCM',
        storage_target: 's3://gayatri-backups/snap-123456.sql.enc',
        inventory: { user_accounts: 50, courses: 5 },
        checksum_sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        status: 'created_and_verified',
      };

      const mockRestore: RestoreReport = {
        restore_simulation_id: 'restore-abcdef',
        snapshot_id: 'snap-123456',
        snapshot_label: 'manual_drill',
        checksum_verified: true,
        status: 'restored_successfully',
        simulated_at: new Date().toISOString(),
        target_environment: 'isolated_recovery_target',
        restored_tables_count: 2,
        restored_records_total: 55,
        data_divergence_detected: false,
        recovery_readiness_score: 100.0,
        message: 'Disaster recovery simulation completed with zero data loss.',
      };

      global.fetch = vi
        .fn()
        .mockResolvedValueOnce({ ok: true, json: async () => mockSnapshot } as any)
        .mockResolvedValueOnce({ ok: true, json: async () => mockRestore } as any);

      const snapshot = await client.createBackupSnapshot('manual_drill');
      expect(snapshot.snapshot_id).toBe('snap-123456');

      const restore = await client.verifyBackupRestore(snapshot);
      expect(restore.status).toBe('restored_successfully');
      expect(restore.data_divergence_detected).toBe(false);
      expect(restore.recovery_readiness_score).toBe(100.0);
    });
  });
});
