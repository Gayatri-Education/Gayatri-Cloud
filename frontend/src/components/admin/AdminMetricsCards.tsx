'use client';

import React from 'react';
import { AdminMetrics } from '../../lib/types/admin';
import { Users, BookOpen, Layers, Activity, Cpu, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface AdminMetricsCardsProps {
  metrics: AdminMetrics;
}

export default function AdminMetricsCards({ metrics }: AdminMetricsCardsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5" data-testid="admin-metrics-cards">
      {/* Total Members */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Total Members
          </span>
          <div className="rounded-xl bg-sky-50 p-2.5 text-sky-600">
            <Users className="h-5 w-5" />
          </div>
        </div>
        <p className="mt-3 text-3xl font-extrabold text-slate-900" data-testid="metric-total-members">
          {metrics.total_members}
        </p>
        <p className="mt-1 text-xs text-slate-400">Enrolled accounts across tenant</p>
      </div>

      {/* Courses & Offerings */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Courses & Offerings
          </span>
          <div className="rounded-xl bg-indigo-50 p-2.5 text-indigo-600">
            <BookOpen className="h-5 w-5" />
          </div>
        </div>
        <p className="mt-3 text-3xl font-extrabold text-slate-900" data-testid="metric-total-courses">
          {metrics.total_courses}
          <span className="ml-2 text-sm font-medium text-slate-400">
            ({metrics.total_offerings} active cohorts)
          </span>
        </p>
        <p className="mt-1 text-xs text-slate-400">Active curriculum catalogs</p>
      </div>

      {/* Outbox Queue Lag */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Outbox Queue Lag
          </span>
          <div className={`rounded-xl p-2.5 ${metrics.outbox_lag_count > 0 ? 'bg-amber-50 text-amber-600' : 'bg-emerald-50 text-emerald-600'}`}>
            <Layers className="h-5 w-5" />
          </div>
        </div>
        <p className="mt-3 text-3xl font-extrabold text-slate-900" data-testid="metric-outbox-lag">
          {metrics.outbox_lag_count}
        </p>
        <p className="mt-1 text-xs text-slate-400">Pending transactional event outbox items</p>
      </div>

      {/* AI Tokens Consumed */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            AI Tokens Consumed
          </span>
          <div className="rounded-xl bg-purple-50 p-2.5 text-purple-600">
            <Cpu className="h-5 w-5" />
          </div>
        </div>
        <p className="mt-3 text-3xl font-extrabold text-slate-900" data-testid="metric-ai-tokens">
          {metrics.total_ai_tokens_consumed.toLocaleString()}
        </p>
        <p className="mt-1 text-xs text-slate-400">Prompt & completion usage telemetry</p>
      </div>

      {/* System Health */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:col-span-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Operational Telemetry Status
          </span>
          <div className="rounded-xl bg-slate-100 p-2.5 text-slate-600">
            <Activity className="h-5 w-5" />
          </div>
        </div>
        <div className="mt-3 flex items-center gap-3">
          {metrics.system_health === 'healthy' ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-sm font-semibold text-emerald-800" data-testid="system-health-badge">
              <CheckCircle2 className="h-4 w-4" /> Healthy
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-3 py-1 text-sm font-semibold text-amber-800" data-testid="system-health-badge">
              <AlertTriangle className="h-4 w-4" /> Degraded
            </span>
          )}
          <span className="text-xs text-slate-500">
            All database partitions, AI circuit-breakers, and outbox workers operating within nominal latency thresholds.
          </span>
        </div>
      </div>
    </div>
  );
}
