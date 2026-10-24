'use client';

import React, { useState, useEffect } from 'react';
import { api } from '../../../lib/api-client';
import { DeletionRequestStatus } from '../../../lib/types/security';
import DataExportCard from '../../../components/security/DataExportCard';
import SecurityAuditCard from '../../../components/security/SecurityAuditCard';
import AccountDeletionModal from '../../../components/security/AccountDeletionModal';
import { Shield, Lock, AlertTriangle, CheckCircle, RotateCcw } from 'lucide-react';

export default function PrivacySettingsPage() {
  const [deletionStatus, setDeletionStatus] = useState<DeletionRequestStatus | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [cancelling, setCancelling] = useState(false);

  const fetchStatus = async () => {
    try {
      const data = await api.getDeletionStatus();
      setDeletionStatus(data);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleCancelDeletion = async () => {
    try {
      setCancelling(true);
      await api.cancelDeletionRequest();
      await fetchStatus();
    } catch {
      // ignore
    } finally {
      setCancelling(false);
    }
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto" data-testid="privacy-settings-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
          <Shield className="h-6 w-6 text-sky-600" />
          <span>Privacy & Security Controls</span>
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Manage your personal data rights, download data archives, and inspect security access logs.
        </p>
      </div>

      {/* Training Governance Disclaimer (DEC-011) */}
      <div className="rounded-2xl border border-sky-100 bg-sky-50/60 p-5 text-xs text-sky-950 space-y-2">
        <div className="flex items-center gap-2 font-bold text-sky-900">
          <Lock className="h-4 w-4 text-sky-600" />
          <span>Strict AI Training Governance (DEC-011)</span>
        </div>
        <p className="text-sky-800 leading-relaxed">
          Gayatri Cloud strictly enforces <strong>deny-by-default</strong> model training policies. Your
          tutoring interactions and assessment submissions are <strong>never</strong> used for general
          AI training without separate institutional authorization, explicit human dataset sign-off,
          and automated PII redaction.
        </p>
      </div>

      {/* Data Export (GDPR Art. 20) */}
      <DataExportCard />

      {/* Security Audit Trail */}
      <SecurityAuditCard />

      {/* Account Deletion & Right to be Forgotten */}
      <div
        className="rounded-2xl border border-rose-200 bg-rose-50/40 p-6 space-y-4"
        data-testid="account-deletion-section"
      >
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-rose-900 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-rose-600" />
              <span>Right to be Forgotten & Account Deletion</span>
            </h3>
            <p className="text-xs text-rose-700 mt-1 max-w-xl">
              Permanently delete your personal profile, credentials, and learning history. A 7-day grace
              period applies, during which you can cancel your request. Statutory accounting records are
              pseudonymized.
            </p>
          </div>

          {deletionStatus?.has_active_request ? (
            <div className="flex items-center gap-2">
              <span className="rounded-lg bg-amber-100 px-3 py-1.5 text-xs font-bold text-amber-900">
                Deletion Scheduled
              </span>
              <button
                onClick={handleCancelDeletion}
                disabled={cancelling}
                className="flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3 py-1.5 text-xs font-bold text-slate-700 hover:bg-slate-50 transition"
                data-testid="cancel-deletion-btn"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Cancel Deletion</span>
              </button>
            </div>
          ) : (
            <button
              onClick={() => setIsModalOpen(true)}
              className="rounded-xl border border-rose-300 bg-rose-600 px-4 py-2 text-xs font-bold text-white hover:bg-rose-700 transition"
              data-testid="open-deletion-modal-btn"
            >
              Request Deletion
            </button>
          )}
        </div>

        {deletionStatus?.has_active_request && (
          <div className="rounded-xl border border-amber-300 bg-amber-50 p-3 text-xs text-amber-900 flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-amber-600 shrink-0" />
            <span>
              Your account deletion is pending. Grace period expires on{' '}
              <strong>{new Date(deletionStatus.grace_period_expires_at || '').toLocaleDateString()}</strong>.
            </span>
          </div>
        )}
      </div>

      {/* Modal */}
      <AccountDeletionModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={fetchStatus}
      />
    </div>
  );
}
