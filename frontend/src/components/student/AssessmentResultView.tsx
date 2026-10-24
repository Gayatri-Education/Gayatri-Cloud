'use client';

import React from 'react';
import Link from 'next/link';
import {
  Award,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Brain,
  HelpCircle,
} from 'lucide-react';
import { EvaluationResult } from '../../lib/types/assessment';

interface AssessmentResultViewProps {
  result: EvaluationResult;
  assessmentTitle: string;
}

export default function AssessmentResultView({
  result,
  assessmentTitle,
}: AssessmentResultViewProps) {
  const isPassed = result.percentage >= 60;

  return (
    <div
      className="mx-auto max-w-4xl space-y-6"
      data-testid="assessment-result-view"
    >
      {/* Top Score Banner */}
      <div
        className={`rounded-2xl border p-8 text-center shadow-sm ${
          isPassed
            ? 'border-emerald-200 bg-emerald-50/50'
            : 'border-amber-200 bg-amber-50/50'
        }`}
      >
        <div
          className={`mx-auto flex h-14 w-14 items-center justify-center rounded-full mb-4 ${
            isPassed ? 'bg-emerald-100 text-emerald-600' : 'bg-amber-100 text-amber-600'
          }`}
        >
          {isPassed ? <Award className="h-7 w-7" /> : <AlertTriangle className="h-7 w-7" />}
        </div>

        <h2 className="text-2xl font-extrabold text-slate-900">{assessmentTitle} — Result</h2>
        <p className="mt-1 text-sm text-slate-600">
          Submitted on {new Date(result.submitted_at).toLocaleString()}
        </p>

        <div className="mt-6 flex items-center justify-center gap-8">
          <div>
            <div className="text-3xl font-black text-slate-900">
              {result.total_score} / {result.max_points}
            </div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1">
              Score
            </div>
          </div>
          <div className="h-10 w-px bg-slate-300"></div>
          <div>
            <div
              className={`text-3xl font-black ${
                isPassed ? 'text-emerald-700' : 'text-amber-700'
              }`}
            >
              {Math.round(result.percentage)}%
            </div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1">
              Percentage
            </div>
          </div>
          <div className="h-10 w-px bg-slate-300"></div>
          <div>
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold ${
                isPassed
                  ? 'bg-emerald-100 text-emerald-800'
                  : 'bg-amber-100 text-amber-800'
              }`}
            >
              {isPassed ? <CheckCircle2 className="h-3.5 w-3.5" /> : <AlertTriangle className="h-3.5 w-3.5" />}
              {isPassed ? 'Passed' : 'Needs Practice'}
            </span>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1">
              Status
            </div>
          </div>
        </div>

        {/* Automated Mastery Feedback Banner */}
        <div className="mt-6 rounded-xl bg-white/80 border border-slate-200/80 p-4 text-xs text-slate-700 flex items-center justify-between max-w-xl mx-auto text-left shadow-sm">
          <div className="flex items-center gap-2.5">
            <Brain className="h-4 w-4 text-sky-600 shrink-0" />
            <span>
              Your learning evidence has been processed. Concept masteries and spaced review intervals have been updated.
            </span>
          </div>
          <Link
            href="/mastery"
            className="flex items-center gap-1 font-semibold text-sky-600 hover:text-sky-700 shrink-0 ml-3"
          >
            <span>Roadmap</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      {/* Misconceptions Alert Panel (if any detected) */}
      {result.misconceptions_detected && result.misconceptions_detected.length > 0 && (
        <div
          className="rounded-2xl border border-rose-200 bg-rose-50/70 p-6"
          data-testid="detected-misconceptions-panel"
        >
          <div className="flex items-center gap-2 text-rose-900 font-bold text-sm mb-3">
            <AlertTriangle className="h-4 w-4 text-rose-600" />
            <span>Remediation Needed: {result.misconceptions_detected.length} Detected Misconception(s)</span>
          </div>
          <div className="space-y-2">
            {result.misconceptions_detected.map((miscon, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-rose-200/80 bg-white p-3 text-xs text-slate-800 flex items-start gap-2.5"
              >
                <HelpCircle className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-rose-800 font-mono text-[11px]">
                    {miscon}
                  </div>
                  <div className="text-slate-600 mt-0.5">
                    Recommended action: Start a Socratic tutoring turn targeted specifically at this misconception.
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Question by Question Evaluation Details */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-base font-bold text-slate-900 mb-4">Question Breakdown</h3>

        <div className="space-y-4">
          {Object.entries(result.question_results || {}).map(([qId, qRes], idx) => (
            <div
              key={qId}
              className="rounded-xl border border-slate-200 p-4 text-xs"
              data-testid={`question-result-${idx}`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-slate-800">Question {idx + 1}</span>
                <span className="font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">
                  {qRes.earned_points} / {qRes.max_points} points
                </span>
              </div>

              <div className="text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">
                {qRes.feedback}
              </div>

              {/* Rubric criteria breakdown if present */}
              {qRes.criteria && qRes.criteria.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-100 space-y-1.5">
                  <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                    Rubric Criteria Breakdown
                  </div>
                  {qRes.criteria.map((c, cIdx) => (
                    <div
                      key={cIdx}
                      className="flex items-center justify-between text-[11px] text-slate-700 bg-white p-1.5 rounded border border-slate-100"
                    >
                      <span>{c.criterion}</span>
                      <span className="font-medium text-slate-900">
                        {c.score} / {c.max_score}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Action Footer */}
      <div className="flex justify-between items-center pt-2">
        <Link
          href="/assessments"
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
        >
          Back to Assessments
        </Link>
        <Link
          href="/mastery"
          className="flex items-center gap-1.5 rounded-lg bg-sky-600 px-5 py-2 text-xs font-semibold text-white hover:bg-sky-700"
        >
          <TrendingUp className="h-4 w-4" />
          <span>View Updated Concept Mastery</span>
        </Link>
      </div>
    </div>
  );
}
