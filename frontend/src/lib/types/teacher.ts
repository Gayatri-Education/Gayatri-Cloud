export interface RosterStudent {
  enrollment_id: string;
  student_id: string;
  student_name: string;
  email: string;
  status: string;
  enrolled_at: string;
  average_mastery: number;
  active_misconceptions: number;
}

export interface HardestConcept {
  concept_id: string;
  average_score: number;
  attempts: number;
}

export interface MisconceptionCluster {
  concept_id: string;
  description: string;
  student_count: number;
}

export interface MasteryDistribution {
  novice: number;
  developing: number;
  competent: number;
  proficient: number;
  master: number;
}

export interface ClassAnalytics {
  total_students: number;
  average_mastery: number;
  mastery_distribution: MasteryDistribution;
  hardest_concepts: HardestConcept[];
  misconception_clusters: MisconceptionCluster[];
}

export interface InterventionItem {
  id: string;
  student_id: string;
  student_name: string;
  concept_id?: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  reason: string;
  status: 'PENDING' | 'ACKNOWLEDGED' | 'RESOLVED';
  created_at: string;
  resolution_notes?: string;
}

export interface CopilotBriefing {
  summary: string;
  evidence_sources: string[];
  confidence_score: number;
  uncertainty_note: string;
  bottleneck_concepts: string[];
  suggested_actions: string[];
  requires_teacher_confirmation: boolean;
}

export interface TeacherInstructionItem {
  id: string;
  course_id: string;
  tier: 'ORG' | 'COURSE' | 'CLASS' | 'STUDENT' | 'SESSION';
  directive_text: string;
  priority: number;
  is_active: boolean;
  created_at: string;
}

export interface ClassAnnouncementItem {
  id: string;
  offering_id: string;
  title: string;
  content: string;
  created_at: string;
}
