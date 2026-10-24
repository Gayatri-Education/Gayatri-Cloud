'use client';

import React, { useState } from 'react';
import { LinkedChild } from '../../lib/types/parent';
import { Users, UserPlus, CheckCircle, Clock, Trash2, AlertCircle } from 'lucide-react';
import EmptyState from '../common/EmptyState';

interface GuardianLinkManagerProps {
  childrenList: LinkedChild[];
  onRequestLink?: (studentIdentifier: string) => Promise<void>;
  onRevokeLink?: (relationshipId: string) => Promise<void>;
}

export default function GuardianLinkManager({
  childrenList,
  onRequestLink,
  onRevokeLink,
}: GuardianLinkManagerProps) {
  const [identifier, setIdentifier] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<{ text: string; isError: boolean } | null>(null);

  const handleRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim() || !onRequestLink) return;

    try {
      setIsSubmitting(true);
      setMessage(null);
      await onRequestLink(identifier.trim());
      setIdentifier('');
      setMessage({
        text: 'Link request submitted! The school administrator or student confirmation is pending.',
        isError: false,
      });
    } catch (err: unknown) {
      setMessage({
        text: err instanceof Error ? err.message : 'Failed to submit link request',
        isError: true,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRevoke = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to revoke guardian access to ${name}? Access will be terminated immediately.`)) {
      return;
    }
    if (!onRevokeLink) return;

    try {
      await onRevokeLink(id);
      setMessage({
        text: `Guardian relationship with ${name} revoked.`,
        isError: false,
      });
    } catch (err: unknown) {
      setMessage({
        text: err instanceof Error ? err.message : 'Failed to revoke link',
        isError: true,
      });
    }
  };

  return (
    <div className="space-y-6" data-testid="guardian-link-manager">
      {/* Link Request Form */}
      {onRequestLink && (
        <form
          onSubmit={handleRequest}
          className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4"
          data-testid="link-request-form"
        >
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <UserPlus className="h-5 w-5 text-sky-600" />
            <h3 className="text-base font-bold text-slate-900">
              Link a Student Account
            </h3>
          </div>

          <p className="text-xs text-slate-600">
            Enter your child&apos;s registered school email or student account ID to request guardian access.
          </p>

          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              placeholder="Student email (e.g., bart@springfield.edu) or User ID..."
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              className="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
              data-testid="student-identifier-input"
            />
            <button
              type="submit"
              disabled={isSubmitting || !identifier.trim()}
              className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-sky-500 disabled:opacity-50 transition"
              data-testid="submit-link-request-btn"
            >
              <UserPlus className="h-4 w-4" />
              <span>Submit Request</span>
            </button>
          </div>

          {message && (
            <div
              className={`rounded-xl p-3 text-xs flex items-center gap-2 border ${
                message.isError
                  ? 'bg-rose-50 text-rose-800 border-rose-200'
                  : 'bg-emerald-50 text-emerald-800 border-emerald-200'
              }`}
            >
              {message.isError ? (
                <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
              ) : (
                <CheckCircle className="h-4 w-4 shrink-0 text-emerald-600" />
              )}
              <span>{message.text}</span>
            </div>
          )}
        </form>
      )}

      {/* Linked Children List */}
      <div className="space-y-3">
        <h4 className="text-sm font-bold text-slate-900">
          Guardian Relationships on Record ({childrenList.length})
        </h4>

        {childrenList.length === 0 ? (
          <EmptyState
            icon={<Users className="h-8 w-8 text-slate-400" />}
            title="No Linked Learners"
            description="You do not have any linked student accounts yet. Submit a request above to connect with your child."
          />
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2" data-testid="linked-children-grid">
            {childrenList.map((child) => (
              <div
                key={child.relationship_id}
                className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm hover:border-slate-300 transition flex items-center justify-between"
                data-testid={`child-card-${child.student_id}`}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-slate-900">
                      {child.student_name}
                    </span>
                    {child.verification_status === 'verified' ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700 border border-emerald-200">
                        <CheckCircle className="h-3 w-3" />
                        Verified
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-bold text-amber-700 border border-amber-200">
                        <Clock className="h-3 w-3" />
                        Pending Approval
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-400">{child.email}</div>
                  <div className="text-[11px] text-slate-500">
                    Linked on {new Date(child.linked_at).toLocaleDateString()}
                  </div>
                </div>

                {onRevokeLink && (
                  <button
                    onClick={() => handleRevoke(child.relationship_id, child.student_name)}
                    className="p-2 text-slate-400 hover:text-rose-600 transition"
                    title="Revoke guardian access"
                    data-testid={`revoke-btn-${child.relationship_id}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
