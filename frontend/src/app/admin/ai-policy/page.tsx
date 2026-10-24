'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { api } from '../../../lib/api-client';
import { AdminAiPolicy } from '../../../lib/types/admin';
import AdminNav from '../../../components/admin/AdminNav';
import AiPolicyManager from '../../../components/admin/AiPolicyManager';
import LoadingSkeleton from '../../../components/common/LoadingSkeleton';
import ErrorState from '../../../components/common/ErrorState';
import { Cpu } from 'lucide-react';

export default function AdminAiPolicyPage() {
  const { activeContext } = useAuth();
  const [policy, setPolicy] = useState<AdminAiPolicy | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const orgId = activeContext?.organizationId || 'org-default';

  const loadPolicy = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getAdminAiPolicy(orgId).catch(() => ({
        organization_id: orgId,
        routing_strategy: 'quality_first',
        allowed_models: ['gpt-4o', 'claude-3-5-sonnet-20241022', 'gemini-1.5-pro'],
        configured_providers: [
          {
            id: 'conn-1',
            provider: 'openai',
            scope: 'organization',
            key_masked: 'sk-...4921',
          },
          {
            id: 'conn-2',
            provider: 'anthropic',
            scope: 'organization',
            key_masked: 'sk-...8820',
          },
        ],
      }));
      setPolicy(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load AI policy');
    } finally {
      setIsLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    loadPolicy();
  }, [loadPolicy]);

  const handleSavePolicy = async (allowedModels: string[], routingStrategy: string) => {
    await api.updateAdminAiPolicy(orgId, allowedModels, routingStrategy);
    await loadPolicy();
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8" data-testid="admin-ai-policy-page">
      <div className="mb-6 flex items-center gap-2">
        <span className="rounded-lg bg-purple-100 p-1.5 text-purple-700">
          <Cpu className="h-5 w-5" />
        </span>
        <h1 className="text-2xl font-black tracking-tight text-slate-900">
          AI Routing & Model Policy
        </h1>
      </div>

      <AdminNav />

      {isLoading ? (
        <LoadingSkeleton />
      ) : error ? (
        <ErrorState message={error} onRetry={loadPolicy} />
      ) : policy ? (
        <AiPolicyManager policy={policy} onSavePolicy={handleSavePolicy} />
      ) : null}
    </div>
  );
}
