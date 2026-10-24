'use client';

import React from 'react';
import { ChildProgressSummary } from '../../lib/types/parent';
import { ShieldCheck, BookOpen, Clock, Award, CheckCircle2, TrendingUp } from 'lucide-react';

interface ChildProgressOverviewProps {
  progress: ChildProgressSummary;
}

export default function ChildProgressOverview({ progress }: ChildProgressOverviewProps) {
  const masteryPct = Math.round(progress.overall_mastery * 100);

  return (
    <div className="space-y-6" data-testid="child-progress-overview">
      {/* Privacy Guarantee Banner */}
      <div
        className="flex items-start gap-3 rounded-2xl border border-sky-200 bg-sky-50/70 p-4 text-xs text-sky-900 shadow-2xs"
        data-testid="privacy-guarantee-banner"
      >
        <ShieldCheck className="h-5 w-5 text-sky-600 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <span className="font-bold text-sky-950 uppercase tracking-wider text-[11px]">
            Privacy & Trust Invariant (RQ-025)
          </span>
          <p className="text-slate-700 leading-relaxed font-normal">
            {progress.privacy_disclosure}
          </p>
        </div>
      </div>

      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Overall Mastery
            </span>
            <TrendingUp className="h-4 w-4 text-sky-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-sky-600" data-testid="overall-mastery-score">
            {masteryPct}%
          </div>
          <div className="mt-1 text-xs text-slate-400">Across verified concepts</div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Tutoring Study Time
            </span>
            <Clock className="h-4 w-4 text-indigo-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900" data-testid="study-time-minutes">
            {progress.estimated_study_minutes}m
          </div>
          <div className="mt-1 text-xs text-slate-400">
            {progress.total_tutoring_sessions} active sessions
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Enrolled Courses
            </span>
            <BookOpen className="h-4 w-4 text-emerald-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900" data-testid="enrolled-courses-count">
            {progress.enrolled_courses.length}
          </div>
          <div className="mt-1 text-xs text-slate-400">In current academic term</div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Active Focus Areas
            </span>
            <Award className="h-4 w-4 text-amber-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900" data-testid="misconceptions-count">
            {progress.active_misconceptions_count}
          </div>
          <div className="mt-1 text-xs text-slate-400">Targeted for remediation</div>
        </div>
      </div>

      {/* Grid: Top Concept Competencies & Enrolled Courses */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Concept Competencies */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
          <h3 className="text-base font-bold text-slate-900">
            Verified Concept Competencies
          </h3>

          {progress.top_concepts.length === 0 ? (
            <div className="text-sm text-slate-400 py-4 text-center">
              No learning mastery recorded yet.
            </div>
          ) : (
            <div className="space-y-3" data-testid="top-concepts-list">
              {progress.top_concepts.map((concept) => {
                const cPct = Math.round(concept.mastery_score * 100);
                return (
                  <div key={concept.concept_id} className="space-y-1" data-testid={`concept-${concept.concept_id}`}>
                    <div className="flex justify-between text-xs font-medium text-slate-700">
                      <span className="font-semibold">{concept.concept_id}</span>
                      <span className="text-slate-500">
                        {cPct}% (stability: {concept.stability_days}d)
                      </span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          cPct >= 75
                            ? 'bg-emerald-500'
                            : cPct >= 50
                            ? 'bg-amber-500'
                            : 'bg-rose-500'
                        }`}
                        style={{ width: `${cPct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Enrolled Courses */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
          <h3 className="text-base font-bold text-slate-900">
            Current Course Offerings
          </h3>

          {progress.enrolled_courses.length === 0 ? (
            <div className="text-sm text-slate-400 py-4 text-center">
              Student is not currently enrolled in any class offerings.
            </div>
          ) : (
            <div className="space-y-2.5" data-testid="enrolled-courses-list">
              {progress.enrolled_courses.map((course, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-3"
                >
                  <div className="flex items-center gap-2.5">
                    <BookOpen className="h-4 w-4 text-sky-600 shrink-0" />
                    <span className="text-xs font-semibold text-slate-800">
                      {course.title}
                    </span>
                  </div>
                  <span className="rounded-md bg-white border border-slate-200 px-2 py-0.5 text-[11px] font-medium text-slate-600">
                    {course.term}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
