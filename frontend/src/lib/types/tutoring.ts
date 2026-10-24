export type PedagogyMode = 'socratic' | 'explain_first' | 'practice_first' | 'custom';

export interface Citation {
  chunk_id: string;
  source_title: string;
  snippet: string;
  score?: number;
}

export interface TutorMessage {
  id: string;
  sender: 'student' | 'tutor' | 'system';
  content: string;
  timestamp: string;
  mode?: PedagogyMode;
  citations?: Citation[];
  model?: string;
  provider?: string;
  status?: 'sending' | 'streaming' | 'complete' | 'error';
  feedback?: 'helpful' | 'unhelpful' | null;
}

export interface TutoringSession {
  id: string;
  student_id: string;
  course_id: string;
  course_title?: string;
  course_version_id: string;
  pedagogy_mode: PedagogyMode;
  current_concept?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface TutorTurnRequest {
  message: string;
  pedagogy_mode?: PedagogyMode;
  current_concept?: string;
}

export interface TutorTurnResponse {
  response_text: string;
  pedagogy_mode: PedagogyMode;
  citations: Citation[];
  concept_identified?: string;
  mastery_delta?: number;
  model_used: string;
  provider_used: string;
  turn_id: string;
}
