'use client';

import React, { useState } from 'react';
import { AuditLogEntry } from '../../lib/types/admin';
import { FileText, Filter, Calendar, Shield, Search } from 'lucide-react';

interface AuditSearchTableProps {
  logs: AuditLogEntry[];
  onSearch: (category?: string) => Promise<void>;
}

const CATEGORIES = [
  { id: '', label: 'All Categories' },
  { id: 'AUTH', label: 'Authentication & Security' },
  { id: 'ORG', label: 'Organization & Tenant' },
  { id: 'LEARNING', label: 'Learning & Tutoring' },
  { id: 'AI', label: 'AI Inference & Execution' },
];

export default function AuditSearchTable({ logs, onSearch }: AuditSearchTableProps) {
  const [selectedCategory, setSelectedCategory] = useState('');
  const [searching, setSearching] = useState(false);

  const handleFilter = async (cat: string) => {
    setSelectedCategory(cat);
    try {
      setSearching(true);
      await onSearch(cat || undefined);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="space-y-4" data-testid="audit-search-panel">
      {/* Header & Category Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-slate-700" />
          <h3 className="text-base font-bold text-slate-900">
            Immutable Audit Trail & Compliance Search
          </h3>
        </div>

        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-slate-400" />
          <div className="flex flex-wrap gap-1">
            {CATEGORIES.map((c) => (
              <button
                key={c.id}
                type="button"
                disabled={searching}
                onClick={() => handleFilter(c.id)}
                className={`rounded-lg px-2.5 py-1 text-xs font-medium transition ${
                  selectedCategory === c.id
                    ? 'bg-slate-900 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
                data-testid={`filter-cat-${c.id || 'all'}`}
              >
                {c.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm" data-testid="audit-logs-table">
          <thead className="bg-slate-50 text-xs font-semibold text-slate-600 uppercase tracking-wider">
            <tr>
              <th className="px-5 py-3">Event Type</th>
              <th className="px-5 py-3">Actor ID</th>
              <th className="px-5 py-3">Sensitivity</th>
              <th className="px-5 py-3">Occurred At</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {logs.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-5 py-8 text-center text-xs text-slate-400">
                  No immutable audit events found matching query.
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr key={log.event_id} className="hover:bg-slate-50/75 transition" data-testid={`audit-row-${log.event_id}`}>
                  <td className="px-5 py-4 font-mono font-semibold text-xs text-slate-900">
                    {log.event_type}
                  </td>
                  <td className="px-5 py-4 font-mono text-xs text-slate-600">
                    {log.actor_id || 'SYSTEM'}
                  </td>
                  <td className="px-5 py-4">
                    <span
                      className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ${
                        log.sensitivity === 'RESTRICTED'
                          ? 'bg-rose-100 text-rose-800'
                          : log.sensitivity === 'PROTECTED'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      <Shield className="h-3 w-3" />
                      {log.sensitivity}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-xs text-slate-500">
                    <div className="flex items-center gap-1.5">
                      <Calendar className="h-3.5 w-3.5 text-slate-400" />
                      {new Date(log.occurred_at).toLocaleString()}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
