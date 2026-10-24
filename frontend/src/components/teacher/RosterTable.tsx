'use client';

import React, { useState } from 'react';
import { RosterStudent } from '../../lib/types/teacher';
import EmptyState from '../common/EmptyState';
import { Users, UserPlus, Trash2, AlertCircle, Search } from 'lucide-react';

interface RosterTableProps {
  students: RosterStudent[];
  offeringId: string;
  onEnroll?: (studentId: string) => Promise<void>;
  onUnenroll?: (studentId: string) => Promise<void>;
}

export default function RosterTable({
  students,
  offeringId,
  onEnroll,
  onUnenroll,
}: RosterTableProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [newStudentId, setNewStudentId] = useState('');
  const [isEnrolling, setIsEnrolling] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const safeStudents = Array.isArray(students) ? students : [];
  const filteredStudents = safeStudents.filter(
    (s) =>
      (s.student_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (s.email || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleEnroll = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newStudentId.trim() || !onEnroll) return;
    try {
      setIsEnrolling(true);
      setActionError(null);
      await onEnroll(newStudentId.trim());
      setNewStudentId('');
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Failed to enroll student');
    } finally {
      setIsEnrolling(false);
    }
  };

  const handleUnenroll = async (studentId: string, studentName: string) => {
    if (!confirm(`Are you sure you want to unenroll ${studentName}?`)) return;
    if (!onUnenroll) return;
    try {
      setActionError(null);
      await onUnenroll(studentId);
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Failed to unenroll student');
    }
  };

  return (
    <div className="space-y-4" data-testid="roster-table-container">
      {/* Top action bar: Search & Quick Enroll */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search students..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            data-testid="roster-search-input"
          />
        </div>

        {onEnroll && (
          <form onSubmit={handleEnroll} className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Student User ID..."
              value={newStudentId}
              onChange={(e) => setNewStudentId(e.target.value)}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
              data-testid="enroll-student-input"
            />
            <button
              type="submit"
              disabled={isEnrolling || !newStudentId.trim()}
              className="inline-flex items-center gap-1.5 rounded-lg bg-sky-600 px-3.5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-sky-500 disabled:opacity-50 transition"
              data-testid="enroll-student-btn"
            >
              <UserPlus className="h-4 w-4" />
              <span>Enroll</span>
            </button>
          </form>
        )}
      </div>

      {actionError && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 border border-red-200 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Table */}
      {filteredStudents.length === 0 ? (
        <EmptyState
          icon={<Users className="h-8 w-8 text-slate-400" />}
          title="No students found"
          description={
            searchTerm
              ? 'No enrolled learners matched your search query.'
              : 'There are currently no students enrolled in this offering.'
          }
        />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm" data-testid="roster-table">
            <thead className="bg-slate-50 text-xs font-semibold text-slate-600 uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3">Learner</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Average Mastery</th>
                <th className="px-4 py-3">Misconceptions</th>
                <th className="px-4 py-3">Enrolled At</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredStudents.map((student) => {
                const masteryPct = Math.round(student.average_mastery * 100);
                return (
                  <tr key={student.student_id} className="hover:bg-slate-50/75 transition" data-testid={`student-row-${student.student_id}`}>
                    <td className="px-4 py-3">
                      <div className="font-medium text-slate-900">{student.student_name}</div>
                      <div className="text-xs text-slate-400">{student.email}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 border border-emerald-200">
                        {student.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-2 rounded-full bg-slate-100 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              masteryPct >= 75
                                ? 'bg-emerald-500'
                                : masteryPct >= 50
                                ? 'bg-amber-500'
                                : 'bg-rose-500'
                            }`}
                            style={{ width: `${masteryPct}%` }}
                          />
                        </div>
                        <span className="text-xs font-semibold text-slate-700">
                          {masteryPct}%
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {student.active_misconceptions > 0 ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2 py-0.5 text-xs font-semibold text-rose-700 border border-rose-200">
                          <AlertCircle className="h-3 w-3" />
                          {student.active_misconceptions} Active
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400">None detected</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      {new Date(student.enrolled_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {onUnenroll && (
                        <button
                          onClick={() => handleUnenroll(student.student_id, student.student_name)}
                          className="text-slate-400 hover:text-rose-600 transition p-1"
                          title="Unenroll student"
                          data-testid={`unenroll-btn-${student.student_id}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
