'use client';

import React, { useState, useEffect } from 'react';
import { api } from '../../../lib/api-client';
import { SystemHealthReport } from '../../../lib/types/observability';
import AdminNav from '../../../components/admin/AdminNav';
import SystemHealthDashboard from '../../../components/observability/SystemHealthDashboard';
import CircuitBreakerControls from '../../../components/observability/CircuitBreakerControls';
import BackupRecoveryPanel from '../../../components/observability/BackupRecoveryPanel';
import { Activity, RefreshCw } from 'lucide-react';

export default function AdminObservabilityPage() {
  const [health, setHealth] = useState<SystemHealthReport | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      const data = await api.getDeepHealth();
      setHealth(data);
    } catch {
      // offline or error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const breakers = health?.components.circuit_breakers?.breakers || [];

  return (
    <div className="space-y-6" data-testid="admin-observability-page">
      <AdminNav />

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Activity className="h-6 w-6 text-sky-600" />
            <span>Platform Observability & Reliability</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time component readiness, AI circuit breakers, outbox queue telemetry, and disaster recovery.
          </p>
        </div>

        <button
          onClick={fetchHealth}
          disabled={loading}
          className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50 disabled:opacity-50 transition"
          data-testid="refresh-health-btn"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      {/* Health Cards */}
      <SystemHealthDashboard health={health} />

      {/* Circuit Breakers & Kill-Switches */}
      <CircuitBreakerControls breakers={breakers} onRefresh={fetchHealth} />

      {/* Backup and Disaster Recovery Simulation */}
      <BackupRecoveryPanel />
    </div>
  );
}
