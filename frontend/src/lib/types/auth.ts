export interface UserProfile {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface OrganizationMembership {
  id: string;
  organization_id: string;
  organization_name: string;
  organization_slug: string;
  role: 'STUDENT' | 'TEACHER' | 'PARENT' | 'COURSE_ADMIN' | 'ORGANIZATION_ADMIN';
  is_active: boolean;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ActiveContext {
  organizationId: string | null;
  organizationName: string;
  role: string;
  isPersonal: boolean;
}
