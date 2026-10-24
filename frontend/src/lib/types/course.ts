export interface CourseVersion {
  id: string;
  course_id: string;
  version_number: number;
  title: string;
  description?: string;
  is_published: boolean;
  published_at?: string;
  metadata?: Record<string, unknown>;
}

export interface Course {
  id: string;
  slug: string;
  title: string;
  description: string;
  subject: string;
  organization_id: string | null;
  active_version?: CourseVersion;
  versions?: CourseVersion[];
  created_at: string;
}

export interface CourseOffering {
  id: string;
  course_id: string;
  course_version_id: string;
  organization_id: string;
  name: string;
  term?: string;
  is_active: boolean;
  created_at: string;
}

export interface CourseEnrollment {
  id: string;
  offering_id: string;
  offering_name: string;
  course_id: string;
  course_title: string;
  version_number: number;
  student_id: string;
  enrolled_at: string;
  progress_percentage: number;
  status: 'active' | 'completed' | 'paused';
}
