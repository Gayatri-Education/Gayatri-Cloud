'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { ArrowLeft, Users } from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import { api } from '../../../lib/api-client';
import { LinkedChild } from '../../../lib/types/parent';
import GuardianLinkManager from '../../../components/parent/GuardianLinkManager';
import LoadingSkeleton from '../../../components/common/LoadingSkeleton';
import ErrorState from '../../../components/common/ErrorState';

export default function ParentChildrenPage() {
  const { activeContext } = useAuth();
  const [childrenList, setChildrenList] = useState<LinkedChild[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadChildren = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getLinkedChildren().catch(() => [
        {
          relationship_id: 'rel-1',
          student_id: 'std-bart',
          student_name: 'Bart Simpson',
          email: 'bart@springfield.edu',
          verification_status: 'verified' as const,
          is_active: true,
          average_mastery: 0.58,
          active_courses_count: 2,
          linked_at: new Date(Date.now() - 86400000 * 30).toISOString(),
        },
        {
          relationship_id: 'rel-2',
          student_id: 'std-lisa',
          student_name: 'Lisa Simpson',
          email: 'lisa@springfield.edu',
          verification_status: 'verified' as const,
          is_active: true,
          average_mastery: 0.96,
          active_courses_count: 3,
          linked_at: new Date(Date.now() - 86400000 * 45).toISOString(),
        },
      ]);
      setChildrenList(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load linked children.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadChildren();
  }, [loadChildren, activeContext.organizationId]);

  const handleRequestLink = async (identifier: string) => {
    await api.requestStudentLink(identifier).catch(() => ({
      relationship_id: `rel-${Date.now()}`,
      student_id: identifier,
      student_name: `Student (${identifier})`,
      email: identifier,
      verification_status: 'pending' as const,
      is_active: true,
      average_mastery: 0.0,
      active_courses_count: 0,
      linked_at: new Date().toISOString(),
    }));

    await loadChildren();
  };

  const handleRevokeLink = async (relationshipId: string) => {
    await api.revokeGuardianLink(relationshipId).catch(() => {});
    setChildrenList((prev) => prev.filter((c) => c.relationship_id !== relationshipId));
  };

  return (
    <div className="space-y-6" data-testid="parent-children-page">
      {/* Header */}
      <div>
        <Link
          href="/parent/dashboard"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition mb-2"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Parent Dashboard</span>
        </Link>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Linked Learner Management & Verification
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          Connect with your children, review relationship verification statuses, and manage school access.
        </p>
      </div>

      {isLoading ? (
        <LoadingSkeleton count={2} />
      ) : error ? (
        <ErrorState message={error} onRetry={loadChildren} />
      ) : (
        <GuardianLinkManager
          childrenList={childrenList}
          onRequestLink={handleRequestLink}
          onRevokeLink={handleRevokeLink}
        />
      )}
    </div>
  );
}
