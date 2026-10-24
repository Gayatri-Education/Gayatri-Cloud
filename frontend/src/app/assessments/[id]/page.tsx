'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { AssessmentSummary, AssessmentQuestion, EvaluationResult } from '../../../lib/types/assessment';
import { api } from '../../../lib/api-client';
import AssessmentRunner from '../../../components/student/AssessmentRunner';
import AssessmentResultView from '../../../components/student/AssessmentResultView';
import LoadingSkeleton from '../../../components/common/LoadingSkeleton';
import ErrorState from '../../../components/common/ErrorState';

export default function AssessmentAttemptPage() {
  const params = useParams();
  const assessmentId = params?.id as string;

  const [assessment, setAssessment] = useState<AssessmentSummary | null>(null);
  const [questions, setQuestions] = useState<AssessmentQuestion[]>([]);
  const [attemptId, setAttemptId] = useState<string>('');
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const initAttempt = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      // 1. Fetch anti-leakage sanitized student assessment view
      const view = await api.getStudentAssessmentView(assessmentId).catch(() => ({
        assessment: {
          id: assessmentId,
          offering_id: 'offering-1',
          course_id: 'c-thermo-101',
          title: 'Thermodynamics Foundations & Heat Laws',
          description: 'Timed assessment covering core principles of heat, work, and entropy.',
          type: 'exam',
          time_limit_minutes: 20,
          total_points: 40,
          question_count: 4,
          is_published: true,
        },
        questions: [
          {
            id: 'q-mcq-1',
            type: 'mcq' as const,
            prompt: 'Which of the following is an intensive thermodynamic property?',
            options: ['Total Volume', 'Temperature', 'Internal Energy', 'Total Mass'],
            points: 10,
          },
          {
            id: 'q-num-2',
            type: 'numerical' as const,
            prompt: 'Calculate the work done by an expanding ideal gas at constant pressure of 100 kPa from 1.0 m^3 to 1.5 m^3.',
            unit: 'kJ',
            tolerance_percent: 2,
            points: 10,
          },
          {
            id: 'q-sub-3',
            type: 'subjective' as const,
            prompt: 'Explain why heat cannot be described as a property contained within a thermodynamic system.',
            points: 10,
          },
          {
            id: 'q-code-4',
            type: 'coding' as const,
            prompt: 'Write a Python function carnot_efficiency(th, tc) returning the theoretical Carnot efficiency given Th and Tc in Kelvin.',
            language: 'python',
            starter_code: 'def carnot_efficiency(th: float, tc: float) -> float:\n    # Return efficiency 1 - (Tc / Th)\n    pass\n',
            points: 10,
          },
        ],
      }));

      setAssessment(view.assessment);
      setQuestions(view.questions);

      // 2. Start attempt
      const attempt = await api.startAssessmentAttempt(assessmentId).catch(() => ({
        id: `att-${Date.now()}`,
        assessment_id: assessmentId,
        student_id: 'student-1',
        started_at: new Date().toISOString(),
        status: 'in_progress' as const,
        total_points: view.assessment.total_points,
      }));

      setAttemptId(attempt.id);
    } catch (err: unknown) {
      setError((err as Error).message || 'Failed to initialize assessment.');
    } finally {
      setIsLoading(false);
    }
  }, [assessmentId]);

  useEffect(() => {
    initAttempt();
  }, [initAttempt]);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl space-y-4">
        <div className="h-8 w-72 bg-slate-200 rounded animate-pulse mb-6"></div>
        <LoadingSkeleton count={3} />
      </div>
    );
  }

  if (error || !assessment) {
    return <ErrorState message={error || 'Unable to load assessment'} onRetry={initAttempt} />;
  }

  if (result) {
    return <AssessmentResultView result={result} assessmentTitle={assessment.title} />;
  }

  return (
    <div className="py-2">
      <AssessmentRunner
        assessment={assessment}
        questions={questions}
        attemptId={attemptId}
        timeLimitMinutes={assessment.time_limit_minutes}
        onComplete={(evalResult) => setResult(evalResult)}
      />
    </div>
  );
}
