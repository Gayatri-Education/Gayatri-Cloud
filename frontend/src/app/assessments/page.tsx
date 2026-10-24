'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { Award, Clock, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react';
import { AssessmentSummary } from '../../lib/types/assessment';
import { api } from '../../lib/api-client';
import LoadingSkeleton from '../../components/common/LoadingSkeleton';
import ErrorState from '../../components/common/ErrorState';

export default function AssessmentsListPage() {
  const [assessments, setAssessments] = useState<AssessmentSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAssessments = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getOfferingAssessments('offering-1');
      if (data && data.length > 0) {
        setAssessments(data);
      } else {
        // Fallback demo assessments
        setAssessments([
          {
            id: 'asm-thermo-quiz-1',
            offering_id: 'offering-1',
            course_id: 'c-thermo-101',
            title: 'Thermodynamics Foundations & Heat Laws',
            description:
              'Comprehensive assessment covering MCQ, numerical calculations with units, subjective thermodynamic reasoning, and code simulations.',
            type: 'quiz',
            time_limit_minutes: 25,
            total_points: 50,
            question_count: 5,
            is_published: true,
          },
          {
            id: 'asm-dsa-trees',
            offering_id: 'offering-2',
            course_id: 'c-dsa-201',
            title: 'Binary Search Trees & Heap Invariants',
            description:
              'Algorithmic verification, AST syntax checks, and complexity analysis.',
            type: 'exam',
            time_limit_minutes: 45,
            total_points: 100,
            question_count: 4,
            is_published: true,
          },
        ]);
      }
    } catch {
      // Default fallback
      setAssessments([
        {
          id: 'asm-thermo-quiz-1',
          offering_id: 'offering-1',
          course_id: 'c-thermo-101',
          title: 'Thermodynamics Foundations & Heat Laws',
          description:
            'Comprehensive assessment covering MCQ, numerical calculations with units, subjective thermodynamic reasoning, and code simulations.',
          type: 'quiz',
          time_limit_minutes: 25,
          total_points: 50,
          question_count: 5,
          is_published: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAssessments();
  }, [loadAssessments]);

  return (
    <div className="space-y-6" data-testid="assessments-list-page">
      <div>
        <h1 className="text-2xl font-black text-slate-900 sm:text-3xl">My Assessments</h1>
        <p className="mt-1 text-sm text-slate-500">
          Timed examinations and practice quizzes with anti-leakage protection and deterministic grading.
        </p>
      </div>

      {isLoading ? (
        <LoadingSkeleton count={3} />
      ) : error ? (
        <ErrorState message={error} onRetry={loadAssessments} />
      ) : (
        <div className="space-y-4">
          {(Array.isArray(assessments) ? assessments : []).map((asm) => (
            <div
              key={asm.id}
              className="flex flex-col sm:flex-row items-start sm:items-center justify-between rounded-2xl border border-slate-200 bg-white p-6 shadow-sm gap-4"
              data-testid={`assessment-item-${asm.id}`}
            >
              <div className="space-y-1.5 max-w-2xl">
                <div className="flex items-center gap-2">
                  <span className="rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-semibold uppercase text-emerald-800">
                    {asm.type}
                  </span>
                  <span className="text-xs font-medium text-slate-400">
                    {asm.question_count} questions
                  </span>
                </div>
                <h3 className="text-lg font-bold text-slate-900">{asm.title}</h3>
                <p className="text-xs text-slate-500 leading-relaxed">{asm.description}</p>
                <div className="flex items-center gap-4 text-xs text-slate-500 pt-1">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5 text-slate-400" />
                    {asm.time_limit_minutes ? `${asm.time_limit_minutes} mins` : 'Untimed'}
                  </span>
                  <span>•</span>
                  <span>{asm.total_points} total points</span>
                </div>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                <Link
                  href={`/assessments/${asm.id}`}
                  className="flex items-center gap-1.5 rounded-xl bg-emerald-600 px-5 py-2.5 text-xs font-semibold text-white hover:bg-emerald-700 shadow-sm transition"
                  data-testid={`start-assessment-${asm.id}`}
                >
                  <span>Start Attempt</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
