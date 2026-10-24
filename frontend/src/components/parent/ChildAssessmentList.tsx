'use client';

import React from 'react';
import { ChildAssessmentReport } from '../../lib/types/parent';
import EmptyState from '../common/EmptyState';
import { Award, CheckCircle2, Clock, Calendar } from 'lucide-react';

interface ChildAssessmentListProps {
  assessments: ChildAssessmentReport[];
}

export default function ChildAssessmentList({ assessments }: ChildAssessmentListProps) {
  return (
    <div className="space-y-4" data-testid="child-assessments-list">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Award className="h-5 w-5 text-sky-600" />
          <h3 className="text-base font-bold text-slate-900">
            Completed Assessments & Evaluations
          </h3>
        </div>
        <span className="text-xs text-slate-400">
          {assessments.length} {assessments.length === 1 ? 'assessment' : 'assessments'} on record
        </span>
      </div>

      {assessments.length === 0 ? (
        <EmptyState
          icon={<Award className="h-8 w-8 text-slate-400" />}
          title="No Assessment Records"
          description="Your linked learner has not submitted any assessments yet."
        />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm" data-testid="assessments-table">
            <thead className="bg-slate-50 text-xs font-semibold text-slate-600 uppercase tracking-wider">
              <tr>
                <th className="px-5 py-3">Assessment</th>
                <th className="px-5 py-3">Date Submitted</th>
                <th className="px-5 py-3">Score</th>
                <th className="px-5 py-3">Percentage</th>
                <th className="px-5 py-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {assessments.map((asm) => (
                <tr key={asm.attempt_id} className="hover:bg-slate-50/75 transition" data-testid={`assessment-row-${asm.attempt_id}`}>
                  <td className="px-5 py-4 font-semibold text-slate-900">
                    {asm.title}
                  </td>
                  <td className="px-5 py-4 text-xs text-slate-500">
                    <div className="flex items-center gap-1.5">
                      <Calendar className="h-3.5 w-3.5 text-slate-400" />
                      <span>{new Date(asm.submitted_at).toLocaleDateString()}</span>
                    </div>
                  </td>
                  <td className="px-5 py-4 text-xs text-slate-700">
                    <span className="font-bold text-slate-900">{asm.score}</span> / {asm.max_points} pts
                  </td>
                  <td className="px-5 py-4">
                    <span
                      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-bold ${
                        asm.percentage >= 75
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : asm.percentage >= 50
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : 'bg-rose-50 text-rose-700 border border-rose-200'
                      }`}
                    >
                      {asm.percentage}%
                    </span>
                  </td>
                  <td className="px-5 py-4 text-right">
                    <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 capitalize">
                      {asm.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
