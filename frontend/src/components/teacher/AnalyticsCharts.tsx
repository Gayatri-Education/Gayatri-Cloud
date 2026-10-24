'use client';

import React from 'react';
import { ClassAnalytics } from '../../lib/types/teacher';
import { BarChart3, AlertTriangle, CheckCircle2, TrendingDown } from 'lucide-react';

interface AnalyticsChartsProps {
  analytics: ClassAnalytics;
}

export default function AnalyticsCharts({ analytics }: AnalyticsChartsProps) {
  const total_students = analytics?.total_students || 0;
  const average_mastery = analytics?.average_mastery || 0;
  const hardestConcepts = Array.isArray(analytics?.hardest_concepts) ? analytics.hardest_concepts : [];
  const misconceptionClusters = Array.isArray(analytics?.misconception_clusters) ? analytics.misconception_clusters : [];

  const dist = analytics?.mastery_distribution || {
    novice: 0,
    developing: 0,
    competent: 0,
    proficient: 0,
    master: 0,
  };

  const totalBucketStudents =
    (dist.novice || 0) +
    (dist.developing || 0) +
    (dist.competent || 0) +
    (dist.proficient || 0) +
    (dist.master || 0);

  const buckets = [
    { label: 'Novice (<40%)', count: dist.novice || 0, color: 'bg-rose-500', barBg: 'bg-rose-100' },
    { label: 'Developing (40-59%)', count: dist.developing || 0, color: 'bg-amber-500', barBg: 'bg-amber-100' },
    { label: 'Competent (60-74%)', count: dist.competent || 0, color: 'bg-sky-500', barBg: 'bg-sky-100' },
    { label: 'Proficient (75-89%)', count: dist.proficient || 0, color: 'bg-indigo-500', barBg: 'bg-indigo-100' },
    { label: 'Master (90-100%)', count: dist.master || 0, color: 'bg-emerald-500', barBg: 'bg-emerald-100' },
  ];

  return (
    <div className="space-y-6" data-testid="analytics-charts">
      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Total Enrolled Cohort
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900" data-testid="metric-total-students">
            {total_students}
          </div>
          <div className="mt-1 text-xs text-slate-400">Active learners in offering</div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Average Cohort Mastery
          </div>
          <div className="mt-2 text-2xl font-bold text-sky-600" data-testid="metric-average-mastery">
            {Math.round(average_mastery * 100)}%
          </div>
          <div className="mt-1 text-xs text-slate-400">Calculated across canonical states</div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Active Misconception Clusters
          </div>
          <div className="mt-2 text-2xl font-bold text-rose-600" data-testid="metric-misconception-count">
            {misconception_clusters.length}
          </div>
          <div className="mt-1 text-xs text-slate-400">Persistent across multiple learners</div>
        </div>
      </div>

      {/* Cohort Mastery Distribution */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-sky-600" />
          <h3 className="text-base font-semibold text-slate-900">
            Cohort Mastery Distribution
          </h3>
        </div>

        <div className="space-y-3" data-testid="mastery-distribution-bars">
          {buckets.map((b) => {
            const pct =
              totalBucketStudents > 0
                ? Math.round((b.count / totalBucketStudents) * 100)
                : 0;
            return (
              <div key={b.label} className="space-y-1">
                <div className="flex justify-between text-xs font-medium text-slate-700">
                  <span>{b.label}</span>
                  <span>
                    {b.count} students ({pct}%)
                  </span>
                </div>
                <div className={`h-3 w-full rounded-full ${b.barBg} overflow-hidden`}>
                  <div
                    className={`h-full rounded-full ${b.color} transition-all duration-300`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Grid: Hardest Concepts & Misconception Clusters */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Hardest Concepts */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <TrendingDown className="h-5 w-5 text-amber-600" />
            <h3 className="text-base font-semibold text-slate-900">
              Hardest Concepts (Lowest Class Mastery)
            </h3>
          </div>

          {hardestConcepts.length === 0 ? (
            <div className="text-sm text-slate-400 py-4 text-center">
              No concept difficulty metrics available yet.
            </div>
          ) : (
            <div className="space-y-2.5" data-testid="hardest-concepts-list">
              {hardestConcepts.map((c) => (
                <div
                  key={c.concept_id}
                  className="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50/70 p-3"
                  data-testid={`concept-item-${c.concept_id}`}
                >
                  <div>
                    <div className="font-semibold text-sm text-slate-800">
                      {c.concept_id}
                    </div>
                    <div className="text-xs text-slate-400">
                      {c.attempts} learner evaluations
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-bold text-amber-600">
                      {Math.round(c.average_score * 100)}%
                    </span>
                    <div className="text-[10px] text-slate-400">avg score</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Misconception Clusters */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-rose-600" />
            <h3 className="text-base font-semibold text-slate-900">
              Cohort Misconception Clusters
            </h3>
          </div>

          {misconceptionClusters.length === 0 ? (
            <div className="text-sm text-slate-400 py-4 text-center flex items-center justify-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              <span>No shared misconceptions detected across the cohort.</span>
            </div>
          ) : (
            <div className="space-y-2.5" data-testid="misconceptions-list">
              {misconceptionClusters.map((m, idx) => (
                <div
                  key={idx}
                  className="rounded-lg border border-rose-100 bg-rose-50/50 p-3 space-y-1"
                  data-testid={`misconception-cluster-${m.concept_id}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="rounded bg-rose-100 px-2 py-0.5 text-xs font-semibold text-rose-800">
                      {m.concept_id}
                    </span>
                    <span className="text-xs font-bold text-rose-700">
                      {m.student_count} {m.student_count === 1 ? 'student' : 'students'} affected
                    </span>
                  </div>
                  <p className="text-xs text-slate-700 leading-normal">
                    {m.description}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
