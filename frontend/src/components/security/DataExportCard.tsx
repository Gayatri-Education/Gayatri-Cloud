'use client';

import React, { useState } from 'react';
import { api } from '../../lib/api-client';
import { UserDataExport } from '../../lib/types/security';
import { DownloadCloud, ShieldCheck, FileJson, Loader2 } from 'lucide-react';

export default function DataExportCard() {
  const [loading, setLoading] = useState(false);
  const [lastExport, setLastExport] = useState<UserDataExport | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getDataExport();
      setLastExport(data);

      // Trigger client file download
      const jsonStr = JSON.stringify(data, null, 2);
      const blob = new Blob([jsonStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `gayatri_user_export_${data.user_profile.id.slice(0, 8)}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err?.message || 'Failed to generate data export.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4"
      data-testid="data-export-card"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <DownloadCloud className="h-5 w-5 text-sky-600" />
            <span>Download Personal Data (GDPR Art. 20)</span>
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Export a complete, machine-readable JSON archive containing your profile, enrollments, assessment results, and tutoring interactions.
          </p>
        </div>

        <button
          onClick={handleExport}
          disabled={loading}
          className="flex items-center gap-2 rounded-xl bg-sky-600 px-4 py-2 text-xs font-bold text-white hover:bg-sky-700 disabled:opacity-50 transition"
          data-testid="generate-export-btn"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Packaging...</span>
            </>
          ) : (
            <>
              <FileJson className="h-4 w-4" />
              <span>Export My Data</span>
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
          {error}
        </div>
      )}

      {lastExport && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-4 space-y-2 text-xs text-emerald-900">
          <div className="flex items-center gap-2 font-bold">
            <ShieldCheck className="h-4 w-4 text-emerald-600" />
            <span>Export Archive Successfully Generated</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 font-mono text-[11px] text-emerald-800">
            <div>Memberships: {lastExport.memberships.length}</div>
            <div>Enrollments: {lastExport.enrollments.length}</div>
            <div>Assessments: {lastExport.assessment_attempts.length}</div>
            <div>Sessions: {lastExport.tutoring_sessions.length}</div>
          </div>
          <div className="pt-2 text-[10px] text-emerald-700 truncate font-mono">
            SHA-256 Checksum: {lastExport.checksum_sha256}
          </div>
        </div>
      )}
    </div>
  );
}
