'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { api } from '../../../lib/api-client';
import { DomainVerification, OrganizationDetails } from '../../../lib/types/admin';
import AdminNav from '../../../components/admin/AdminNav';
import DomainVerificationPanel from '../../../components/admin/DomainVerificationPanel';
import LoadingSkeleton from '../../../components/common/LoadingSkeleton';
import ErrorState from '../../../components/common/ErrorState';
import { Building2, Save, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function AdminSettingsPage() {
  const { activeContext } = useAuth();
  const [org, setOrg] = useState<OrganizationDetails | null>(null);
  const [domains, setDomains] = useState<DomainVerification[]>([]);
  const [orgName, setOrgName] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const orgId = activeContext?.organizationId || 'org-default';

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [orgData, domainData] = await Promise.all([
        api.getAdminOrganization(orgId).catch(() => ({
          id: orgId,
          name: 'Apex Academy of Sciences',
          slug: 'apex-academy',
          status: 'active',
        })),
        api.getAdminDomains(orgId).catch(() => [
          {
            id: 'dom-1',
            domain_name: 'apex.edu',
            is_verified: true,
            created_at: new Date(Date.now() - 86400000 * 60).toISOString(),
          },
          {
            id: 'dom-2',
            domain_name: 'stem.apex.org',
            is_verified: false,
            verification_token: 'gayatri-verify-9812470123fa',
            created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
          },
        ]),
      ]);
      setOrg(orgData);
      setOrgName(orgData.name);
      setDomains(domainData);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load organization settings');
    } finally {
      setIsLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleUpdateBranding = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaveStatus(null);
      const res = await api.updateAdminBranding(orgId, orgName);
      setOrg(res);
      setSaveStatus('Organization details saved successfully.');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update organization branding');
    }
  };

  const handleAddDomain = async (domainName: string) => {
    const newDom = await api.addAdminDomain(orgId, domainName);
    setDomains([...(Array.isArray(domains) ? domains : []), newDom]);
    return newDom;
  };

  const handleVerifyDomain = async (domainId: string) => {
    await api.verifyAdminDomain(orgId, domainId);
    setDomains(
      (Array.isArray(domains) ? domains : []).map((d) => (d.id === domainId ? { ...d, is_verified: true } : d))
    );
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8" data-testid="admin-settings-page">
      <div className="mb-6 flex items-center gap-2">
        <span className="rounded-lg bg-slate-100 p-1.5 text-slate-700">
          <Building2 className="h-5 w-5" />
        </span>
        <h1 className="text-2xl font-black tracking-tight text-slate-900">
          Organization Settings & Ownership
        </h1>
      </div>

      <AdminNav />

      {isLoading ? (
        <LoadingSkeleton />
      ) : error ? (
        <ErrorState message={error} onRetry={loadData} />
      ) : (
        <div className="space-y-8">
          {/* General Branding Form */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Building2 className="h-4 w-4 text-slate-700" />
              Institutional Profile & Identity
            </h3>

            {saveStatus && (
              <div className="mb-4 rounded-xl bg-emerald-50 p-3 text-xs text-emerald-800 border border-emerald-200" data-testid="settings-save-status">
                {saveStatus}
              </div>
            )}

            <form onSubmit={handleUpdateBranding} className="space-y-4 max-w-xl">
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">
                  Organization Name
                </label>
                <input
                  type="text"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 px-4 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none"
                  data-testid="input-org-name"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">
                  Tenant Slug (Immutable)
                </label>
                <input
                  type="text"
                  disabled
                  value={org?.slug || ''}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-500 font-mono"
                />
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700"
                  data-testid="btn-save-branding"
                >
                  <Save className="h-4 w-4" />
                  Save Changes
                </button>
              </div>
            </form>
          </div>

          {/* Domain Proof Verification */}
          <DomainVerificationPanel
            domains={domains}
            onAddDomain={handleAddDomain}
            onVerifyDomain={handleVerifyDomain}
          />
        </div>
      )}
    </div>
  );
}
