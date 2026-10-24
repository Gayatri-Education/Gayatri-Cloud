import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiClient } from '../src/lib/api-client';
import {
  LinkedChild,
  ChildProgressSummary,
  ChildAssessmentReport,
  ChildCommunicationItem,
} from '../src/lib/types/parent';

describe('P14 Parent & Guardian Portal — Frontend Architecture & Contracts', () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient('http://localhost:8000');
    vi.restoreAllMocks();
  });

  describe('1. Guardian Link Management (RQ-003, RQ-005, RQ-006)', () => {
    it('retrieves linked children list with verification statuses', async () => {
      client.setToken('parent-jwt-token');
      client.setOrganizationId('org-springfield');

      const mockChildren: LinkedChild[] = [
        {
          relationship_id: 'rel-1',
          student_id: 'usr-bart',
          student_name: 'Bart Simpson',
          email: 'bart@springfield.edu',
          verification_status: 'verified',
          is_active: true,
          average_mastery: 0.58,
          active_courses_count: 2,
          linked_at: '2026-10-01T10:00:00Z',
        },
        {
          relationship_id: 'rel-2',
          student_id: 'usr-lisa',
          student_name: 'Lisa Simpson',
          email: 'lisa@springfield.edu',
          verification_status: 'pending',
          is_active: true,
          average_mastery: 0.96,
          active_courses_count: 3,
          linked_at: '2026-10-05T10:00:00Z',
        },
      ];

      let capturedHeaders: Record<string, string> = {};
      global.fetch = vi.fn().mockImplementation((url, init) => {
        capturedHeaders = init.headers;
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mockChildren,
        });
      });

      const children = await client.getLinkedChildren();
      expect(children).toHaveLength(2);
      expect(children[0].student_name).toBe('Bart Simpson');
      expect(children[0].verification_status).toBe('verified');
      expect(children[1].verification_status).toBe('pending');
      expect(capturedHeaders['Authorization']).toBe('Bearer parent-jwt-token');
      expect(capturedHeaders['X-Organization-Id']).toBe('org-springfield');
    });

    it('submits a student link request with identifier payload', async () => {
      client.setToken('parent-jwt-token');

      let capturedBody: any = null;
      global.fetch = vi.fn().mockImplementation((url, init) => {
        capturedBody = JSON.parse(init.body);
        return Promise.resolve({
          ok: true,
          status: 201,
          json: async () => ({
            relationship_id: 'rel-3',
            student_id: 'usr-maggie',
            student_name: 'Maggie Simpson',
            email: capturedBody.student_identifier,
            verification_status: 'pending',
            is_active: true,
            average_mastery: 0,
            active_courses_count: 0,
            linked_at: new Date().toISOString(),
          }),
        });
      });

      const res = await client.requestStudentLink('maggie@springfield.edu');
      expect(res.verification_status).toBe('pending');
      expect(capturedBody.student_identifier).toBe('maggie@springfield.edu');
    });

    it('immediately revokes guardian link with DELETE call', async () => {
      client.setToken('parent-jwt-token');

      let capturedMethod = '';
      global.fetch = vi.fn().mockImplementation((url, init) => {
        capturedMethod = init.method;
        return Promise.resolve({
          ok: true,
          status: 204,
          json: async () => null,
        });
      });

      await client.revokeGuardianLink('rel-1');
      expect(capturedMethod).toBe('DELETE');
    });

    it('rejects access to unlinked student with 403 Forbidden', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 403,
        json: async () => ({
          detail: 'Access denied: No verified guardian relationship for this student.',
        }),
      } as Response);

      await expect(client.getChildProgress('usr-unlinked')).rejects.toThrow(
        'Access denied: No verified guardian relationship for this student.'
      );
    });
  });

  describe('2. Privacy-Filtered Progress Invariant (RQ-025)', () => {
    it('returns summarized learning mastery without raw conversation transcripts', async () => {
      const mockProgress: ChildProgressSummary = {
        student_id: 'usr-bart',
        overall_mastery: 0.58,
        total_tutoring_sessions: 14,
        estimated_study_minutes: 350,
        active_misconceptions_count: 2,
        top_concepts: [
          { concept_id: 'heat_capacity', mastery_score: 0.72, stability_days: 10 },
          { concept_id: 'carnot_cycle', mastery_score: 0.45, stability_days: 4 },
        ],
        enrolled_courses: [{ title: 'Introductory Science', term: 'Fall 2026' }],
        privacy_disclosure:
          'Parent Portal Privacy Protocol: Raw conversational turns are excluded from parent views to maintain learner safe-space and autonomous Socratic inquiry.',
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockProgress,
      } as Response);

      const progress = await client.getChildProgress('usr-bart');
      expect(progress.overall_mastery).toBe(0.58);
      expect(progress.top_concepts).toHaveLength(2);
      expect(progress.privacy_disclosure).toContain('Raw conversational turns are excluded');

      // Assert absence of any raw conversation dialogue keys
      expect((progress as any).conversation_turns).toBeUndefined();
      expect((progress as any).raw_turns).toBeUndefined();
      expect((progress as any).messages).toBeUndefined();
    });
  });

  describe('3. Multi-Child Assessment Reports & Communications (RQ-006, RQ-026)', () => {
    it('retrieves completed assessment reports for linked child', async () => {
      const mockAssessments: ChildAssessmentReport[] = [
        {
          attempt_id: 'att-1',
          assessment_id: 'asm-1',
          title: 'Science Milestone 1',
          score: 42,
          max_points: 50,
          percentage: 84,
          submitted_at: '2026-10-20T14:00:00Z',
          status: 'graded',
        },
      ];

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockAssessments,
      } as Response);

      const list = await client.getChildAssessments('usr-bart');
      expect(list).toHaveLength(1);
      expect(list[0].title).toBe('Science Milestone 1');
      expect(list[0].percentage).toBe(84);
      expect(list[0].status).toBe('graded');
    });

    it('retrieves teacher announcements for child enrolled offerings', async () => {
      const mockComms: ChildCommunicationItem[] = [
        {
          id: 'comm-1',
          offering_id: 'off-1',
          title: 'Science Fair Project Due Date',
          content: 'Please submit topic proposals by next Monday.',
          teacher_name: 'Edna Krabappel',
          posted_at: '2026-10-22T09:00:00Z',
        },
      ];

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockComms,
      } as Response);

      const comms = await client.getChildCommunications('usr-bart');
      expect(comms).toHaveLength(1);
      expect(comms[0].title).toBe('Science Fair Project Due Date');
      expect(comms[0].teacher_name).toBe('Edna Krabappel');
    });
  });
});
