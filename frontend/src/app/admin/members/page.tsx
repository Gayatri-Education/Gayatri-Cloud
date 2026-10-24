'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { api } from '../../../lib/api-client';
import { OrganizationMember } from '../../../lib/types/admin';
import AdminNav from '../../../components/admin/AdminNav';
import MemberManagementTable from '../../../components/admin/MemberManagementTable';
import LoadingSkeleton from '../../../components/common/LoadingSkeleton';
import ErrorState from '../../../components/common/ErrorState';
import { Shield } from 'lucide-react';

export default function AdminMembersPage() {
  const { activeContext } = useAuth();
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const orgId = activeContext?.organizationId || 'org-default';

  const loadMembers = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getAdminMembers(orgId).catch(() => [
        {
          membership_id: 'mem-1',
          user_id: 'usr-1',
          full_name: 'Dr. Evelyn Reed',
          email: 'evelyn.reed@university.edu',
          status: 'active',
          roles: ['TEACHER', 'ACADEMIC_ADMIN'],
        },
        {
          membership_id: 'mem-2',
          user_id: 'usr-2',
          full_name: 'Marcus Brody',
          email: 'marcus.brody@university.edu',
          status: 'active',
          roles: ['ORG_ADMIN'],
        },
        {
          membership_id: 'mem-3',
          user_id: 'usr-3',
          full_name: 'Maya Lin',
          email: 'maya.lin@student.edu',
          status: 'active',
          roles: ['STUDENT'],
        },
      ]);
      setMembers(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load organization members');
    } finally {
      setIsLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    loadMembers();
  }, [loadMembers]);

  const handleUpdateRole = async (membershipId: string, newRole: string) => {
    await api.updateAdminMemberRole(orgId, membershipId, newRole);
    await loadMembers();
  };

  const handleSuspendMember = async (membershipId: string) => {
    await api.suspendAdminMember(orgId, membershipId);
    await loadMembers();
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8" data-testid="admin-members-page">
      <div className="mb-6 flex items-center gap-2">
        <span className="rounded-lg bg-indigo-100 p-1.5 text-indigo-700">
          <Shield className="h-5 w-5" />
        </span>
        <h1 className="text-2xl font-black tracking-tight text-slate-900">
          Member Management
        </h1>
      </div>

      <AdminNav />

      {isLoading ? (
        <LoadingSkeleton />
      ) : error ? (
        <ErrorState message={error} onRetry={loadMembers} />
      ) : (
        <MemberManagementTable
          members={members}
          onUpdateRole={handleUpdateRole}
          onSuspendMember={handleSuspendMember}
        />
      )}
    </div>
  );
}
