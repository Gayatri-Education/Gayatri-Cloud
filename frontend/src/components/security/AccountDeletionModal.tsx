'use client';

import React, { useState } from 'react';
import { api } from '../../lib/api-client';
import { AlertTriangle, X, ShieldAlert, Loader2 } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function AccountDeletionModal({ isOpen, onClose, onSuccess }: Props) {
  const [confirmationText, setConfirmationText] = useState('');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const isConfirmed = confirmationText.trim().toUpperCase() === 'DELETE MY ACCOUNT';

  const handleDelete = async () => {
    if (!isConfirmed) return;
    try {
      setLoading(true);
      setError(null);
      await api.requestAccountDeletion(reason, false);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to submit deletion request.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-xs"
      role="dialog"
      aria-modal="true"
      data-testid="account-deletion-modal"
    >
      <div className="w-full max-w-lg rounded-2xl border border-rose-200 bg-white p-6 shadow-xl space-y-5">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 text-rose-600">
            <AlertTriangle className="h-6 w-6 shrink-0" />
            <h2 className="text-lg font-bold text-slate-900">Request Account Deletion</h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Legal & Retention Disclosure */}
        <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-3.5 text-xs text-amber-950 space-y-2">
          <div className="font-bold flex items-center gap-1.5">
            <ShieldAlert className="h-4 w-4 text-amber-600 shrink-0" />
            <span>Right to be Forgotten & Statutory Legal Holds:</span>
          </div>
          <ul className="list-disc pl-5 space-y-1 text-amber-900">
            <li>You will be immediately logged out and your active sessions invalidated.</li>
            <li>You have a <strong>7-day grace period</strong> during which you can cancel this request.</li>
            <li>
              Per statutory regulations, tax receipts and accounting records are preserved with all
              personal details pseudonymized (RQ-027).
            </li>
          </ul>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-slate-700">
              Reason for leaving (Optional):
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={2}
              className="mt-1 w-full rounded-xl border border-slate-200 p-2.5 text-xs text-slate-800 focus:border-rose-500 focus:outline-hidden"
              placeholder="Completed courses, privacy preference, etc."
              data-testid="deletion-reason-input"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700">
              Type <strong className="text-rose-600 font-mono">DELETE MY ACCOUNT</strong> to confirm:
            </label>
            <input
              type="text"
              value={confirmationText}
              onChange={(e) => setConfirmationText(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 p-2.5 text-xs font-mono text-slate-900 focus:border-rose-500 focus:outline-hidden"
              placeholder="DELETE MY ACCOUNT"
              data-testid="deletion-confirm-input"
            />
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
            {error}
          </div>
        )}

        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 transition"
          >
            Keep Account
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={!isConfirmed || loading}
            className="flex items-center gap-1.5 rounded-xl bg-rose-600 px-4 py-2 text-xs font-bold text-white hover:bg-rose-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
            data-testid="confirm-deletion-btn"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            <span>Permanently Delete Account</span>
          </button>
        </div>
      </div>
    </div>
  );
}
