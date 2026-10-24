'use client';

import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api-client';
import { SecurityAuditEntry } from '../../lib/types/security';
import { History, Shield, RefreshCw } from 'lucide-react';

export default function SecurityAuditCard() {
  const [logs, setLogs] = useState<SecurityAuditEntry[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const data = await api.getSecurityAudit();
      setLogs(data);
    } catch {
      // offline or unauthenticated fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div
      className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4"
      data-testid="security-audit-card"
    >
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <History className="h-5 w-5 text-indigo-600" />
            <span>Security & Access Audit Trail</span>
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Immutable log of account security actions, session changes, and data export downloads.
          </p>
        </div>

        <button
          onClick={fetchLogs}
          disabled={loading}
          className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition"
          data-testid="refresh-audit-btn"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {logs.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-200 p-8 text-center text-xs text-slate-400">
          No security audit records logged yet.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-100 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                <th className="pb-2">Action</th>
                <th className="pb-2">IP Address</th>
                <th className="pb-2">Details</th>
                <th className="pb-2">Status</th>
                <th className="pb-2 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50/60 transition">
                  <td className="py-2.5 font-bold flex items-center gap-1.5">
                    <Shield className="h-3 w-3 text-indigo-500 shrink-0" />
                    <span>{log.action}</span>
                  </td>
                  <td className="py-2.5 font-mono text-[11px] text-slate-500">
                    {log.ip_address || '—'}
                  </td>
                  <td className="py-2.5 text-slate-600 max-w-xs truncate">{log.details || '—'}</td>
                  <td className="py-2.5">
                    <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700">
                      {log.status}
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-mono text-[11px] text-slate-400">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
