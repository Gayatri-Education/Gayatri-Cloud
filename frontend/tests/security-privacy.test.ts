import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiClient } from '../src/lib/api-client';
import { UserDataExport, DeletionRequestStatus, SecurityAuditEntry } from '../src/lib/types/security';

describe('P18 Security, Privacy, Retention & Deletion Hardening — Frontend Tests', () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient('http://localhost:8000');
    vi.restoreAllMocks();
  });

  describe('1. Machine-Readable Data Export (GDPR Art. 20)', () => {
    it('retrieves user personal data export with valid SHA-256 checksum', async () => {
      const mockExport: UserDataExport = {
        export_version: '1.0',
        exported_at: new Date().toISOString(),
        checksum_sha256: 'a1b2c3d4e5f67890123456789012345678901234567890123456789012345678',
        user_profile: {
          id: 'usr-101',
          email: 'alice@example.com',
          full_name: 'Alice Learner',
          created_at: new Date().toISOString(),
          is_verified: true,
        },
        memberships: [
          {
            organization_id: 'org-1',
            membership_id: 'mem-1',
            status: 'active',
            role: 'STUDENT',
            joined_at: new Date().toISOString(),
          },
        ],
        enrollments: [
          {
            enrollment_id: 'enr-1',
            offering_id: 'off-1',
            status: 'enrolled',
            enrolled_at: new Date().toISOString(),
          },
        ],
        assessment_attempts: [
          {
            attempt_id: 'att-1',
            assessment_id: 'asm-1',
            status: 'submitted',
            score: 95.0,
            submitted_at: new Date().toISOString(),
          },
        ],
        tutoring_sessions: [
          {
            session_id: 'tut-1',
            course_id: 'crs-1',
            status: 'completed',
            created_at: new Date().toISOString(),
          },
        ],
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockExport,
      } as any);

      const res = await client.getDataExport();
      expect(res.user_profile.id).toBe('usr-101');
      expect(res.memberships).toHaveLength(1);
      expect(res.assessment_attempts[0].score).toBe(95.0);
      expect(res.checksum_sha256).toHaveLength(64);
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/security/export',
        expect.anything()
      );
    });
  });

  describe('2. Account Deletion & Right to be Forgotten Lifecycle', () => {
    it('initiates account deletion with grace period', async () => {
      const mockDeletionResponse = {
        request_id: 'del-101',
        status: 'pending',
        message: 'Deletion request scheduled. You have a 7-day grace period to cancel.',
        grace_period_expires_at: new Date(Date.now() + 7 * 86400000).toISOString(),
        legal_hold_retained_records: null,
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockDeletionResponse,
      } as any);

      const res = await client.requestAccountDeletion('Graduated', false);
      expect(res.request_id).toBe('del-101');
      expect(res.status).toBe('pending');
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/security/deletion-request',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ reason: 'Graduated', immediate: false }),
        })
      );
    });

    it('retrieves deletion status and checks active request', async () => {
      const mockStatus: DeletionRequestStatus = {
        has_active_request: true,
        request_id: 'del-101',
        status: 'pending',
        grace_period_expires_at: new Date(Date.now() + 7 * 86400000).toISOString(),
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockStatus,
      } as any);

      const res = await client.getDeletionStatus();
      expect(res.has_active_request).toBe(true);
      expect(res.status).toBe('pending');
    });

    it('cancels pending deletion request during grace period', async () => {
      const mockCancelResponse = {
        request_id: 'del-101',
        status: 'cancelled',
        message: 'Deletion request cancelled. Account access restored.',
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockCancelResponse,
      } as any);

      const res = await client.cancelDeletionRequest();
      expect(res.status).toBe('cancelled');
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/security/deletion-request/cancel',
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  describe('3. Security & Access Audit Trail', () => {
    it('retrieves immutable security audit logs', async () => {
      const mockAuditLogs: SecurityAuditEntry[] = [
        {
          id: 'log-1',
          action: 'LOGIN',
          ip_address: '198.51.100.1',
          status: 'success',
          details: 'User logged in via password',
          timestamp: new Date().toISOString(),
        },
        {
          id: 'log-2',
          action: 'EXPORT_DOWNLOAD',
          ip_address: '198.51.100.1',
          status: 'success',
          details: 'Data export downloaded',
          timestamp: new Date().toISOString(),
        },
      ];

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockAuditLogs,
      } as any);

      const res = await client.getSecurityAudit();
      expect(res).toHaveLength(2);
      expect(res[0].action).toBe('LOGIN');
      expect(res[1].action).toBe('EXPORT_DOWNLOAD');
    });
  });
});
