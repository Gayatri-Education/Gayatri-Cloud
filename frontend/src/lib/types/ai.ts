export type ProviderType = 'openai' | 'anthropic' | 'gemini' | 'openrouter' | 'custom' | 'mock';

export interface ProviderConnection {
  id: string;
  provider: ProviderType;
  label: string;
  scope: 'PERSONAL' | 'ORGANIZATION';
  is_active: boolean;
  masked_key: string;
  created_at: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: ProviderType;
  context_window?: number;
  supports_streaming: boolean;
  tier: 'fast' | 'balanced' | 'reasoning';
}

export interface PrivacyConsentSettings {
  allow_interaction_logging: boolean;
  allow_training_inclusion: boolean;
  data_retention_days: number;
  last_updated: string;
}
