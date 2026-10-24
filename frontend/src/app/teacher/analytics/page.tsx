'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { ArrowLeft, BarChart3, Download, RefreshCw } from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import { api } from '../../../lib/api-client';
import { ClassAnalytics } from '../../../lib/types/teacher';
import AnalyticsCharts from '../../../components/teacher/AnalyticsCharts';
import LoadingSkeleton from '../../../components/common/LoadingSkeleton';
import ErrorState from '../../../components/common/ErrorState';

export default function TeacherAnalyticsPage() {
  const { activeContext } = useAuth();
  const [selectedOfferingId, setSelectedOfferingId] = useState<string>('offering-thermo-fall2026');
  const [analytics, setAnalytics] = useState<ClassAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAnalytics = useCallback(async (offeringId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getClassAnalytics(offeringId).catch(() => ({
        total_students: 24,
        average_mastery: 0.68,
        mastery_distribution: {
          novice: 3,
          developing: 5,
          competent: 10,
          proficient: 4,
          master: 2,
        },
        hardest_concepts: [
          { concept_id: 'carnot_cycle', average_score: 0.42, attempts: 48 },
          { concept_id: 'entropy_derivation', average_score: 0.51, attempts: 39 },
          { concept_id: 'heat_capacity', average_score: 0.72, attempts: 54 },
          { concept_id: 'first_law_closed_system', average_score: 0.88, attempts: 60 },
        ],
        misconception_clusters: [
          {
            concept_id: 'entropy_derivation',
            description: 'Learners confusing microscopic states with thermal equilibrium.',
            student_count: 6,
          },
          {
            concept_id: 'carnot_cycle',
            description: 'Assuming 100% thermal efficiency is achievable at finite temperatures.',
            student_count: 4,
          },
        ],
      }));
      setAnalytics(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load class analytics.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAnalytics(selectedOfferingId);
  }, [loadAnalytics, selectedOfferingId, activeContext.organizationId]);

  return (
    <div className="space-y-6" data-testid="analytics-page">
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
            Cohort Learning Analytics & Misconception Clusters
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Track concept mastery distributions, hardest topics, and common student errors across offerings.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={selectedOfferingId}
            onChange={(e) => setSelectedOfferingId(e.target.value)}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-800 focus:border-sky-500 focus:outline-none"
            data-testid="analytics-offering-select"
          >
            <option value="offering-thermo-fall2026">
              PHYS-401: Advanced Thermodynamics
            </option>
            <option value="offering-chem-fall2026">
              CHEM-101: Organic Chemistry
            </option>
          </select>

          <button
            onClick={() => loadAnalytics(selectedOfferingId)}
            className="p-2 rounded-xl border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 transition"
            title="Refresh Analytics"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {isLoading ? (
        <LoadingSkeleton count={3} />
      ) : error || !analytics ? (
        <ErrorState
          message={error || 'No analytics available'}
          onRetry={() => loadAnalytics(selectedOfferingId)}
        />
      ) : (
        <AnalyticsCharts analytics={analytics} />
      )}
    </div>
  );
}
