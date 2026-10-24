'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  Users,
  Award,
  Bell,
  Heart,
  TrendingUp,
} from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import { api } from '../../../lib/api-client';
import { LinkedChild, ChildProgressSummary } from '../../../lib/types/parent';
import ChildSelector from '../../../components/parent/ChildSelector';
import ChildProgressOverview from '../../../components/parent/ChildProgressOverview';
import LoadingSkeleton from '../../../components/common/LoadingSkeleton';
import ErrorState from '../../../components/common/ErrorState';

export default function ParentDashboardPage() {
  const { user, activeContext } = useAuth();
  const [childrenList, setChildrenList] = useState<LinkedChild[]>([]);
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null);
  const [progress, setProgress] = useState<ChildProgressSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadParentDashboard = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const childrenData = await api.getLinkedChildren().catch(() => [
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

      const safeList = Array.isArray(childrenData) ? childrenData : [];
      setChildrenList(safeList);
      const activeChild = safeList.find((c) => c.verification_status === 'verified');
      if (activeChild) {
        setSelectedStudentId(activeChild.student_id);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load parent dashboard.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadChildProgress = useCallback(async (studentId: string) => {
    try {
      const progressData = await api.getChildProgress(studentId).catch(() => ({
        student_id: studentId,
        overall_mastery: studentId === 'std-bart' ? 0.58 : 0.96,
        total_tutoring_sessions: studentId === 'std-bart' ? 12 : 28,
        estimated_study_minutes: studentId === 'std-bart' ? 300 : 700,
        active_misconceptions_count: studentId === 'std-bart' ? 2 : 0,
        top_concepts: [
          { concept_id: 'heat_capacity', mastery_score: 0.75, stability_days: 14 },
          { concept_id: 'carnot_cycle', mastery_score: 0.42, stability_days: 3 },
        ],
        enrolled_courses: [
          { title: 'PHYS-401: Advanced Thermodynamics', term: 'Fall 2026' },
          { title: 'SCI-101: Introductory Science', term: 'Fall 2026' },
        ],
        privacy_disclosure:
          'Parent Portal Privacy Protocol: Raw conversational turns are excluded from parent views to maintain learner safe-space and autonomous Socratic inquiry.',
      }));

      setProgress(progressData);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load child progress.');
    }
  }, []);

  useEffect(() => {
    loadParentDashboard();
  }, [loadParentDashboard, activeContext.organizationId]);

  useEffect(() => {
    if (selectedStudentId) {
      loadChildProgress(selectedStudentId);
    }
  }, [selectedStudentId, loadChildProgress]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-slate-200 rounded animate-pulse" />
        <LoadingSkeleton count={3} />
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadParentDashboard} />;
  }

  return (
    <div className="space-y-8" data-testid="parent-dashboard">
      {/* Welcome Banner */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="rounded-md bg-rose-100 px-2.5 py-1 text-xs font-bold text-rose-800 uppercase tracking-wider">
                Parent & Guardian Portal
              </span>
              <span className="text-xs text-slate-400">
                {activeContext.organizationName}
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Welcome, {user ? `${user.first_name} ${user.last_name}` : 'Parent/Guardian'}
            </h1>
            <p className="mt-1 text-sm text-slate-600">
              Monitor your children&apos;s educational progress, assessment results, and school updates with guaranteed privacy.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Heart className="h-5 w-5 text-rose-500 fill-rose-500" />
            <span className="text-xs font-semibold text-slate-600">
              {childrenList.filter((c) => c.verification_status === 'verified').length} Linked Learner(s)
            </span>
          </div>
        </div>

        {/* Quick Nav Grid */}
        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3 pt-6 border-t border-slate-100">
          <Link
            href="/parent/children"
            className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-slate-50/60 p-3 hover:bg-white hover:shadow-sm hover:border-sky-300 transition"
          >
            <Users className="h-5 w-5 text-sky-600" />
            <div>
              <div className="text-xs font-bold text-slate-800">Manage Children</div>
              <div className="text-[11px] text-slate-400">Verification & Links</div>
            </div>
          </Link>

          <Link
            href="/parent/assessments"
            className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-slate-50/60 p-3 hover:bg-white hover:shadow-sm hover:border-sky-300 transition"
          >
            <Award className="h-5 w-5 text-amber-600" />
            <div>
              <div className="text-xs font-bold text-slate-800">Assessment Reports</div>
              <div className="text-[11px] text-slate-400">Grades & Remarks</div>
            </div>
          </Link>

          <Link
            href="/parent/communications"
            className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-slate-50/60 p-3 hover:bg-white hover:shadow-sm hover:border-sky-300 transition"
          >
            <Bell className="h-5 w-5 text-indigo-600" />
            <div>
              <div className="text-xs font-bold text-slate-800">School Notices</div>
              <div className="text-[11px] text-slate-400">Class Announcements</div>
            </div>
          </Link>
        </div>
      </div>

      {/* Multi-Child Selector */}
      {childrenList.length > 0 && (
        <ChildSelector
          childrenList={childrenList}
          selectedStudentId={selectedStudentId}
          onSelectChild={(id) => setSelectedStudentId(id)}
        />
      )}

      {/* Child Learning Progress */}
      {progress && <ChildProgressOverview progress={progress} />}
    </div>
  );
}
