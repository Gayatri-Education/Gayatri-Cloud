'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Award, Edit3, CheckCircle, ShieldCheck, AlertCircle } from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import EmptyState from '../../../components/common/EmptyState';

interface SubmissionItem {
  id: string;
  student_name: string;
  student_id: string;
  assessment_title: string;
  score: number;
  max_score: number;
  submitted_at: string;
  is_overridden: boolean;
  override_notes?: string;
}

export default function TeacherAssessmentsPage() {
  const { activeContext } = useAuth();
  const [submissions, setSubmissions] = useState<SubmissionItem[]>([
    {
      id: 'sub-1',
      student_name: 'Bart Simpson',
      student_id: 'std-bart',
      assessment_title: 'Thermodynamics Milestone 1',
      score: 65,
      max_score: 100,
      submitted_at: new Date(Date.now() - 86400000 * 2).toISOString(),
      is_overridden: false,
    },
    {
      id: 'sub-2',
      student_name: 'Milhouse VanHouten',
      student_id: 'std-milhouse',
      assessment_title: 'Thermodynamics Milestone 1',
      score: 72,
      max_score: 100,
      submitted_at: new Date(Date.now() - 86400000 * 3).toISOString(),
      is_overridden: false,
    },
    {
      id: 'sub-3',
      student_name: 'Lisa Simpson',
      student_id: 'std-lisa',
      assessment_title: 'Thermodynamics Milestone 1',
      score: 98,
      max_score: 100,
      submitted_at: new Date(Date.now() - 86400000 * 4).toISOString(),
      is_overridden: false,
    },
  ]);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [overrideScore, setOverrideScore] = useState<number>(0);
  const [overrideReason, setOverrideReason] = useState<string>('');
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  const startOverride = (sub: SubmissionItem) => {
    setEditingId(sub.id);
    setOverrideScore(sub.score);
    setOverrideReason(sub.override_notes || '');
    setSaveSuccess(null);
  };

  const handleSaveOverride = (id: string) => {
    if (!overrideReason.trim()) {
      alert('Please provide a pedagogical rationale for this manual score adjustment.');
      return;
    }

    setSubmissions((prev) =>
      prev.map((sub) =>
        sub.id === id
          ? {
              ...sub,
              score: overrideScore,
              is_overridden: true,
              override_notes: overrideReason.trim(),
            }
          : sub
      )
    );
    setEditingId(null);
    setSaveSuccess('Grade override recorded with audit justification.');
  };

  return (
    <div className="space-y-6" data-testid="teacher-assessments-page">
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
            Assessment Oversight & Grade Adjustments
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Audit automated AI evaluation results and apply teacher overrides with recorded pedagogical justifications.
          </p>
        </div>
      </div>

      {saveSuccess && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800 flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-emerald-600 shrink-0" />
          <span>{saveSuccess}</span>
        </div>
      )}

      {/* Submissions Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm" data-testid="assessments-table">
          <thead className="bg-slate-50 text-xs font-semibold text-slate-600 uppercase tracking-wider">
            <tr>
              <th className="px-4 py-3">Learner</th>
              <th className="px-4 py-3">Assessment</th>
              <th className="px-4 py-3">Submitted</th>
              <th className="px-4 py-3">Score</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {submissions.map((sub) => {
              const isEditing = editingId === sub.id;
              const pct = Math.round((sub.score / sub.max_score) * 100);

              return (
                <tr key={sub.id} className="hover:bg-slate-50/75 transition" data-testid={`submission-row-${sub.id}`}>
                  <td className="px-4 py-3">
                    <div className="font-medium text-slate-900">{sub.student_name}</div>
                    <div className="text-xs text-slate-400">{sub.student_id}</div>
                  </td>
                  <td className="px-4 py-3 text-slate-800">{sub.assessment_title}</td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    {new Date(sub.submitted_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    {isEditing ? (
                      <div className="flex items-center gap-1.5">
                        <input
                          type="number"
                          min="0"
                          max={sub.max_score}
                          value={overrideScore}
                          onChange={(e) => setOverrideScore(parseInt(e.target.value, 10) || 0)}
                          className="w-20 rounded-md border border-slate-300 px-2 py-1 text-sm focus:border-sky-500 focus:outline-none"
                          data-testid="override-score-input"
                        />
                        <span className="text-xs text-slate-500">/ {sub.max_score}</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900">{sub.score}</span>
                        <span className="text-xs text-slate-400">/ {sub.max_score}</span>
                        <span
                          className={`text-xs font-semibold ${
                            pct >= 75
                              ? 'text-emerald-600'
                              : pct >= 50
                              ? 'text-amber-600'
                              : 'text-rose-600'
                          }`}
                        >
                          ({pct}%)
                        </span>
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {sub.is_overridden ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-purple-50 px-2 py-0.5 text-xs font-semibold text-purple-700 border border-purple-200">
                        <ShieldCheck className="h-3 w-3" />
                        Teacher Override
                      </span>
                    ) : (
                      <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
                        AI Graded
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {isEditing ? (
                      <div className="flex flex-col items-end gap-2">
                        <input
                          type="text"
                          placeholder="Teacher audit rationale (required)..."
                          value={overrideReason}
                          onChange={(e) => setOverrideReason(e.target.value)}
                          className="w-64 rounded-md border border-slate-300 px-2 py-1 text-xs focus:border-sky-500 focus:outline-none"
                          data-testid="override-reason-input"
                        />
                        <div className="flex gap-1.5">
                          <button
                            onClick={() => handleSaveOverride(sub.id)}
                            className="rounded-md bg-sky-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-sky-500"
                            data-testid="save-override-btn"
                          >
                            Save Override
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="rounded-md px-2 py-1 text-xs text-slate-400 hover:text-slate-600"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button
                        onClick={() => startOverride(sub)}
                        className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 transition shadow-2xs"
                        data-testid={`override-btn-${sub.id}`}
                      >
                        <Edit3 className="h-3.5 w-3.5 text-slate-500" />
                        <span>Adjust Grade</span>
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
