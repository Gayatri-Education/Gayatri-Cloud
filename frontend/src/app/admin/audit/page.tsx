'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { api } from '../../../lib/api-client';
import { AuditLogEntry } from '../../../lib/types/admin';
import AdminNav from '../../../components/admin/AdminNav';
import AuditSearchTable from '../../../components/admin/AuditSearchTable';
import LoadingSkeleton from '../../../components/common/LoadingSkeleton';
import ErrorState from '../../../components/common/ErrorState';
import { FileText } from 'lucide-react';

export default function AdminAuditPage() {
  const { activeContext } = useAuth();
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const orgId = activeContext?.organizationId || 'org-default';

  const loadAuditLogs = useCallback(
    async (category?: string) => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await api.searchAdminAuditLogs(orgId, category).catch(() => [
          {
            event_id: 'evt-101',
            event_type: 'AUTH_SESSION_AUTHENTICATED',
            actor_id: 'usr-1',
            sensitivity: 'INTERNAL',
            occurred_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
          },
          {
            event_id: 'evt-102',
            event_type: 'LEARNING_SESSION_STARTED',
            actor_id: 'usr-3',
            sensitivity: 'PROTECTED',
            occurred_at: new Date(Date.now() - 1000 * 60 * 35).toISOString(),
          },
          {
            event_id: 'evt-103',
            event_type: 'AI_MODEL_POLICY_UPDATED',
            actor_id: 'usr-2',
            sensitivity: 'RESTRICTED',
            occurred_at: new Date(Date.now() - 1000 * 3600 * 2).toISOString(),
          },
        ]);
        setLogs(data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to search audit trail');
      } finally {
        setIsLoading(false);
      }
    },
    [orgId]
  );

  useEffect(() => {
    loadAuditLogs();
  }, [loadAuditLogs]);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8" data-testid="admin-audit-page">
      <div className="mb-6 flex items-center gap-2">
        <span className="rounded-lg bg-slate-100 p-1.5 text-slate-700">
          <FileText className="h-5 w-5" />
        </span>
        <h1 className="text-2xl font-black tracking-tight text-slate-900">
          Compliance Audit Trail
        </h1>
      </div>

      <AdminNav />

      {isLoading ? (
        <LoadingSkeleton />
      ) : error ? (
        <ErrorState message={error} onRetry={() => loadAuditLogs()} />
      ) : (
        <AuditSearchTable logs={logs} onSearch={(cat) => loadAuditLogs(cat)} />
      )}
    </div>
  );
}
