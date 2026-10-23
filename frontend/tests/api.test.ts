import { describe, it, expect, vi } from 'vitest';
import { fetchHealth, fetchReadiness } from '../src/lib/api';

describe('Frontend API Client Contracts', () => {
  it('fetchHealth parses valid backend health response', async () => {
    const mockHealth = {
      status: 'ok',
      app: 'Gayatri Cloud API',
      version: '0.1.0',
      timestamp: '2026-10-24T00:00:00Z',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockHealth,
    } as Response);

    const result = await fetchHealth();
    expect(result.status).toBe('ok');
    expect(result.app).toBe('Gayatri Cloud API');
    expect(result.version).toBe('0.1.0');
  });

  it('fetchHealth throws structured error on HTTP failure', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
    } as Response);

    await expect(fetchHealth()).rejects.toThrow('Health check failed with status: 503');
  });

  it('fetchReadiness parses valid backend readiness checks', async () => {
    const mockReadiness = {
      status: 'ready',
      checks: { api: 'ok', environment: 'testing' },
      timestamp: '2026-10-24T00:00:00Z',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockReadiness,
    } as Response);

    const result = await fetchReadiness();
    expect(result.status).toBe('ready');
    expect(result.checks.api).toBe('ok');
  });
});
