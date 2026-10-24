'use client';

import React, { useState } from 'react';
import { OrganizationMember } from '../../lib/types/admin';
import { Users, Shield, UserX, AlertCircle, CheckCircle2 } from 'lucide-react';

interface MemberManagementTableProps {
  members: OrganizationMember[];
  onUpdateRole: (membershipId: string, newRole: string) => Promise<void>;
  onSuspendMember: (membershipId: string) => Promise<void>;
}

const AVAILABLE_ROLES = [
  'STUDENT',
  'TEACHER',
  'PARENT',
  'ORG_ADMIN',
  'ACADEMIC_ADMIN',
];

export default function MemberManagementTable({
  members,
  onUpdateRole,
  onSuspendMember,
}: MemberManagementTableProps) {
  const [selectedRole, setSelectedRole] = useState<{ [key: string]: string }>({});
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const handleRoleChange = async (membershipId: string, currentRoles: string[]) => {
    const newRole = selectedRole[membershipId];
    if (!newRole) return;

    // Client-side RQ-003 check for immediate user feedback
    if (
      (currentRoles.includes('STUDENT') && newRole === 'TEACHER') ||
      (currentRoles.includes('TEACHER') && newRole === 'STUDENT')
    ) {
      setMessage({
        text: 'Invariant Violation (RQ-003): Student and Teacher roles cannot coexist for an account in this organization.',
        type: 'error',
      });
      return;
    }

    try {
      setLoadingAction(`role-${membershipId}`);
      setMessage(null);
      await onUpdateRole(membershipId, newRole);
      setMessage({ text: 'Role successfully updated.', type: 'success' });
    } catch (err: unknown) {
      const errMessage = err instanceof Error ? err.message : 'Failed to update member role';
      setMessage({ text: errMessage, type: 'error' });
    } finally {
      setLoadingAction(null);
    }
  };

  const handleSuspend = async (membershipId: string) => {
    if (!confirm('Are you sure you want to suspend this member?')) return;
    try {
      setLoadingAction(`suspend-${membershipId}`);
      setMessage(null);
      await onSuspendMember(membershipId);
      setMessage({ text: 'Member suspended successfully.', type: 'success' });
    } catch (err: unknown) {
      const errMessage = err instanceof Error ? err.message : 'Failed to suspend member';
      setMessage({ text: errMessage, type: 'error' });
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="space-y-4" data-testid="member-management-panel">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-indigo-600" />
          <h3 className="text-base font-bold text-slate-900">
            Tenant Membership & Role Lifecycle
          </h3>
        </div>
        <span className="text-xs text-slate-400">{members.length} members</span>
      </div>

      {message && (
        <div
          className={`flex items-center gap-2 rounded-xl p-3 text-sm ${
            message.type === 'error'
              ? 'bg-rose-50 text-rose-700 border border-rose-200'
              : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
          }`}
          data-testid="member-action-message"
        >
          {message.type === 'error' ? (
            <AlertCircle className="h-4 w-4 shrink-0" />
          ) : (
            <CheckCircle2 className="h-4 w-4 shrink-0" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm" data-testid="members-table">
          <thead className="bg-slate-50 text-xs font-semibold text-slate-600 uppercase tracking-wider">
            <tr>
              <th className="px-5 py-3">Member</th>
              <th className="px-5 py-3">Current Roles</th>
              <th className="px-5 py-3">Status</th>
              <th className="px-5 py-3">Assign Role</th>
              <th className="px-5 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {members.map((m) => (
              <tr key={m.membership_id} className="hover:bg-slate-50/75 transition" data-testid={`member-row-${m.membership_id}`}>
                <td className="px-5 py-4">
                  <p className="font-semibold text-slate-900">{m.full_name}</p>
                  <p className="text-xs text-slate-500">{m.email}</p>
                </td>
                <td className="px-5 py-4">
                  <div className="flex flex-wrap gap-1">
                    {m.roles.map((r) => (
                      <span
                        key={r}
                        className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ${
                          r === 'ORG_ADMIN' || r === 'SUPER_ADMIN'
                            ? 'bg-purple-100 text-purple-800'
                            : r === 'TEACHER'
                            ? 'bg-sky-100 text-sky-800'
                            : r === 'PARENT'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        <Shield className="h-3 w-3" />
                        {r}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-5 py-4">
                  <span
                    className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                      m.status === 'active'
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-rose-100 text-rose-800'
                    }`}
                  >
                    {m.status}
                  </span>
                </td>
                <td className="px-5 py-4">
                  <div className="flex items-center gap-2">
                    <select
                      className="rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-700 focus:border-indigo-500 focus:outline-none"
                      value={selectedRole[m.membership_id] || ''}
                      onChange={(e) =>
                        setSelectedRole({ ...selectedRole, [m.membership_id]: e.target.value })
                      }
                      data-testid={`select-role-${m.membership_id}`}
                    >
                      <option value="">Select role...</option>
                      {AVAILABLE_ROLES.map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      disabled={!selectedRole[m.membership_id] || loadingAction === `role-${m.membership_id}`}
                      onClick={() => handleRoleChange(m.membership_id, m.roles)}
                      className="rounded-lg bg-indigo-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                      data-testid={`btn-apply-role-${m.membership_id}`}
                    >
                      Apply
                    </button>
                  </div>
                </td>
                <td className="px-5 py-4 text-right">
                  {m.status === 'active' && (
                    <button
                      type="button"
                      disabled={loadingAction === `suspend-${m.membership_id}`}
                      onClick={() => handleSuspend(m.membership_id)}
                      className="inline-flex items-center gap-1 rounded-lg border border-rose-300 px-2.5 py-1 text-xs font-medium text-rose-600 hover:bg-rose-50 disabled:opacity-50"
                      data-testid={`btn-suspend-${m.membership_id}`}
                    >
                      <UserX className="h-3.5 w-3.5" />
                      Suspend
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
