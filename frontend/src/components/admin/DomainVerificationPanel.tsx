'use client';

import React, { useState } from 'react';
import { DomainVerification } from '../../lib/types/admin';
import { Globe, Plus, CheckCircle2, Clock, ShieldCheck, Copy, Check } from 'lucide-react';

interface DomainVerificationPanelProps {
  domains: DomainVerification[];
  onAddDomain: (domainName: string) => Promise<DomainVerification>;
  onVerifyDomain: (domainId: string) => Promise<void>;
}

export default function DomainVerificationPanel({
  domains,
  onAddDomain,
  onVerifyDomain,
}: DomainVerificationPanelProps) {
  const [newDomain, setNewDomain] = useState('');
  const [adding, setAdding] = useState(false);
  const [verifyingId, setVerifyingId] = useState<string | null>(null);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDomain.trim()) return;
    try {
      setAdding(true);
      setErrorMsg(null);
      await onAddDomain(newDomain.trim());
      setNewDomain('');
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to register domain');
    } finally {
      setAdding(false);
    }
  };

  const handleVerify = async (domainId: string) => {
    try {
      setVerifyingId(domainId);
      setErrorMsg(null);
      await onVerifyDomain(domainId);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to complete verification');
    } finally {
      setVerifyingId(null);
    }
  };

  const copyToClipboard = (token: string) => {
    navigator.clipboard?.writeText(token);
    setCopiedToken(token);
    setTimeout(() => setCopiedToken(null), 2000);
  };

  return (
    <div className="space-y-6" data-testid="domain-verification-panel">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <Globe className="h-5 w-5 text-sky-600" />
          <h3 className="text-base font-bold text-slate-900">
            Institutional Domain Ownership & DNS Proofs
          </h3>
        </div>
        <p className="mt-1 text-xs text-slate-500">
          Verify institutional domain ownership via DNS TXT records. Domain verification does not automatically grant admin privileges or bypass course entitlement boundaries.
        </p>
      </div>

      {errorMsg && (
        <div className="rounded-xl bg-rose-50 p-3 text-xs text-rose-700 border border-rose-200" data-testid="domain-error">
          {errorMsg}
        </div>
      )}

      {/* Add Domain Form */}
      <form onSubmit={handleAdd} className="flex gap-3" data-testid="add-domain-form">
        <input
          type="text"
          placeholder="e.g. stanford.edu, oxford.ac.uk"
          value={newDomain}
          onChange={(e) => setNewDomain(e.target.value)}
          className="flex-1 rounded-xl border border-slate-300 px-4 py-2 text-sm text-slate-800 placeholder-slate-400 focus:border-sky-500 focus:outline-none"
          data-testid="input-new-domain"
        />
        <button
          type="submit"
          disabled={adding || !newDomain.trim()}
          className="inline-flex items-center gap-2 rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-sky-700 disabled:opacity-50"
          data-testid="btn-add-domain"
        >
          <Plus className="h-4 w-4" />
          {adding ? 'Registering...' : 'Add Domain'}
        </button>
      </form>

      {/* Domains List */}
      <div className="space-y-3" data-testid="domains-list">
        {domains.map((dom) => (
          <div
            key={dom.id}
            className="flex flex-col sm:flex-row sm:items-center sm:justify-between rounded-2xl border border-slate-200 bg-white p-4 shadow-sm gap-3"
            data-testid={`domain-card-${dom.id}`}
          >
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-900 text-sm">{dom.domain_name}</span>
                {dom.is_verified ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800" data-testid="status-verified">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Verified
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-800" data-testid="status-pending">
                    <Clock className="h-3.5 w-3.5" />
                    Pending Proof
                  </span>
                )}
              </div>

              {!dom.is_verified && dom.verification_token && (
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-xs text-slate-500">DNS TXT Record:</span>
                  <code className="rounded bg-slate-100 px-2 py-0.5 font-mono text-xs text-slate-700">
                    {dom.verification_token}
                  </code>
                  <button
                    type="button"
                    onClick={() => copyToClipboard(dom.verification_token!)}
                    className="text-slate-400 hover:text-slate-600"
                    title="Copy token"
                    data-testid={`btn-copy-token-${dom.id}`}
                  >
                    {copiedToken === dom.verification_token ? (
                      <Check className="h-3.5 w-3.5 text-emerald-600" />
                    ) : (
                      <Copy className="h-3.5 w-3.5" />
                    )}
                  </button>
                </div>
              )}
            </div>

            {!dom.is_verified && (
              <button
                type="button"
                disabled={verifyingId === dom.id}
                onClick={() => handleVerify(dom.id)}
                className="inline-flex items-center gap-1.5 self-start sm:self-auto rounded-xl bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-emerald-700 disabled:opacity-50"
                data-testid={`btn-verify-domain-${dom.id}`}
              >
                <ShieldCheck className="h-3.5 w-3.5" />
                {verifyingId === dom.id ? 'Checking...' : 'Verify Proof'}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
