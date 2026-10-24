'use client';

import React from 'react';
import Link from 'next/link';
import {
  TrendingUp,
  Brain,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Calendar,
  Sparkles,
} from 'lucide-react';
import {
  ConceptMastery,
  MisconceptionItem,
  SpacedReviewReminder,
  MasteryStatus,
} from '../../lib/types/mastery';

interface MasteryRoadmapProps {
  masteries: ConceptMastery[];
  misconceptions: MisconceptionItem[];
  spacedReviews: SpacedReviewReminder[];
}

export default function MasteryRoadmap({
  masteries,
  misconceptions,
  spacedReviews,
}: MasteryRoadmapProps) {
  const safeMasteries = Array.isArray(masteries) ? masteries : [];
  const safeMisconceptions = Array.isArray(misconceptions) ? misconceptions : [];
  const safeReviews = Array.isArray(spacedReviews) ? spacedReviews : [];
  const getStatusBadge = (status: MasteryStatus) => {
    switch (status) {
      case 'master':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'proficient':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'competent':
        return 'bg-sky-100 text-sky-800 border-sky-200';
      case 'developing':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const averageMastery =
    masteries.length > 0
      ? Math.round(
          (masteries.reduce((acc, m) => acc + m.mastery_score, 0) / masteries.length) * 100
        )
      : 0;

  return (
    <div className="space-y-8" data-testid="mastery-roadmap-container">
      {/* Overview Metric Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            <TrendingUp className="h-4 w-4 text-sky-600" />
            Average Mastery
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-900">{averageMastery}%</span>
            <span className="text-xs text-slate-500">across {masteries.length} concepts</span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            Active Misconceptions
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-black text-amber-700">
              {misconceptions.filter((m) => !m.remediated).length}
            </span>
            <span className="text-xs text-slate-500">requiring remediation</span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            <Clock className="h-4 w-4 text-purple-600" />
            Spaced Reviews Due
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-black text-purple-700">{spacedReviews.length}</span>
            <span className="text-xs text-slate-500">scheduled reviews</span>
          </div>
        </div>
      </div>

      {/* Spaced Review Reminders Queue */}
      {safeReviews.length > 0 && (
        <div className="rounded-2xl border border-purple-200 bg-purple-50/50 p-6">
          <div className="flex items-center gap-2 text-sm font-bold text-purple-900 mb-3">
            <Calendar className="h-4 w-4 text-purple-600" />
            <span>Spaced Review Schedule</span>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {safeReviews.map((rev, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between rounded-xl border border-purple-100 bg-white p-3.5 shadow-sm text-xs"
              >
                <div>
                  <div className="font-semibold text-slate-900">{rev.concept_name}</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    Course: {rev.course_title} • Due: {new Date(rev.due_date).toLocaleDateString()}
                  </div>
                </div>
                <Link
                  href={`/tutoring?concept=${encodeURIComponent(rev.concept_name)}`}
                  className="rounded-lg bg-purple-600 px-3 py-1.5 text-[11px] font-semibold text-white hover:bg-purple-700 transition shrink-0 ml-2"
                >
                  Review
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Concept Mastery Progress Cards */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
          <Brain className="h-4 w-4 text-sky-600" />
          <span>Course Concept Mastery Hierarchy</span>
        </h3>

        <div className="space-y-4">
          {safeMasteries.map((m) => {
            const pct = Math.round(m.mastery_score * 100);
            return (
              <div
                key={m.concept_id}
                className="rounded-xl border border-slate-200 p-4 hover:border-slate-300 transition"
                data-testid={`concept-card-${m.concept_id}`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2.5">
                    <span className="font-semibold text-sm text-slate-900">{m.concept_name}</span>
                    <span
                      className={`rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${getStatusBadge(
                        m.status
                      )}`}
                    >
                      {m.status}
                    </span>
                  </div>
                  <span className="text-sm font-black text-slate-900 font-mono">{pct}%</span>
                </div>

                {/* Progress bar */}
                <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden mb-3">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${
                      pct >= 85
                        ? 'bg-purple-600'
                        : pct >= 65
                        ? 'bg-emerald-500'
                        : pct >= 40
                        ? 'bg-sky-500'
                        : 'bg-amber-500'
                    }`}
                    style={{ width: `${pct}%` }}
                  ></div>
                </div>

                <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-500 gap-2">
                  <div className="flex items-center gap-3">
                    <span>Stability: {m.stability} days</span>
                    <span>•</span>
                    <span>Evidence entries: {m.evidence_count}</span>
                  </div>
                  <Link
                    href={`/tutoring?concept=${encodeURIComponent(m.concept_name)}`}
                    className="flex items-center gap-1 font-semibold text-sky-600 hover:text-sky-700"
                  >
                    <Sparkles className="h-3 w-3" />
                    <span>Practice with Tutor</span>
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Misconceptions Remediation Panel */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <span>Identified Misconceptions & Diagnostics</span>
        </h3>

        {safeMisconceptions.length === 0 ? (
          <div className="rounded-xl bg-emerald-50 border border-emerald-100 p-4 text-xs text-emerald-800 flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            <span>No active misconceptions recorded! Great job maintaining conceptual accuracy.</span>
          </div>
        ) : (
          <div className="space-y-3">
            {safeMisconceptions.map((mis) => (
              <div
                key={mis.id}
                className={`rounded-xl border p-4 text-xs ${
                  mis.remediated
                    ? 'border-emerald-200 bg-emerald-50/40 opacity-70'
                    : 'border-amber-200 bg-amber-50/40'
                }`}
                data-testid={`misconception-card-${mis.id}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900">{mis.concept_name}</span>
                    <span className="font-mono text-[10px] text-slate-500">
                      [{mis.misconception_code}]
                    </span>
                  </div>
                  <span
                    className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${
                      mis.remediated
                        ? 'bg-emerald-100 text-emerald-800'
                        : mis.severity === 'high'
                        ? 'bg-rose-100 text-rose-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {mis.remediated ? 'Remediated' : `${mis.severity} Severity`}
                  </span>
                </div>
                <div className="text-slate-700 mt-1">{mis.description}</div>
                <div className="mt-2.5 rounded-lg bg-white/80 p-2.5 border border-slate-200/80 text-[11px] text-slate-600 flex items-center justify-between">
                  <span>
                    <strong>Remediation Strategy:</strong> {mis.remediation_advice}
                  </span>
                  {!mis.remediated && (
                    <Link
                      href={`/tutoring?concept=${encodeURIComponent(
                        mis.concept_name
                      )}&mode=socratic`}
                      className="ml-3 shrink-0 rounded bg-sky-600 px-2.5 py-1 text-[11px] font-semibold text-white hover:bg-sky-700"
                    >
                      Remediate
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
