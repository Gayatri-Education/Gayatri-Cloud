/**
 * Gayatri Cloud Typed REST API Client.
 * Handles JWT token injection, tenant context headers, and typed responses.
 */

import { AuthTokens, UserProfile, OrganizationMembership } from './types/auth';
import { Course, CourseOffering, CourseEnrollment } from './types/course';
import { TutoringSession, TutorTurnRequest, TutorTurnResponse } from './types/tutoring';
import {
  AssessmentSummary,
  AssessmentQuestion,
  AssessmentAttempt,
  EvaluationResult,
} from './types/assessment';
import {
  ConceptMastery,
  MisconceptionItem,
  SpacedReviewReminder,
  StudyActivity,
} from './types/mastery';
import { ProviderConnection, ModelInfo, PrivacyConsentSettings } from './types/ai';
import {
  RosterStudent,
  ClassAnalytics,
  InterventionItem,
  CopilotBriefing,
  TeacherInstructionItem,
  ClassAnnouncementItem,
} from './types/teacher';

export class ApiError extends Error {
  public status: number;
  public details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

export class ApiClient {
  private baseUrl: string;
  private token: string | null = null;
  private organizationId: string | null = null;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('gc_access_token');
      this.organizationId = localStorage.getItem('gc_org_id');
    }
  }

  public setToken(token: string | null): void {
    this.token = token;
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('gc_access_token', token);
      } else {
        localStorage.removeItem('gc_access_token');
      }
    }
  }

  public getToken(): string | null {
    return this.token;
  }

  public setOrganizationId(orgId: string | null): void {
    this.organizationId = orgId;
    if (typeof window !== 'undefined') {
      if (orgId) {
        localStorage.setItem('gc_org_id', orgId);
      } else {
        localStorage.removeItem('gc_org_id');
      }
    }
  }

  public getOrganizationId(): string | null {
    return this.organizationId;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    if (this.organizationId) {
      headers['X-Organization-Id'] = this.organizationId;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        let errorMessage = `Request failed with status ${response.status}`;
        let details: unknown = null;
        try {
          const errorJson = await response.json();
          errorMessage = errorJson.detail || errorJson.message || errorMessage;
          details = errorJson;
        } catch {
          // Non-JSON error
        }
        throw new ApiError(errorMessage, response.status, details);
      }

      if (response.status === 204) {
        return {} as T;
      }

      return (await response.json()) as T;
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        throw err;
      }
      const rawMsg = (err as Error).message || '';
      const msg =
        rawMsg.includes('Failed to fetch') || rawMsg.includes('NetworkError')
          ? 'Network connection failed. Please check your connectivity.'
          : rawMsg || 'Network connection failed. Please check your connectivity.';
      throw new ApiError(msg, 0);
    }
  }

  // Auth Endpoints
  public async login(formData: FormData | Record<string, string>): Promise<AuthTokens> {
    let body: string;
    let contentType = 'application/json';

    if (formData instanceof FormData) {
      const obj: Record<string, string> = {};
      formData.forEach((val, key) => {
        obj[key] = val.toString();
      });
      body = JSON.stringify(obj);
    } else {
      body = JSON.stringify(formData);
    }

    const tokens = await this.request<AuthTokens>('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': contentType },
      body,
    });
    this.setToken(tokens.access_token);
    return tokens;
  }

  public async register(payload: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
  }): Promise<UserProfile> {
    return this.request<UserProfile>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  public async getCurrentUser(): Promise<UserProfile> {
    return this.request<UserProfile>('/api/v1/auth/me');
  }

  public logout(): void {
    this.setToken(null);
    this.setOrganizationId(null);
  }

  // Organizations & Memberships
  public async getMyMemberships(): Promise<OrganizationMembership[]> {
    return this.request<OrganizationMembership[]>('/api/v1/organizations/memberships');
  }

  // Courses & Offerings
  public async getCourses(): Promise<Course[]> {
    return this.request<Course[]>('/api/v1/courses');
  }

  public async getCourse(courseId: string): Promise<Course> {
    return this.request<Course>(`/api/v1/courses/${courseId}`);
  }

  public async getEnrollments(): Promise<CourseEnrollment[]> {
    return this.request<CourseEnrollment[]>('/api/v1/courses/enrollments');
  }

  public async enrollOffering(offeringId: string): Promise<CourseEnrollment> {
    return this.request<CourseEnrollment>(`/api/v1/courses/offerings/${offeringId}/enroll`, {
      method: 'POST',
    });
  }

  // Tutoring Sessions
  public async createTutoringSession(payload: {
    course_id: string;
    course_version_id: string;
    pedagogy_mode?: string;
  }): Promise<TutoringSession> {
    return this.request<TutoringSession>('/api/v1/tutoring/sessions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  public async getTutoringSession(sessionId: string): Promise<TutoringSession> {
    return this.request<TutoringSession>(`/api/v1/tutoring/sessions/${sessionId}`);
  }

  public async submitTutorTurn(
    sessionId: string,
    payload: TutorTurnRequest
  ): Promise<TutorTurnResponse> {
    return this.request<TutorTurnResponse>(`/api/v1/tutoring/sessions/${sessionId}/turn`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // Assessments
  public async getOfferingAssessments(offeringId: string): Promise<AssessmentSummary[]> {
    return this.request<AssessmentSummary[]>(`/api/v1/assessments/offerings/${offeringId}`);
  }

  public async getStudentAssessmentView(
    assessmentId: string
  ): Promise<{ assessment: AssessmentSummary; questions: AssessmentQuestion[] }> {
    return this.request<{ assessment: AssessmentSummary; questions: AssessmentQuestion[] }>(
      `/api/v1/assessments/${assessmentId}/student-view`
    );
  }

  public async startAssessmentAttempt(assessmentId: string): Promise<AssessmentAttempt> {
    return this.request<AssessmentAttempt>(`/api/v1/assessments/${assessmentId}/start`, {
      method: 'POST',
    });
  }

  public async autosaveAttempt(
    assessmentId: string,
    attemptId: string,
    draftAnswers: Record<string, unknown>
  ): Promise<{ status: string; updated_at: string }> {
    return this.request<{ status: string; updated_at: string }>(
      `/api/v1/assessments/${assessmentId}/attempts/${attemptId}/autosave`,
      {
        method: 'POST',
        body: JSON.stringify({ draft_answers: draftAnswers }),
      }
    );
  }

  public async submitAssessmentAttempt(
    assessmentId: string,
    attemptId: string,
    answers: Record<string, unknown>
  ): Promise<EvaluationResult> {
    return this.request<EvaluationResult>(
      `/api/v1/assessments/${assessmentId}/attempts/${attemptId}/submit`,
      {
        method: 'POST',
        body: JSON.stringify({ answers }),
      }
    );
  }

  public async getAttemptResult(
    assessmentId: string,
    attemptId: string
  ): Promise<EvaluationResult> {
    return this.request<EvaluationResult>(
      `/api/v1/assessments/${assessmentId}/attempts/${attemptId}/result`
    );
  }

  // Mastery & Analytics
  public async getConceptMasteries(courseId?: string): Promise<ConceptMastery[]> {
    const query = courseId ? `?course_id=${courseId}` : '';
    return this.request<ConceptMastery[]>(`/api/v1/tutoring/mastery${query}`);
  }

  public async getMisconceptions(): Promise<MisconceptionItem[]> {
    return this.request<MisconceptionItem[]>('/api/v1/tutoring/misconceptions');
  }

  public async getSpacedReviewSchedule(): Promise<SpacedReviewReminder[]> {
    return this.request<SpacedReviewReminder[]>('/api/v1/tutoring/spaced-reviews');
  }

  public async getRecentStudyActivity(): Promise<StudyActivity[]> {
    return this.request<StudyActivity[]>('/api/v1/tutoring/activity');
  }

  // AI BYOK Keys & Models
  public async getProviderConnections(): Promise<ProviderConnection[]> {
    return this.request<ProviderConnection[]>('/api/v1/ai/connections');
  }

  public async addProviderConnection(payload: {
    provider: string;
    label: string;
    api_key: string;
    scope?: string;
  }): Promise<ProviderConnection> {
    return this.request<ProviderConnection>('/api/v1/ai/connections', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  public async deleteProviderConnection(connectionId: string): Promise<void> {
    await this.request<void>(`/api/v1/ai/connections/${connectionId}`, {
      method: 'DELETE',
    });
  }

  public async getAvailableModels(): Promise<ModelInfo[]> {
    return this.request<ModelInfo[]>('/api/v1/ai/models');
  }

  // Privacy & Consent
  public async getPrivacySettings(): Promise<PrivacyConsentSettings> {
    return this.request<PrivacyConsentSettings>('/api/v1/events/training/consent');
  }

  public async updatePrivacySettings(
    settings: Partial<PrivacyConsentSettings>
  ): Promise<PrivacyConsentSettings> {
    return this.request<PrivacyConsentSettings>('/api/v1/events/training/consent', {
      method: 'POST',
      body: JSON.stringify(settings),
    });
  }

  // Teacher & Academic Administration
  public async getClassRoster(offeringId: string): Promise<RosterStudent[]> {
    return this.request<RosterStudent[]>(`/api/v1/teacher/offerings/${offeringId}/roster`);
  }

  public async enrollStudent(offeringId: string, studentId: string): Promise<{ id: string; status: string }> {
    return this.request<{ id: string; status: string }>(`/api/v1/teacher/offerings/${offeringId}/enroll`, {
      method: 'POST',
      body: JSON.stringify({ student_id: studentId }),
    });
  }

  public async unenrollStudent(offeringId: string, studentId: string): Promise<void> {
    await this.request<void>(`/api/v1/teacher/offerings/${offeringId}/enroll/${studentId}`, {
      method: 'DELETE',
    });
  }

  public async getClassAnalytics(offeringId: string): Promise<ClassAnalytics> {
    return this.request<ClassAnalytics>(`/api/v1/teacher/offerings/${offeringId}/analytics`);
  }

  public async getInterventionQueue(offeringId: string): Promise<InterventionItem[]> {
    return this.request<InterventionItem[]>(`/api/v1/teacher/offerings/${offeringId}/interventions`);
  }

  public async acknowledgeIntervention(
    interventionId: string,
    notes?: string,
    resolve = false
  ): Promise<InterventionItem> {
    return this.request<InterventionItem>(`/api/v1/teacher/interventions/${interventionId}/acknowledge`, {
      method: 'POST',
      body: JSON.stringify({ resolution_notes: notes, resolve }),
    });
  }

  public async getCopilotBriefing(offeringId: string): Promise<CopilotBriefing> {
    return this.request<CopilotBriefing>(`/api/v1/teacher/offerings/${offeringId}/copilot-briefing`);
  }

  public async getTeacherInstructions(courseId?: string): Promise<TeacherInstructionItem[]> {
    const query = courseId ? `?course_id=${courseId}` : '';
    return this.request<TeacherInstructionItem[]>(`/api/v1/teacher/instructions${query}`);
  }

  public async createTeacherInstruction(payload: {
    course_id: string;
    tier: string;
    directive_text: string;
    priority?: number;
  }): Promise<TeacherInstructionItem> {
    return this.request<TeacherInstructionItem>('/api/v1/teacher/instructions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  public async deactivateTeacherInstruction(instructionId: string): Promise<void> {
    await this.request<void>(`/api/v1/teacher/instructions/${instructionId}`, {
      method: 'DELETE',
    });
  }

  public async createAnnouncement(
    offeringId: string,
    payload: { title: string; content: string }
  ): Promise<ClassAnnouncementItem> {
    return this.request<ClassAnnouncementItem>('/api/v1/teacher/announcements', {
      method: 'POST',
      body: JSON.stringify({ offering_id: offeringId, ...payload }),
    });
  }

  public async getAnnouncements(offeringId: string): Promise<ClassAnnouncementItem[]> {
    return this.request<ClassAnnouncementItem[]>(`/api/v1/teacher/offerings/${offeringId}/announcements`);
  }
}

export const api = new ApiClient();
