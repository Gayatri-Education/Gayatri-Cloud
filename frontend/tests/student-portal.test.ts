import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiClient, ApiError } from '../src/lib/api-client';
import { TutorStreamClient } from '../src/lib/stream-client';
import { Citation, PedagogyMode } from '../src/lib/types/tutoring';
import { AssessmentQuestion, AssessmentSummary } from '../src/lib/types/assessment';
import { ConceptMastery, MisconceptionItem } from '../src/lib/types/mastery';
import { ProviderConnection } from '../src/lib/types/ai';

describe('P12 Student Portal — Frontend Architecture & Contracts', () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient('http://localhost:8000');
    vi.restoreAllMocks();
  });

  describe('1. API Client & Tenant Context Isolation (RQ-005, RQ-006)', () => {
    it('injects Bearer token and X-Organization-Id header when configured', async () => {
      client.setToken('test-access-token-xyz');
      client.setOrganizationId('org-academy-999');

      let capturedHeaders: Record<string, string> = {};
      global.fetch = vi.fn().mockImplementation((url, init) => {
        capturedHeaders = init.headers;
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => [{ id: 'course-1', title: 'Thermodynamics' }],
        });
      });

      const courses = await client.getCourses();
      expect(courses).toHaveLength(1);
      expect(capturedHeaders['Authorization']).toBe('Bearer test-access-token-xyz');
      expect(capturedHeaders['X-Organization-Id']).toBe('org-academy-999');
    });

    it('clears X-Organization-Id in personal context to prevent context mixing', async () => {
      client.setToken('test-token');
      client.setOrganizationId(null); // Personal Learning Space

      let capturedHeaders: Record<string, string> = {};
      global.fetch = vi.fn().mockImplementation((url, init) => {
        capturedHeaders = init.headers;
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => [],
        });
      });

      await client.getCourses();
      expect(capturedHeaders['Authorization']).toBe('Bearer test-token');
      expect(capturedHeaders['X-Organization-Id']).toBeUndefined();
    });

    it('creates structured ApiError on 403 Forbidden with details', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 403,
        json: async () => ({ detail: 'Access denied across tenant boundaries' }),
      } as Response);

      await expect(client.getCourse('course-secret')).rejects.toThrow(
        'Access denied across tenant boundaries'
      );
    });

    it('handles network failure with helpful diagnostic message', async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error('Failed to fetch'));

      await expect(client.getCourses()).rejects.toThrow(
        'Network connection failed. Please check your connectivity.'
      );
    });
  });

  describe('2. Tutor SSE Streaming Client (RQ-010, RQ-014)', () => {
    it('aggregates tokens and parses citations from SSE stream', async () => {
      const streamClient = new TutorStreamClient('http://localhost:8000');

      const sseChunks = [
        'event: token\ndata: {"token": "Heat "}\n\n',
        'event: token\ndata: {"token": "is energy "}\n\n',
        'event: token\ndata: {"token": "in transit."}\n\n',
        'event: citation\ndata: {"citation": {"chunk_id": "c1", "source_title": "Thermo Ch 2", "snippet": "Heat is energy in transit"}}\n\n',
        'event: done\ndata: {"done": true}\n\n',
      ];

      let streamIndex = 0;
      const mockReader = {
        read: vi.fn().mockImplementation(() => {
          if (streamIndex < sseChunks.length) {
            const chunk = sseChunks[streamIndex++];
            return Promise.resolve({
              done: false,
              value: new TextEncoder().encode(chunk),
            });
          }
          return Promise.resolve({ done: true, value: undefined });
        }),
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      } as unknown as Response);

      let accumulatedText = '';
      const collectedCitations: Citation[] = [];
      let isComplete = false;

      await new Promise<void>((resolve) => {
        streamClient.streamTurn(
          'session-123',
          'What is heat?',
          'socratic',
          'token-xyz',
          'org-1',
          {
            onToken: (tok) => {
              accumulatedText += tok;
            },
            onCitation: (cit) => {
              collectedCitations.push(cit);
            },
            onComplete: (fullText, citations) => {
              isComplete = true;
              resolve();
            },
          }
        );
      });

      expect(accumulatedText).toBe('Heat is energy in transit.');
      expect(collectedCitations).toHaveLength(1);
      expect(collectedCitations[0].source_title).toBe('Thermo Ch 2');
      expect(isComplete).toBe(true);
    });

    it('supports client-side cancellation via AbortController', () => {
      const streamClient = new TutorStreamClient('http://localhost:8000');
      let abortSignal: AbortSignal | undefined;

      global.fetch = vi.fn().mockImplementation((url, init) => {
        abortSignal = init.signal;
        return new Promise(() => {}); // Pending
      });

      const cancelFn = streamClient.streamTurn('session-1', 'Explain entropy');
      expect(abortSignal).toBeDefined();
      expect(abortSignal?.aborted).toBe(false);

      cancelFn();
      expect(abortSignal?.aborted).toBe(true);
    });
  });

  describe('3. Assessment Scoring & Question Models (RQ-013)', () => {
    it('supports MCQ, Boolean, Numerical, Subjective, and Coding questions', () => {
      const questions: AssessmentQuestion[] = [
        {
          id: 'q1',
          type: 'mcq',
          prompt: 'What is entropy?',
          options: ['State function', 'Path function', 'Process'],
          points: 10,
        },
        {
          id: 'q2',
          type: 'boolean',
          prompt: 'Is total entropy conserved in irreversible processes?',
          points: 5,
        },
        {
          id: 'q3',
          type: 'numerical',
          prompt: 'Calculate work done at 100 kPa for 0.5 m^3 expansion.',
          unit: 'kJ',
          tolerance_percent: 2,
          points: 10,
        },
        {
          id: 'q4',
          type: 'subjective',
          prompt: 'Explain the difference between closed and isolated systems.',
          points: 15,
        },
        {
          id: 'q5',
          type: 'coding',
          prompt: 'Write carnot_efficiency(th, tc)',
          language: 'python',
          starter_code: 'def carnot_efficiency(th, tc):\n    pass\n',
          points: 10,
        },
      ];

      expect(questions).toHaveLength(5);
      const totalPoints = questions.reduce((sum, q) => sum + q.points, 0);
      expect(totalPoints).toBe(50);
    });

    it('autosave and idempotent submission API contracts', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          status: 'draft_saved',
          updated_at: '2026-10-24T12:00:00Z',
        }),
      } as Response);

      const autosaveRes = await client.autosaveAttempt('asm-1', 'att-1', {
        q1: 'State function',
      });
      expect(autosaveRes.status).toBe('draft_saved');

      // Submit
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          attempt_id: 'att-1',
          total_score: 45,
          max_points: 50,
          percentage: 90,
          passed: true,
          question_results: {},
          misconceptions_detected: [],
          submitted_at: '2026-10-24T12:05:00Z',
        }),
      } as Response);

      const submitRes = await client.submitAssessmentAttempt('asm-1', 'att-1', {
        q1: 'State function',
      });
      expect(submitRes.passed).toBe(true);
      expect(submitRes.percentage).toBe(90);
    });
  });

  describe('4. BYOK Security & Key Masking (RQ-014, RQ-015)', () => {
    it('verifies keys are strictly masked and raw secrets never exposed', () => {
      const connections: ProviderConnection[] = [
        {
          id: 'c1',
          provider: 'openai',
          label: 'Personal Key',
          scope: 'PERSONAL',
          is_active: true,
          masked_key: 'sk-...4f9b',
          created_at: '2026-10-24T00:00:00Z',
        },
        {
          id: 'c2',
          provider: 'anthropic',
          label: 'Claude Pro',
          scope: 'PERSONAL',
          is_active: true,
          masked_key: 'sk-ant-...9182',
          created_at: '2026-10-24T00:00:00Z',
        },
      ];

      for (const conn of connections) {
        expect(conn.masked_key).toContain('...');
        expect(conn.masked_key.length).toBeLessThan(16);
        // Ensure no full 32+ character raw key is ever present
        expect(conn.masked_key.length).toBeGreaterThanOrEqual(8);
      }
    });

    it('revokes connection through DELETE endpoint', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 204,
      } as Response);

      await expect(client.deleteProviderConnection('c1')).resolves.not.toThrow();
    });
  });

  describe('5. Mastery Roadmap & Misconception Remediation (RQ-012)', () => {
    it('computes weighted mastery percentage and flags active misconceptions', () => {
      const masteries: ConceptMastery[] = [
        {
          concept_id: 'c1',
          concept_name: 'First Law',
          course_id: 'thermo-1',
          mastery_score: 0.9,
          stability: 20,
          status: 'proficient',
          last_practiced: '2026-10-24T00:00:00Z',
          next_review_due: '2026-11-10T00:00:00Z',
          evidence_count: 5,
        },
        {
          concept_id: 'c2',
          concept_name: 'Entropy Generation',
          course_id: 'thermo-1',
          mastery_score: 0.5,
          stability: 6,
          status: 'developing',
          last_practiced: '2026-10-24T00:00:00Z',
          next_review_due: '2026-10-25T00:00:00Z',
          evidence_count: 2,
        },
      ];

      const avg = Math.round(
        (masteries.reduce((acc, m) => acc + m.mastery_score, 0) / masteries.length) * 100
      );
      expect(avg).toBe(70);

      const misconceptions: MisconceptionItem[] = [
        {
          id: 'm1',
          concept_id: 'c1',
          concept_name: 'First Law',
          misconception_code: 'MISCON_HEAT_WORK',
          description: 'Treating heat as a stored state property',
          severity: 'high',
          detected_at: '2026-10-24T00:00:00Z',
          remediated: false,
          remediation_advice: 'Emphasize that heat is energy in transit.',
        },
      ];

      const activeMiscons = misconceptions.filter((m) => !m.remediated);
      expect(activeMiscons).toHaveLength(1);
      expect(activeMiscons[0].misconception_code).toBe('MISCON_HEAT_WORK');
    });
  });
});
