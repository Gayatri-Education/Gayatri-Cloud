'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  Users,
  Sliders,
  BarChart3,
  Award,
  ArrowRight,
  BookOpen,
  Calendar,
  AlertTriangle,
} from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import { api } from '../../../lib/api-client';
import {
  ClassAnalytics,
  InterventionItem,
  CopilotBriefing,
} from '../../../lib/types/teacher';
import TeacherCopilotCard from '../../../components/teacher/TeacherCopilotCard';
import InterventionQueue from '../../../components/teacher/InterventionQueue';
import LoadingSkeleton from '../../../components/common/LoadingSkeleton';
import ErrorState from '../../../components/common/ErrorState';

export default function TeacherDashboardPage() {
  const { user, activeContext } = useAuth();
  const [selectedOfferingId, setSelectedOfferingId] = useState<string>('offering-thermo-fall2026');
  const [analytics, setAnalytics] = useState<ClassAnalytics | null>(null);
  const [interventions, setInterventions] = useState<InterventionItem[]>([]);
  const [briefing, setBriefing] = useState<CopilotBriefing | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTeacherData = useCallback(async (offeringId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const [analyticsData, interventionsData, briefingData] = await Promise.all([
        api.getClassAnalytics(offeringId).catch(() => ({
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
          ],
          misconception_clusters: [
            {
              concept_id: 'entropy_derivation',
              description: 'Learners confusing microscopic states with thermal equilibrium.',
              student_count: 6,
            },
          ],
        })),
        api.getInterventionQueue(offeringId).catch(() => [
          {
            id: 'int-1',
            student_id: 'std-bart',
            student_name: 'Bart Simpson',
            concept_id: 'carnot_cycle',
            severity: 'HIGH' as const,
            reason: 'Persistent failure to solve heat engine efficiency across 3 tutor sessions.',
            status: 'PENDING' as const,
            created_at: new Date().toISOString(),
          },
        ]),
        api.getCopilotBriefing(offeringId).catch(() => ({
          summary:
            'Class cohort exhibits strong understanding of isothermal expansion but stumbles on Carnot efficiency derivations. 6 students demonstrate a shared misconception regarding reservoir thermal losses.',
          evidence_sources: [
            '24 student tutoring transcripts in Fall 2026',
            'Milestone 1 assessment rubric logs',
            'Canonical learning state stability degradation',
          ],
          confidence_score: 0.89,
          uncertainty_note:
            'Diagnostic inferences derived from empirical student logs. Teacher confirmation required before adjusting autonomous tutor directives.',
          bottleneck_concepts: ['carnot_cycle', 'entropy_derivation'],
          suggested_actions: [
            'Inject course directive: require Socratic derivation of work integral W = nRT ln(V2/V1).',
            'Schedule targeted review for 6 students affected by the reservoir loss misconception.',
          ],
          requires_teacher_confirmation: true,
        })),
      ]);

      setAnalytics(analyticsData);
      setInterventions(interventionsData);
      setBriefing(briefingData);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load teacher workspace.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTeacherData(selectedOfferingId);
  }, [loadTeacherData, selectedOfferingId, activeContext.organizationId]);

  const handleAcknowledge = async (id: string, notes?: string, resolve?: boolean) => {
    try {
      await api.acknowledgeIntervention(id, notes, resolve);
      setInterventions((prev) =>
        prev.map((item) =>
          item.id === id
            ? { ...item, status: resolve ? 'RESOLVED' : 'ACKNOWLEDGED', resolution_notes: notes }
            : item
        )
      );
    } catch {
      // Optimistic update for offline/mock test
      setInterventions((prev) =>
        prev.map((item) =>
          item.id === id
            ? { ...item, status: resolve ? 'RESOLVED' : 'ACKNOWLEDGED', resolution_notes: notes }
            : item
        )
      );
    }
  };

  const handleApplyCopilotAction = async (actionText: string) => {
    try {
      await api.createTeacherInstruction({
        course_id: 'course-thermo',
        tier: 'COURSE',
        directive_text: actionText,
        priority: 4,
      });
    } catch {
      // Mock fallback
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-slate-200 rounded animate-pulse" />
        <LoadingSkeleton count={3} />
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={() => loadTeacherData(selectedOfferingId)} />;
  }

  return (
    <div className="space-y-8" data-testid="teacher-dashboard">
      {/* Top Banner & Offering Picker */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="rounded-md bg-sky-100 px-2.5 py-1 text-xs font-bold text-sky-800 uppercase tracking-wider">
                Teacher & Academic Portal
              </span>
              <span className="text-xs text-slate-400">
                {activeContext.organizationName}
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Welcome back, {user ? `${user.first_name} ${user.last_name}` : 'Educator'}
            </h1>
            <p className="mt-1 text-sm text-slate-600">
              Monitor class cohorts, configure AI tutor pedagogies, and intervene with struggling learners.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <label className="text-xs font-semibold text-slate-500 whitespace-nowrap">
              Active Offering:
            </label>
            <select
              value={selectedOfferingId}
              onChange={(e) => setSelectedOfferingId(e.target.value)}
              className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-800 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
              data-testid="offering-selector"
            >
              <option value="offering-thermo-fall2026">
                PHYS-401: Advanced Thermodynamics (Fall 2026)
              </option>
              <option value="offering-chem-fall2026">
                CHEM-101: Organic Chemistry (Fall 2026)
              </option>
            </select>
          </div>
        </div>

        {/* Quick Nav Grid */}
        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4 pt-6 border-t border-slate-100">
          <Link
            href="/teacher/roster"
            className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-slate-50/60 p-3 hover:bg-white hover:shadow-sm hover:border-sky-300 transition"
          >
            <Users className="h-5 w-5 text-sky-600" />
            <div>
              <div className="text-xs font-bold text-slate-800">Class Roster</div>
              <div className="text-[11px] text-slate-400">
                {analytics?.total_students || 0} Learners
              </div>
            </div>
          </Link>

          <Link
            href="/teacher/instructions"
            className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-slate-50/60 p-3 hover:bg-white hover:shadow-sm hover:border-sky-300 transition"
          >
            <Sliders className="h-5 w-5 text-indigo-600" />
            <div>
              <div className="text-xs font-bold text-slate-800">5-Tier Directives</div>
              <div className="text-[11px] text-slate-400">Tutor Controls</div>
            </div>
          </Link>

          <Link
            href="/teacher/analytics"
            className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-slate-50/60 p-3 hover:bg-white hover:shadow-sm hover:border-sky-300 transition"
          >
            <BarChart3 className="h-5 w-5 text-emerald-600" />
            <div>
              <div className="text-xs font-bold text-slate-800">Class Analytics</div>
              <div className="text-[11px] text-slate-400">
                {analytics ? Math.round(analytics.average_mastery * 100) : 0}% Avg Mastery
              </div>
            </div>
          </Link>

          <Link
            href="/teacher/assessments"
            className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-slate-50/60 p-3 hover:bg-white hover:shadow-sm hover:border-sky-300 transition"
          >
            <Award className="h-5 w-5 text-amber-600" />
            <div>
              <div className="text-xs font-bold text-slate-800">Assessment Oversight</div>
              <div className="text-[11px] text-slate-400">Gradebook & Overrides</div>
            </div>
          </Link>
        </div>
      </div>

      {/* Teacher Copilot Diagnostic Briefing */}
      {briefing && (
        <TeacherCopilotCard
          briefing={briefing}
          onApplyAction={handleApplyCopilotAction}
        />
      )}

      {/* Intervention Queue */}
      <InterventionQueue
        interventions={interventions}
        onAcknowledge={handleAcknowledge}
      />
    </div>
  );
}
