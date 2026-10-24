export interface LinkedChild {
  relationship_id: string;
  student_id: string;
  student_name: string;
  email: string;
  verification_status: 'pending' | 'verified' | 'rejected' | 'revoked';
  is_active: boolean;
  average_mastery: number;
  active_courses_count: number;
  linked_at: string;
}

export interface ConceptSummary {
  concept_id: string;
  mastery_score: number;
  stability_days: number;
}

export interface EnrolledCourseSummary {
  title: string;
  term: string;
}

export interface ChildProgressSummary {
  student_id: string;
  overall_mastery: number;
  total_tutoring_sessions: number;
  estimated_study_minutes: number;
  active_misconceptions_count: number;
  top_concepts: ConceptSummary[];
  enrolled_courses: EnrolledCourseSummary[];
  privacy_disclosure: string;
}

export interface ChildAssessmentReport {
  attempt_id: string;
  assessment_id: string;
  title: string;
  score: number;
  max_points: number;
  percentage: number;
  submitted_at: string;
  status: string;
}

export interface ChildCommunicationItem {
  id: string;
  offering_id: string;
  title: string;
  content: string;
  teacher_name: string;
  posted_at: string;
}
