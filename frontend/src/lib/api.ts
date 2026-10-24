/**
 * API client configuration and health probe for Gayatri Cloud.
 */

export interface HealthResponse {
  status: string;
  app: string;
  version: string;
  timestamp: string;
}

export interface ReadinessResponse {
  status: string;
  checks: Record<string, string>;
  timestamp: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`, {
    headers: {
      'Accept': 'application/json',
    },
    cache: 'no-store',
  });
  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`);
  }
  return response.json();
}

export async function fetchReadiness(): Promise<ReadinessResponse> {
  const response = await fetch(`${API_BASE_URL}/ready`, {
    headers: {
      'Accept': 'application/json',
    },
    cache: 'no-store',
  });
  if (!response.ok) {
    throw new Error(`Readiness check failed with status: ${response.status}`);
  }
  return response.json();
}
