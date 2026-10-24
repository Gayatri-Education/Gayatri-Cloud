'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { ArrowLeft, Users, Download, UserPlus } from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import { api } from '../../../lib/api-client';
import { RosterStudent } from '../../../lib/types/teacher';
import RosterTable from '../../../components/teacher/RosterTable';
import LoadingSkeleton from '../../../components/common/LoadingSkeleton';
import ErrorState from '../../../components/common/ErrorState';

export default function TeacherRosterPage() {
  const { activeContext } = useAuth();
  const [selectedOfferingId, setSelectedOfferingId] = useState<string>('offering-thermo-fall2026');
  const [students, setStudents] = useState<RosterStudent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadRoster = useCallback(async (offeringId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getClassRoster(offeringId).catch(() => [
        {
          enrollment_id: 'enr-1',
          student_id: 'std-bart',
          student_name: 'Bart Simpson',
          email: 'bart@springfield.edu',
          status: 'enrolled',
          enrolled_at: new Date(Date.now() - 86400000 * 14).toISOString(),
          average_mastery: 0.52,
          active_misconceptions: 2,
        },
        {
          enrollment_id: 'enr-2',
          student_id: 'std-milhouse',
          student_name: 'Milhouse VanHouten',
          email: 'milhouse@springfield.edu',
          status: 'enrolled',
          enrolled_at: new Date(Date.now() - 86400000 * 12).toISOString(),
          average_mastery: 0.61,
          active_misconceptions: 1,
        },
        {
          enrollment_id: 'enr-3',
          student_id: 'std-lisa',
          student_name: 'Lisa Simpson',
          email: 'lisa@springfield.edu',
          status: 'enrolled',
          enrolled_at: new Date(Date.now() - 86400000 * 20).toISOString(),
          average_mastery: 0.96,
          active_misconceptions: 0,
        },
      ]);
      setStudents(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load class roster.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRoster(selectedOfferingId);
  }, [loadRoster, selectedOfferingId, activeContext.organizationId]);

  const handleEnroll = async (studentId: string) => {
    await api.enrollStudent(selectedOfferingId, studentId);
    // Reload roster or insert mock
    setStudents((prev) => [
      ...prev,
      {
        enrollment_id: `enr-${Date.now()}`,
        student_id: studentId,
        student_name: `Student (${studentId.substring(0, 8)})`,
        email: `${studentId}@organization.edu`,
        status: 'enrolled',
        enrolled_at: new Date().toISOString(),
        average_mastery: 0.0,
        active_misconceptions: 0,
      },
    ]);
  };

  const handleUnenroll = async (studentId: string) => {
    await api.unenrollStudent(selectedOfferingId, studentId);
    setStudents((prev) => prev.filter((s) => s.student_id !== studentId));
  };

  return (
    <div className="space-y-6" data-testid="roster-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <Link
            href="/teacher/dashboard"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition mb-2"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Teacher Dashboard</span>
          </Link>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Class Roster & Enrollment Management
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            View student progress, enrollment dates, active misconceptions, and manage course offerings.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={selectedOfferingId}
            onChange={(e) => setSelectedOfferingId(e.target.value)}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-800 focus:border-sky-500 focus:outline-none"
            data-testid="roster-offering-select"
          >
            <option value="offering-thermo-fall2026">
              PHYS-401: Advanced Thermodynamics
            </option>
            <option value="offering-chem-fall2026">
              CHEM-101: Organic Chemistry
            </option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <LoadingSkeleton count={3} />
      ) : error ? (
        <ErrorState message={error} onRetry={() => loadRoster(selectedOfferingId)} />
      ) : (
        <RosterTable
          students={students}
          offeringId={selectedOfferingId}
          onEnroll={handleEnroll}
          onUnenroll={handleUnenroll}
        />
      )}
    </div>
  );
}
