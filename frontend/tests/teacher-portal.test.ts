import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiClient, ApiError } from '../src/lib/api-client';
import {
  RosterStudent,
  ClassAnalytics,
  InterventionItem,
  CopilotBriefing,
  TeacherInstructionItem,
} from '../src/lib/types/teacher';

describe('P13 Teacher & Academic Administration Portal — Frontend Architecture & Contracts', () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient('http://localhost:8000');
    vi.restoreAllMocks();
  });

  describe('1. Class Roster & Enrollment Management (RQ-003, RQ-005, RQ-006)', () => {
    it('retrieves class roster with tenant headers and student mastery data', async () => {
      client.setToken('teacher-jwt-token');
      client.setOrganizationId('org-springfield');

      const mockRoster: RosterStudent[] = [
        {
          enrollment_id: 'enr-1',
          student_id: 'usr-bart',
          student_name: 'Bart Simpson',
          email: 'bart@springfield.edu',
          status: 'enrolled',
          enrolled_at: '2026-10-01T10:00:00Z',
          average_mastery: 0.52,
          active_misconceptions: 2,
        },
        {
          enrollment_id: 'enr-2',
          student_id: 'usr-milhouse',
          student_name: 'Milhouse VanHouten',
          email: 'milhouse@springfield.edu',
          status: 'enrolled',
          enrolled_at: '2026-10-02T10:00:00Z',
          average_mastery: 0.65,
          active_misconceptions: 1,
        },
      ];

      let capturedHeaders: Record<string, string> = {};
      global.fetch = vi.fn().mockImplementation((url, init) => {
        capturedHeaders = init.headers;
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mockRoster,
        });
      });

      const roster = await client.getClassRoster('offering-thermo-1');
      expect(roster).toHaveLength(2);
      expect(roster[0].student_name).toBe('Bart Simpson');
      expect(roster[0].average_mastery).toBe(0.52);
      expect(roster[0].active_misconceptions).toBe(2);
      expect(capturedHeaders['Authorization']).toBe('Bearer teacher-jwt-token');
      expect(capturedHeaders['X-Organization-Id']).toBe('org-springfield');
    });

    it('enrolls student into offering with POST payload', async () => {
      client.setToken('teacher-jwt-token');
      client.setOrganizationId('org-springfield');

      let capturedBody = '';
      global.fetch = vi.fn().mockImplementation((url, init) => {
        capturedBody = init.body;
        return Promise.resolve({
          ok: true,
          status: 201,
          json: async () => ({ id: 'enr-3', status: 'enrolled' }),
        });
      });

      const res = await client.enrollStudent('offering-thermo-1', 'usr-lisa');
      expect(res.id).toBe('enr-3');
      expect(JSON.parse(capturedBody)).toEqual({ student_id: 'usr-lisa' });
    });

    it('unenrolls student from offering with DELETE method', async () => {
      client.setToken('teacher-jwt-token');
      client.setOrganizationId('org-springfield');

      let capturedMethod = '';
      global.fetch = vi.fn().mockImplementation((url, init) => {
        capturedMethod = init.method;
        return Promise.resolve({
          ok: true,
          status: 204,
          json: async () => null,
        });
      });

      await client.unenrollStudent('offering-thermo-1', 'usr-milhouse');
      expect(capturedMethod).toBe('DELETE');
    });

    it('rejects cross-tenant access with 403 Forbidden', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 403,
        json: async () => ({ detail: 'Access denied across tenant boundaries.' }),
      } as Response);

      await expect(client.getClassRoster('offering-shelbyville')).rejects.toThrow(
        'Access denied across tenant boundaries.'
      );
    });
  });

  describe('2. 5-Tier Teacher Instruction Cascade (RQ-010, RQ-011)', () => {
    it('creates pedagogical directive across tiers with priority', async () => {
      client.setToken('teacher-jwt-token');
      client.setOrganizationId('org-springfield');

      let capturedBody: any = null;
      global.fetch = vi.fn().mockImplementation((url, init) => {
        capturedBody = JSON.parse(init.body);
        return Promise.resolve({
          ok: true,
          status: 201,
          json: async () => ({
            id: 'inst-99',
            course_id: capturedBody.course_id,
            tier: capturedBody.tier,
            directive_text: capturedBody.directive_text,
            priority: capturedBody.priority,
            is_active: true,
            created_at: new Date().toISOString(),
          }),
        });
      });

      const res = await client.createTeacherInstruction({
        course_id: 'course-thermo',
        tier: 'COURSE',
        directive_text: 'Do not provide formula until student specifies temperature difference.',
        priority: 4,
      });

      expect(res.id).toBe('inst-99');
      expect(res.tier).toBe('COURSE');
      expect(res.priority).toBe(4);
      expect(capturedBody.tier).toBe('COURSE');
    });

    it('lists and deactivates teacher instructions', async () => {
      client.setToken('teacher-jwt-token');
      client.setOrganizationId('org-springfield');

      global.fetch = vi.fn().mockImplementation((url, init) => {
        if (init?.method === 'DELETE') {
          return Promise.resolve({ ok: true, status: 204, json: async () => null });
        }
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => [
            {
              id: 'inst-1',
              course_id: 'course-thermo',
              tier: 'COURSE',
              directive_text: 'Active directive',
              priority: 5,
              is_active: true,
              created_at: '2026-10-01T00:00:00Z',
            },
          ],
        });
      });

      const list = await client.getTeacherInstructions('course-thermo');
      expect(list).toHaveLength(1);
      expect(list[0].priority).toBe(5);

      await expect(client.deactivateTeacherInstruction('inst-1')).resolves.not.toThrow();
    });
  });

  describe('3. Class Analytics & Misconception Clustering (RQ-013, RQ-038)', () => {
    it('processes cohort mastery distribution, hardest concepts, and misconception clusters', async () => {
      const mockAnalytics: ClassAnalytics = {
        total_students: 30,
        average_mastery: 0.71,
        mastery_distribution: {
          novice: 2,
          developing: 6,
          competent: 12,
          proficient: 7,
          master: 3,
        },
        hardest_concepts: [
          { concept_id: 'carnot_cycle', average_score: 0.38, attempts: 55 },
          { concept_id: 'entropy_derivation', average_score: 0.49, attempts: 42 },
        ],
        misconception_clusters: [
          {
            concept_id: 'carnot_cycle',
            description: 'Assuming efficiency can equal 100% at nonzero sink temp.',
            student_count: 5,
          },
        ],
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockAnalytics,
      } as Response);

      const analytics = await client.getClassAnalytics('offering-thermo-1');
      expect(analytics.total_students).toBe(30);
      expect(analytics.average_mastery).toBe(0.71);
      expect(analytics.mastery_distribution.competent).toBe(12);
      expect(analytics.hardest_concepts[0].concept_id).toBe('carnot_cycle');
      expect(analytics.hardest_concepts[0].average_score).toBe(0.38);
      expect(analytics.misconception_clusters[0].student_count).toBe(5);
    });
  });

  describe('4. Intervention Queue & Teacher Acknowledgement (RQ-010, RQ-026)', () => {
    it('retrieves active intervention queue and acknowledges with notes', async () => {
      const mockInterventions: InterventionItem[] = [
        {
          id: 'int-101',
          student_id: 'usr-bart',
          student_name: 'Bart Simpson',
          concept_id: 'carnot_cycle',
          severity: 'HIGH',
          reason: '3 consecutive failed assessments on heat engine efficiency.',
          status: 'PENDING',
          created_at: '2026-10-23T14:00:00Z',
        },
      ];

      let capturedBody: any = null;
      global.fetch = vi.fn().mockImplementation((url, init) => {
        if (init?.method === 'POST') {
          capturedBody = JSON.parse(init.body);
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              ...mockInterventions[0],
              status: capturedBody.resolve ? 'RESOLVED' : 'ACKNOWLEDGED',
              resolution_notes: capturedBody.resolution_notes,
            }),
          });
        }
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mockInterventions,
        });
      });

      const queue = await client.getInterventionQueue('offering-thermo-1');
      expect(queue).toHaveLength(1);
      expect(queue[0].severity).toBe('HIGH');

      const ack = await client.acknowledgeIntervention(
        'int-101',
        'Assigned targeted Socratic drill on temperature differentials.',
        true
      );
      expect(ack.status).toBe('RESOLVED');
      expect(ack.resolution_notes).toBe(
        'Assigned targeted Socratic drill on temperature differentials.'
      );
      expect(capturedBody.resolve).toBe(true);
    });
  });

  describe('5. Teacher Copilot Briefing & Grounding Protocol (RQ-010, RQ-038)', () => {
    it('enforces empirical evidence grounding, uncertainty disclosure, and teacher confirmation', async () => {
      const mockBriefing: CopilotBriefing = {
        summary:
          'Cohort shows high proficiency in isobaric calculations but 5 learners struggle with cyclic Carnot efficiency.',
        evidence_sources: [
          '30 student chat transcripts',
          'Milestone 1 assessment log',
          'Canonical learning stability decay curve',
        ],
        confidence_score: 0.88,
        uncertainty_note:
          'Grounding: empirical student logs. Teacher confirmation required before applying instructional modifications.',
        bottleneck_concepts: ['carnot_cycle'],
        suggested_actions: [
          'Introduce interactive PV diagram before equation derivation.',
          'Inject student-tier directive for 5 learners.',
        ],
        requires_teacher_confirmation: true,
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockBriefing,
      } as Response);

      const briefing = await client.getCopilotBriefing('offering-thermo-1');
      expect(briefing.confidence_score).toBe(0.88);
      expect(briefing.requires_teacher_confirmation).toBe(true);
      expect(briefing.evidence_sources).toHaveLength(3);
      expect(briefing.uncertainty_note).toContain('Teacher confirmation required');
      expect(briefing.suggested_actions).toHaveLength(2);
    });
  });
});
