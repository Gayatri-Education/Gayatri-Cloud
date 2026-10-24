/**
 * Security, Privacy, and Data Subject Rights TypeScript contracts.
 */

export interface UserProfileExport {
  id: string;
  email: string;
  full_name: string;
  created_at: string;
  is_verified: boolean;
}

export interface UserDataExport {
  export_version: string;
  exported_at: string;
  checksum_sha256: string;
  user_profile: UserProfileExport;
  memberships: Array<{
    organization_id: string;
    membership_id: string;
    status: string;
    role: string;
    joined_at: string;
  }>;
  enrollments: Array<{
    enrollment_id: string;
    offering_id: string;
    status: string;
    enrolled_at: string;
  }>;
  assessment_attempts: Array<{
    attempt_id: string;
    assessment_id: string;
    status: string;
    score: number | null;
    submitted_at: string | null;
  }>;
  tutoring_sessions: Array<{
    session_id: string;
    course_id: string;
    status: string;
    created_at: string;
  }>;
}

export interface DeletionRequestStatus {
  has_active_request: boolean;
  request_id?: string;
  status: 'none' | 'pending' | 'completed' | 'cancelled';
  message?: string;
  grace_period_expires_at?: string;
  completed_at?: string | null;
  legal_hold_retained_records?: string | null;
}

export interface SecurityAuditEntry {
  id: string;
  action: string;
  ip_address: string | null;
  status: string;
  details: string | null;
  timestamp: string;
}
