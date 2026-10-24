export interface AdminMetrics {
  organization_id?: string;
  total_members: number;
  total_courses: number;
  total_offerings: number;
  outbox_lag_count: number;
  total_ai_tokens_consumed: number;
  system_health: 'healthy' | 'degraded';
}

export interface OrganizationMember {
  membership_id: string;
  user_id: string;
  full_name: string;
  email: string;
  status: string;
  roles: string[];
}

export interface DomainVerification {
  id: string;
  domain_name: string;
  is_verified: boolean;
  verification_token?: string;
  created_at?: string;
}

export interface ConfiguredProvider {
  id: string;
  provider: string;
  scope: string;
  key_masked: string;
}

export interface AdminAiPolicy {
  organization_id: string;
  routing_strategy: string;
  allowed_models: string[];
  configured_providers?: ConfiguredProvider[];
}

export interface AuditLogEntry {
  event_id: string;
  event_type: string;
  actor_id: string;
  sensitivity: string;
  occurred_at: string;
}

export interface OrganizationDetails {
  id: string;
  name: string;
  slug: string;
  status: string;
  branding_config?: string;
}
