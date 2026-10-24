'use client';

import React from 'react';
import { SystemHealthReport } from '../../lib/types/observability';
import { Database, HardDrive, Inbox, Cpu, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

interface Props {
  health: SystemHealthReport | null;
}

export default function SystemHealthDashboard({ health }: Props) {
  if (!health) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-xs text-slate-400">
        Loading system readiness status...
      </div>
    );
  }

  const { components } = health;

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'healthy':
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700">
            <CheckCircle className="h-3 w-3 text-emerald-600" />
            Healthy
          </span>
        );
      case 'degraded':
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-bold text-amber-700">
            <AlertTriangle className="h-3 w-3 text-amber-600" />
            Degraded
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2 py-0.5 text-[10px] font-bold text-rose-700">
            <XCircle className="h-3 w-3 text-rose-600" />
            Unhealthy
          </span>
        );
    }
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="health-dashboard-cards">
      {/* 1. Database Connectivity */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-600">
            <Database className="h-4 w-4 text-sky-600" />
            <span>Database</span>
          </div>
          {getStatusBadge(components.database?.status)}
        </div>
        <div className="text-xl font-black text-slate-900">
          {components.database?.latency_ms !== undefined
            ? `${components.database.latency_ms} ms`
            : 'N/A'}
        </div>
        <p className="text-[11px] text-slate-400">Relational SQL connection probe latency</p>
      </div>

      {/* 2. Storage System */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-600">
            <HardDrive className="h-4 w-4 text-indigo-600" />
            <span>Object Storage</span>
          </div>
          {getStatusBadge(components.storage?.status)}
        </div>
        <div className="text-xl font-black text-slate-900">
          {components.storage?.writeable ? 'Writeable' : 'Degraded'}
        </div>
        <p className="text-[11px] text-slate-400">Curriculum documents and RAG volumes</p>
      </div>

      {/* 3. Event Outbox Queue Lag */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-600">
            <Inbox className="h-4 w-4 text-amber-600" />
            <span>Outbox Backlog</span>
          </div>
          {getStatusBadge(components.event_outbox?.status)}
        </div>
        <div className="text-xl font-black text-slate-900">
          {components.event_outbox?.unprocessed_events_lag ?? 0} events
        </div>
        <p className="text-[11px] text-slate-400">Unprocessed transactional outbox lag</p>
      </div>

      {/* 4. Circuit Breakers */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-600">
            <Cpu className="h-4 w-4 text-violet-600" />
            <span>AI Gateways</span>
          </div>
          {getStatusBadge(components.circuit_breakers?.status)}
        </div>
        <div className="text-xl font-black text-slate-900">
          {components.circuit_breakers?.tripped_count ?? 0} Tripped
        </div>
        <p className="text-[11px] text-slate-400">
          {components.circuit_breakers?.total_monitored ?? 0} provider circuits monitored
        </p>
      </div>
    </div>
  );
}
