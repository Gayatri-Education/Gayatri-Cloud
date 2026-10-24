export type QuestionType =
  | 'mcq'
  | 'boolean'
  | 'numerical'
  | 'subjective'
  | 'coding'
  | 'adaptive';

export interface AssessmentQuestion {
  id: string;
  type: QuestionType;
  prompt: string;
  options?: string[]; // For MCQ
  unit?: string; // For Numerical
  tolerance_percent?: number; // For Numerical
  language?: string; // For Coding
  starter_code?: string; // For Coding
  points: number;
}

export interface AssessmentSummary {
  id: string;
  offering_id: string;
  course_id: string;
  title: string;
  description: string;
  type: string;
  time_limit_minutes?: number | null;
  total_points: number;
  question_count: number;
  deadline?: string | null;
  is_published: boolean;
}

export interface AssessmentAttempt {
  id: string;
  assessment_id: string;
  student_id: string;
  started_at: string;
  submitted_at?: string | null;
  expires_at?: string | null;
  time_limit_seconds?: number | null;
  status: 'in_progress' | 'submitted' | 'graded' | 'expired';
  draft_answers?: Record<string, string | number | boolean>;
  score?: number | null;
  total_points: number;
}

export interface CriterionFeedback {
  criterion: string;
  score: number;
  max_score: number;
  feedback: string;
}

export interface EvaluationResult {
  attempt_id: string;
  total_score: number;
  max_points: number;
  percentage: number;
  passed: boolean;
  question_results: Record<
    string,
    {
      earned_points: number;
      max_points: number;
      feedback: string;
      detected_misconceptions?: string[];
      criteria?: CriterionFeedback[];
    }
  >;
  misconceptions_detected: string[];
  submitted_at: string;
}
