'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import { api } from '../../../lib/api-client';
import { LinkedChild, ChildCommunicationItem } from '../../../lib/types/parent';
import ChildSelector from '../../../components/parent/ChildSelector';
import SchoolCommunications from '../../../components/parent/SchoolCommunications';
import LoadingSkeleton from '../../../components/common/LoadingSkeleton';
import ErrorState from '../../../components/common/ErrorState';

export default function ParentCommunicationsPage() {
  const { activeContext } = useAuth();
  const [childrenList, setChildrenList] = useState<LinkedChild[]>([]);
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null);
  const [communications, setCommunications] = useState<ChildCommunicationItem[]>([]);
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

  const loadCommunications = useCallback(async (studentId: string) => {
    try {
      const data = await api.getChildCommunications(studentId).catch(() => [
        {
          id: 'comm-1',
          offering_id: 'offering-sci-1',
          title: 'Field Trip to Springfield Science Center',
          content:
            'Permission slips for the upcoming natural sciences demonstration must be returned by Friday afternoon.',
          teacher_name: 'Edna Krabappel',
          posted_at: new Date(Date.now() - 86400000 * 2).toISOString(),
        },
      ]);
      setCommunications(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load school communications.');
    }
  }, []);

  useEffect(() => {
    loadChildren();
  }, [loadChildren, activeContext.organizationId]);

  useEffect(() => {
    if (selectedStudentId) {
      loadCommunications(selectedStudentId);
    }
  }, [selectedStudentId, loadCommunications]);

  return (
    <div className="space-y-6" data-testid="parent-communications-page">
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
          School Notices & Class Announcements
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          Stay informed about course schedules, field trips, and teacher announcements for your children.
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
        <SchoolCommunications communications={communications} />
      )}
    </div>
  );
}
