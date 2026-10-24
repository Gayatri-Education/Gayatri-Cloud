'use client';

import React, { useState } from 'react';
import { api } from '../../lib/api-client';
import { BackupSnapshot, RestoreReport } from '../../lib/types/observability';
import { Database, ShieldCheck, PlayCircle, Loader2 } from 'lucide-react';

export default function BackupRecoveryPanel() {
  const [snapshot, setSnapshot] = useState<BackupSnapshot | null>(null);
  const [restoreReport, setRestoreReport] = useState<RestoreReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreateSnapshot = async () => {
    try {
      setLoading(true);
      setError(null);
      setRestoreReport(null);
      const data = await api.createBackupSnapshot('admin_manual_drill');
      setSnapshot(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to generate snapshot.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyRestore = async () => {
    if (!snapshot) return;
    try {
      setVerifying(true);
      setError(null);
      const report = await api.verifyBackupRestore(snapshot);
      setRestoreReport(report);
    } catch (err: any) {
      setError(err?.message || 'Failed to simulate restore.');
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div
      className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-5"
      data-testid="backup-recovery-panel"
    >
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Database className="h-5 w-5 text-indigo-600" />
            <span>Database Backup Snapshot & Restore Verification</span>
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Simulate point-in-time snapshot creation, compute SHA-256 manifests, and test automated disaster recovery drills.
          </p>
        </div>

        <button
          onClick={handleCreateSnapshot}
          disabled={loading}
          className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-700 disabled:opacity-50 transition"
          data-testid="create-snapshot-btn"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Snapshotting...</span>
            </>
          ) : (
            <>
              <Database className="h-4 w-4" />
              <span>Create Snapshot</span>
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
          {error}
        </div>
      )}

      {snapshot && (
        <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-4 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-slate-900">{snapshot.snapshot_id}</span>
              <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
                {snapshot.encryption}
              </span>
            </div>
            <button
              onClick={handleVerifyRestore}
              disabled={verifying}
              className="flex items-center gap-1.5 rounded-lg border border-emerald-300 bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-800 hover:bg-emerald-100 disabled:opacity-50 transition"
              data-testid="verify-restore-btn"
            >
              {verifying ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin text-emerald-700" />
              ) : (
                <PlayCircle className="h-3.5 w-3.5 text-emerald-700" />
              )}
              <span>Run Restore Simulation Drill</span>
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs text-slate-600 font-mono text-[11px]">
            {Object.entries(snapshot?.inventory || {}).map(([table, count]) => (
              <div key={table} className="rounded bg-white p-2 border border-slate-200">
                <span className="text-slate-400 block text-[9px] uppercase">{table}</span>
                <span className="font-bold text-slate-800">{count} rows</span>
              </div>
            ))}
          </div>

          <div className="font-mono text-[10px] text-slate-500 truncate pt-1">
            SHA-256 Manifest: {snapshot.checksum_sha256}
          </div>
        </div>
      )}

      {restoreReport && (
        <div className="rounded-xl border border-emerald-300 bg-emerald-50/80 p-4 space-y-2 text-xs text-emerald-950">
          <div className="flex items-center gap-2 font-bold text-emerald-900">
            <ShieldCheck className="h-5 w-5 text-emerald-600" />
            <span>Disaster Recovery Simulation Drill: PASSED</span>
          </div>
          <p className="text-emerald-800">{restoreReport.message}</p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-[11px] font-mono text-emerald-800">
            <div>Target: {restoreReport.target_environment}</div>
            <div>Tables Restored: {restoreReport.restored_tables_count}</div>
            <div>Records Restored: {restoreReport.restored_records_total}</div>
            <div>Readiness Score: {restoreReport.recovery_readiness_score}%</div>
          </div>
        </div>
      )}
    </div>
  );
}
