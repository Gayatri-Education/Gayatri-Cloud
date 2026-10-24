export type MasteryStatus = 'novice' | 'developing' | 'competent' | 'proficient' | 'master';

export interface ConceptMastery {
  concept_id: string;
  concept_name: string;
  course_id: string;
  mastery_score: number; // 0.0 - 1.0
  stability: number; // Half-life stability in days
  status: MasteryStatus;
  last_practiced: string;
  next_review_due: string;
  evidence_count: number;
}

export interface MisconceptionItem {
  id: string;
  concept_id: string;
  concept_name: string;
  misconception_code: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
  detected_at: string;
  remediated: boolean;
  remediation_advice: string;
}

export interface StudyActivity {
  id: string;
  activity_type: 'tutoring' | 'assessment' | 'practice';
  title: string;
  duration_minutes: number;
  timestamp: string;
  score_or_delta?: string;
}

export interface SpacedReviewReminder {
  concept_id: string;
  concept_name: string;
  course_title: string;
  due_date: string;
  is_overdue: boolean;
  priority: 'normal' | 'high';
}
