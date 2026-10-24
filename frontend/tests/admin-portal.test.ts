import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiClient } from '../src/lib/api-client';
import {
  AdminMetrics,
  OrganizationMember,
  DomainVerification,
  AdminAiPolicy,
  AuditLogEntry,
  OrganizationDetails,
} from '../src/lib/types/admin';

describe('P15 Super-Admin & Organization-Admin Portal — Frontend Contracts & Security', () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient('http://localhost:8000');
    vi.restoreAllMocks();
  });

  describe('1. Operational Dashboard & Telemetry', () => {
    it('fetches aggregated admin metrics and system health', async () => {
      client.setToken('admin-jwt-token');
      client.setOrganizationId('org-alpha');

      const mockMetrics: AdminMetrics = {
        organization_id: 'org-alpha',
        total_members: 85,
        total_courses: 6,
        total_offerings: 12,
        outbox_lag_count: 0,
        total_ai_tokens_consumed: 125000,
        system_health: 'healthy',
      };

      global.fetch = vi.fn().mockImplementation((url) => {
        expect(url).toContain('/api/v1/admin/dashboard?organization_id=org-alpha');
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mockMetrics,
        });
      });

      const metrics = await client.getAdminDashboardMetrics('org-alpha');
      expect(metrics.total_members).toBe(85);
      expect(metrics.system_health).toBe('healthy');
      expect(metrics.total_ai_tokens_consumed).toBe(125000);
    });
  });

  describe('2. Domain Ownership Proof & DNS Verification', () => {
    it('manages domain registration, DNS verification tokens, and completion proof', async () => {
      client.setToken('admin-jwt-token');

      const mockDomains: DomainVerification[] = [
        {
          id: 'dom-1',
          domain_name: 'alpha.edu',
          is_verified: true,
          created_at: '2026-10-01T10:00:00Z',
        },
      ];

      // 1. List domains
      global.fetch = vi.fn().mockImplementation((url) => {
        if (url.endsWith('/domains')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => mockDomains,
          });
        }
        return Promise.reject(new Error('Unknown endpoint'));
      });

      const domains = await client.getAdminDomains('org-alpha');
      expect(domains).toHaveLength(1);
      expect(domains[0].domain_name).toBe('alpha.edu');

      // 2. Add domain generates DNS token
      const newDomain: DomainVerification = {
        id: 'dom-2',
        domain_name: 'stem.alpha.edu',
        is_verified: false,
        verification_token: 'gayatri-verify-abcdef123456',
      };

      global.fetch = vi.fn().mockImplementation((url, init) => {
        if (url.endsWith('/domains') && init.method === 'POST') {
          const body = JSON.parse(init.body as string);
          expect(body.domain_name).toBe('stem.alpha.edu');
          return Promise.resolve({
            ok: true,
            status: 201,
            json: async () => newDomain,
          });
        }
        return Promise.reject(new Error('Unknown endpoint'));
      });

      const added = await client.addAdminDomain('org-alpha', 'stem.alpha.edu');
      expect(added.verification_token).toBe('gayatri-verify-abcdef123456');
      expect(added.is_verified).toBe(false);

      // 3. Verify domain proof
      global.fetch = vi.fn().mockImplementation((url, init) => {
        if (url.endsWith('/verify') && init.method === 'POST') {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({ ...newDomain, is_verified: true }),
          });
        }
        return Promise.reject(new Error('Unknown endpoint'));
      });

      const verified = await client.verifyAdminDomain('org-alpha', 'dom-2');
      expect(verified.is_verified).toBe(true);
    });
  });

  describe('3. Membership & Role Lifecycle (RQ-003 Invariant)', () => {
    it('lists members, updates role assignments, and suspends accounts', async () => {
      client.setToken('admin-jwt-token');

      const mockMembers: OrganizationMember[] = [
        {
          membership_id: 'mem-101',
          user_id: 'usr-101',
          full_name: 'Jane Doe',
          email: 'jane.doe@alpha.edu',
          status: 'active',
          roles: ['STUDENT'],
        },
      ];

      // 1. List members
      global.fetch = vi.fn().mockImplementation(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mockMembers,
        })
      );

      const members = await client.getAdminMembers('org-alpha');
      expect(members).toHaveLength(1);
      expect(members[0].roles).toContain('STUDENT');

      // 2. Update role
      global.fetch = vi.fn().mockImplementation((url, init) => {
        expect(init.method).toBe('PATCH');
        const body = JSON.parse(init.body as string);
        expect(body.new_role).toBe('PARENT');
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({ membership_id: 'mem-101', assigned_role: 'PARENT' }),
        });
      });

      const updated = await client.updateAdminMemberRole('org-alpha', 'mem-101', 'PARENT');
      expect(updated.assigned_role).toBe('PARENT');

      // 3. Suspend member
      global.fetch = vi.fn().mockImplementation((url, init) => {
        expect(init.method).toBe('POST');
        expect(url).toContain('/members/mem-101/suspend');
        return Promise.resolve({
          ok: true,
          status: 204,
          json: async () => ({}),
        });
      });

      await expect(client.suspendAdminMember('org-alpha', 'mem-101')).resolves.toBeUndefined();
    });
  });

  describe('4. AI Routing Policy & Model Whitelist (No Secrets Leaked)', () => {
    it('retrieves and updates AI policy with masked key fingerprints', async () => {
      client.setToken('admin-jwt-token');

      const mockPolicy: AdminAiPolicy = {
        organization_id: 'org-alpha',
        routing_strategy: 'cost_efficient',
        allowed_models: ['gpt-4o', 'claude-3-5-sonnet-20241022'],
        configured_providers: [
          {
            id: 'conn-1',
            provider: 'openai',
            scope: 'organization',
            key_masked: 'sk-...4921',
          },
        ],
      };

      // 1. Get AI Policy
      global.fetch = vi.fn().mockImplementation(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mockPolicy,
        })
      );

      const policy = await client.getAdminAiPolicy('org-alpha');
      expect(policy.routing_strategy).toBe('cost_efficient');
      expect(policy.allowed_models).toContain('gpt-4o');
      expect(policy.configured_providers?.[0].key_masked).toBe('sk-...4921');

      // 2. Update AI Policy
      global.fetch = vi.fn().mockImplementation((url, init) => {
        expect(init.method).toBe('PUT');
        const body = JSON.parse(init.body as string);
        expect(body.allowed_models).toEqual(['gpt-4o', 'gemini-1.5-pro']);
        expect(body.routing_strategy).toBe('quality_first');
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            organization_id: 'org-alpha',
            routing_strategy: 'quality_first',
            allowed_models: ['gpt-4o', 'gemini-1.5-pro'],
          }),
        });
      });

      const updated = await client.updateAdminAiPolicy(
        'org-alpha',
        ['gpt-4o', 'gemini-1.5-pro'],
        'quality_first'
      );
      expect(updated.routing_strategy).toBe('quality_first');
    });
  });

  describe('5. Immutable Audit Trail & Compliance Search', () => {
    it('searches audit trail filtered by event category', async () => {
      client.setToken('admin-jwt-token');

      const mockLogs: AuditLogEntry[] = [
        {
          event_id: 'evt-1',
          event_type: 'AUTH_SESSION_AUTHENTICATED',
          actor_id: 'usr-1',
          sensitivity: 'INTERNAL',
          occurred_at: '2026-10-24T10:00:00Z',
        },
      ];

      global.fetch = vi.fn().mockImplementation((url) => {
        expect(url).toContain('/audit?category=AUTH');
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mockLogs,
        });
      });

      const logs = await client.searchAdminAuditLogs('org-alpha', 'AUTH', 50);
      expect(logs).toHaveLength(1);
      expect(logs[0].event_type).toBe('AUTH_SESSION_AUTHENTICATED');
    });
  });

  describe('6. Organization Suspension & Reactivation Controls', () => {
    it('executes suspension and reactivation with mandatory justification reason', async () => {
      client.setToken('super-admin-jwt-token');

      // 1. Suspend
      global.fetch = vi.fn().mockImplementation((url, init) => {
        expect(url).toContain('/organizations/org-beta/suspend');
        const body = JSON.parse(init.body as string);
        expect(body.reason).toBe('Overdue compliance review');
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            id: 'org-beta',
            status: 'suspended',
            reason: body.reason,
          }),
        });
      });

      const suspended = await client.suspendOrganization('org-beta', 'Overdue compliance review');
      expect(suspended.status).toBe('suspended');

      // 2. Reactivate
      global.fetch = vi.fn().mockImplementation((url, init) => {
        expect(url).toContain('/organizations/org-beta/reactivate');
        const body = JSON.parse(init.body as string);
        expect(body.reason).toBe('Compliance review passed');
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            id: 'org-beta',
            status: 'active',
            reason: body.reason,
          }),
        });
      });

      const reactivated = await client.reactivateOrganization('org-beta', 'Compliance review passed');
      expect(reactivated.status).toBe('active');
    });
  });
});
