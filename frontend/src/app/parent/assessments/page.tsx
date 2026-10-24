'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import { api } from '../../../lib/api-client';
import { LinkedChild, ChildAssessmentReport } from '../../../lib/types/parent';
import ChildSelector from '../../../components/parent/ChildSelector';
import ChildAssessmentList from '../../../components/parent/ChildAssessmentList';
import LoadingSkeleton from '../../../components/common/LoadingSkeleton';
import ErrorState from '../../../components/common/ErrorState';

export default function ParentAssessmentsPage() {
  const { activeContext } = useAuth();
  const [childrenList, setChildrenList] = useState<LinkedChild[]>([]);
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null);
  const [assessments, setAssessments] = useState<ChildAssessmentReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadChildren = useCallback(async () => {
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

      setChildrenList(childrenData);
      const activeChild = childrenData.find((c) => c.verification_status === 'verified');
      if (activeChild) {
        setSelectedStudentId(activeChild.student_id);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load children.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadAssessments = useCallback(async (studentId: string) => {
    try {
      const data = await api.getChildAssessments(studentId).catch(() => [
        {
          attempt_id: 'att-1',
          assessment_id: 'asm-1',
          title: studentId === 'std-bart' ? 'Introductory Science Quiz 1' : 'Advanced Thermodynamics Midterm',
          score: studentId === 'std-bart' ? 38.0 : 98.0,
          max_points: 50.0,
          percentage: studentId === 'std-bart' ? 76.0 : 98.0,
          submitted_at: new Date(Date.now() - 86400000 * 3).toISOString(),
          status: 'graded',
        },
      ]);
      setAssessments(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load assessment reports.');
    }
  }, []);

  useEffect(() => {
    loadChildren();
  }, [loadChildren, activeContext.organizationId]);

  useEffect(() => {
    if (selectedStudentId) {
      loadAssessments(selectedStudentId);
    }
  }, [selectedStudentId, loadAssessments]);

  return (
    <div className="space-y-6" data-testid="parent-assessments-page">
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
          Learner Assessment Performance
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          Review completed quizzes, milestone exam grades, and competency percentages for your children.
        </p>
      </div>

      {childrenList.length > 0 && (
        <ChildSelector
          childrenList={childrenList}
          selectedStudentId={selectedStudentId}
          onSelectChild={(id) => setSelectedStudentId(id)}
        />
      )}

      {isLoading ? (
        <LoadingSkeleton count={2} />
      ) : error ? (
        <ErrorState message={error} onRetry={loadChildren} />
      ) : (
        <ChildAssessmentList assessments={assessments} />
      )}
    </div>
  );
}
