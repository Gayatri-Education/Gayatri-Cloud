import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiClient } from '../src/lib/api-client';
import { SUPPORTED_LANGUAGES, TRANSLATIONS } from '../src/lib/i18n/catalogs';
import { OfflineStorage, OfflineBundle } from '../src/lib/offline/offline-storage';

class LocalStorageMock {
  private store: Record<string, string> = {};
  clear() {
    this.store = {};
  }
  getItem(key: string) {
    return this.store[key] || null;
  }
  setItem(key: string, value: string) {
    this.store[key] = String(value);
  }
  removeItem(key: string) {
    delete this.store[key];
  }
}

describe('P20 Integrated System Journey & Cross-Portal E2E Tests', () => {
  let client: ApiClient;
  const mockStorage = new LocalStorageMock();

  beforeEach(() => {
    (global as any).localStorage = mockStorage;
    (global as any).window = global;
    mockStorage.clear();
    client = new ApiClient('http://localhost:8000');
    vi.restoreAllMocks();
  });

  describe('1. Integrated Authentication & Multi-Tenant Context Switching', () => {
    it('manages token storage, active session, and tenant switching', () => {
      // Set session token
      client.setToken('jwt-access-token-pilot-user');
      expect(client.getToken()).toBe('jwt-access-token-pilot-user');

      // Set active tenant context
      client.setOrganizationId('org-iit-bombay-2026');
      expect(client.getOrganizationId()).toBe('org-iit-bombay-2026');

      // Switch to personal / independent learner context
      client.setOrganizationId(null);
      expect(client.getOrganizationId()).toBeNull();

      // Clear tokens on logout
      client.logout();
      expect(client.getToken()).toBeNull();
      expect(client.getOrganizationId()).toBeNull();
    });
  });

  describe('2. Multi-Portal End-to-End Navigation & Domain Contracts', () => {
    it('traverses the Student journey: courses, adaptive tutoring, and assessments', async () => {
      client.setToken('student-auth-token');
      client.setOrganizationId('org-iitb');

      const mockFetch = vi.fn().mockImplementation((url: string) => {
        if (url.includes('/api/v1/courses')) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve([
                {
                  id: 'course-cs-101',
                  code: 'CS-101',
                  title: 'Distributed Systems',
                  status: 'published',
                },
              ]),
          });
        }
        if (url.includes('/api/v1/tutoring/mastery')) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve([
                {
                  concept_id: 'c_consensus',
                  mastery_score: 0.92,
                  state: 'mastered',
                },
              ]),
          });
        }
        return Promise.reject(new Error(`Unhandled route ${url}`));
      });
      (global as any).fetch = mockFetch;

      const courses = await client.getCourses();
      expect(courses).toHaveLength(1);
      expect(courses[0].code).toBe('CS-101');

      const masteries = await client.getConceptMasteries();
      expect(masteries).toHaveLength(1);
      expect(masteries[0].concept_id).toBe('c_consensus');
    });

    it('traverses the Teacher journey: roster, 5-tier directives, and interventions', async () => {
      client.setToken('teacher-auth-token');
      client.setOrganizationId('org-iitb');

      const mockFetch = vi.fn().mockImplementation((url: string) => {
        if (url.includes('/api/v1/teacher/instructions')) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve([
                {
                  id: 'inst-1',
                  tier: 'COURSE',
                  directive_text: 'Use Socratic hints before explaining Paxos.',
                  is_active: true,
                },
              ]),
          });
        }
        if (url.includes('/interventions')) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve([
                {
                  id: 'interv-1',
                  student_id: 'student-ananya',
                  severity: 'HIGH',
                  status: 'RESOLVED',
                },
              ]),
          });
        }
        return Promise.reject(new Error(`Unhandled route ${url}`));
      });
      (global as any).fetch = mockFetch;

      const instructions = await client.getTeacherInstructions('course-cs-101');
      expect(instructions).toHaveLength(1);
      expect(instructions[0].directive_text).toContain('Socratic');

      const queue = await client.getInterventionQueue('offering-autumn-2026');
      expect(queue).toHaveLength(1);
      expect(queue[0].severity).toBe('HIGH');
      expect(queue[0].status).toBe('RESOLVED');
    });

    it('traverses the Parent journey: verified child progress and assessment reports', async () => {
      client.setToken('parent-auth-token');

      const mockFetch = vi.fn().mockImplementation((url: string) => {
        if (url.includes('/api/v1/parent/children')) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve([
                {
                  relationship_id: 'rel-1',
                  student_id: 'student-ananya',
                  student_name: 'Ananya Roy',
                  verification_status: 'verified',
                  average_mastery: 0.88,
                },
              ]),
          });
        }
        return Promise.reject(new Error(`Unhandled route ${url}`));
      });
      (global as any).fetch = mockFetch;

      const children = await client.getLinkedChildren();
      expect(children).toHaveLength(1);
      expect(children[0].student_name).toBe('Ananya Roy');
      expect(children[0].verification_status).toBe('verified');
    });

    it('traverses the Billing & Entitlements journey: fee schedules and checkout', async () => {
      client.setToken('admin-auth-token');
      client.setOrganizationId('org-iitb');

      const mockFetch = vi.fn().mockImplementation((url: string) => {
        if (url.includes('/api/v1/billing/institution/fees')) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve([
                {
                  id: 'fee-lab-compute',
                  title: 'Lab & Cloud Computing Fee',
                  amount_cents: 15000,
                  currency: 'USD',
                  status: 'active',
                },
              ]),
          });
        }
        return Promise.reject(new Error(`Unhandled route ${url}`));
      });
      (global as any).fetch = mockFetch;

      const fees = await client.getInstitutionFees('org-iitb');
      expect(fees).toHaveLength(1);
      expect(fees[0].amount_cents).toBe(15000);
      expect(fees[0].title).toContain('Cloud Computing');
    });

    it('traverses Security & Privacy journey: data export archive and legal hold', async () => {
      client.setToken('student-auth-token');

      const mockFetch = vi.fn().mockImplementation((url: string, opts: any) => {
        if (url.includes('/api/v1/security/export')) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                user_profile: { id: 'student-ananya', email: 'ananya@iit.ac.in' },
                checksum_sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
                exported_at: '2026-10-24T14:48:00Z',
              }),
          });
        }
        if (url.includes('/api/v1/security/deletion-request') && opts?.method === 'POST') {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                request_id: 'del-req-1',
                status: 'completed',
                message: 'Account permanently deleted and statutory financial records preserved.',
                legal_hold_retained_records: ['fee_payments', 'invoices'],
              }),
          });
        }
        return Promise.reject(new Error(`Unhandled route ${url}`));
      });
      (global as any).fetch = mockFetch;

      const exportArchive = await client.getDataExport('student-ananya');
      expect(exportArchive.checksum_sha256).toHaveLength(64);

      const delRes = await client.requestAccountDeletion('Graduation', true, 'student-ananya');
      expect(delRes.status).toBe('completed');
      expect(delRes.legal_hold_retained_records).toContain('fee_payments');
    });
  });

  describe('3. Multilingual, Accessibility & Offline Integrated Reading', () => {
    it('verifies 8-language translations and fallback robustness across portals', () => {
      expect(SUPPORTED_LANGUAGES).toHaveLength(8);

      for (const lang of SUPPORTED_LANGUAGES) {
        const cat = TRANSLATIONS[lang.code as keyof typeof TRANSLATIONS];
        expect(cat).toBeDefined();
        expect(cat.courses).toBeTruthy();
        expect(cat.tutor).toBeTruthy();
        expect(cat.assessments).toBeTruthy();
      }

      // Check specific Indian language translations
      expect(TRANSLATIONS.te.assessments).toBe('మూల్యాంకనాలు');
      expect(TRANSLATIONS.kn.courses).toBe('ಕೋರ್ಸ್‌ಗಳು');
      expect(TRANSLATIONS.bn.dashboard).toBe('ড্যাশবোর্ড');
    });

    it('bundles offline content, persists to storage, and validates integrity check', () => {
      const bundle: OfflineBundle = {
        course_id: 'course-distributed-systems',
        course_title: 'Distributed Systems & Cloud Computing',
        description: 'Consensus algorithms, Raft, Paxos, and fault tolerance.',
        version_id: 'ver-1-0-0',
        version_tag: 'v1.0.0',
        sha256_checksum: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        packaged_at: '2026-10-24T14:48:00Z',
        lessons_count: 2,
        lessons: [
          {
            chunk_id: 'chk-1',
            title: 'Introduction to Raft',
            content_text: 'Raft is a consensus algorithm designed to be understandable.',
            sequence_order: 0,
            token_count: 12,
          },
          {
            chunk_id: 'chk-2',
            title: 'Leader Election',
            content_text: 'Followers timeout and trigger elections.',
            sequence_order: 1,
            token_count: 14,
          },
        ],
        offline_guidance: 'Reading mode active. Live AI tutoring requires reconnection.',
      };

      OfflineStorage.saveBundle(bundle);

      const saved = OfflineStorage.getBundle('course-distributed-systems');
      expect(saved).not.toBeNull();
      expect(saved?.course_id).toBe('course-distributed-systems');
      expect(saved?.lessons).toHaveLength(2);
      expect(saved?.sha256_checksum).toBe('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855');

      const all = OfflineStorage.listBundles();
      expect(all).toHaveLength(1);

      OfflineStorage.removeBundle('course-distributed-systems');
      expect(OfflineStorage.getBundle('course-distributed-systems')).toBeNull();
    });
  });
});
