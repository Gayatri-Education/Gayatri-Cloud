'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { ArrowLeft, Sliders, Info, ShieldCheck } from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import { api } from '../../../lib/api-client';
import { TeacherInstructionItem } from '../../../lib/types/teacher';
import InstructionEditor from '../../../components/teacher/InstructionEditor';
import LoadingSkeleton from '../../../components/common/LoadingSkeleton';
import ErrorState from '../../../components/common/ErrorState';

export default function TeacherInstructionsPage() {
  const { activeContext } = useAuth();
  const [selectedCourseId, setSelectedCourseId] = useState<string>('course-thermo');
  const [instructions, setInstructions] = useState<TeacherInstructionItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadInstructions = useCallback(async (courseId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getTeacherInstructions(courseId).catch(() => [
        {
          id: 'inst-1',
          course_id: courseId,
          tier: 'COURSE' as const,
          directive_text:
            'Require conceptual derivation of work integral W = nRT ln(V2/V1) before confirming student calculations.',
          priority: 5,
          is_active: true,
          created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
        },
        {
          id: 'inst-2',
          course_id: courseId,
          tier: 'CLASS' as const,
          directive_text:
            'Use Socratic questioning when students confuse isothermal with adiabatic processes.',
          priority: 3,
          is_active: true,
          created_at: new Date(Date.now() - 86400000 * 5).toISOString(),
        },
      ]);
      setInstructions(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load teacher instructions.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadInstructions(selectedCourseId);
  }, [loadInstructions, selectedCourseId, activeContext.organizationId]);

  const handleCreateInstruction = async (data: {
    tier: 'ORG' | 'COURSE' | 'CLASS' | 'STUDENT' | 'SESSION';
    directive_text: string;
    priority: number;
  }) => {
    const created = await api
      .createTeacherInstruction({
        course_id: selectedCourseId,
        tier: data.tier,
        directive_text: data.directive_text,
        priority: data.priority,
      })
      .catch(() => ({
        id: `inst-${Date.now()}`,
        course_id: selectedCourseId,
        tier: data.tier,
        directive_text: data.directive_text,
        priority: data.priority,
        is_active: true,
        created_at: new Date().toISOString(),
      }));

    setInstructions((prev) => [created, ...prev]);
  };

  const handleDeactivateInstruction = async (instructionId: string) => {
    await api.deactivateTeacherInstruction(instructionId).catch(() => {});
    setInstructions((prev) => prev.filter((i) => i.id !== instructionId));
  };

  return (
    <div className="space-y-6" data-testid="instructions-page">
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
            5-Tier Pedagogical Instruction Cascade
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Define hierarchical constraints and instructional directives that guide the AI Tutor during live learner dialogues.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={selectedCourseId}
            onChange={(e) => setSelectedCourseId(e.target.value)}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-800 focus:border-sky-500 focus:outline-none"
            data-testid="instructions-course-select"
          >
            <option value="course-thermo">PHYS-401: Advanced Thermodynamics</option>
            <option value="course-chem">CHEM-101: Organic Chemistry</option>
          </select>
        </div>
      </div>

      {/* Hierarchy Info Box */}
      <div className="rounded-xl border border-sky-100 bg-sky-50/60 p-4 text-xs text-sky-900 space-y-1">
        <div className="flex items-center gap-1.5 font-bold text-sky-800">
          <Info className="h-4 w-4" />
          <span>Cascade Precedence Rules</span>
        </div>
        <p className="leading-relaxed">
          Directives are evaluated from most specific to broadest:{' '}
          <strong>SESSION &gt; STUDENT &gt; CLASS &gt; COURSE &gt; ORG</strong>. Higher priority numbers (up to 5) take precedence within the same tier. Strict safety boundaries and verified syllabus facts always override teacher directives.
        </p>
      </div>

      {isLoading ? (
        <LoadingSkeleton count={2} />
      ) : error ? (
        <ErrorState message={error} onRetry={() => loadInstructions(selectedCourseId)} />
      ) : (
        <InstructionEditor
          courseId={selectedCourseId}
          instructions={instructions}
          onCreateInstruction={handleCreateInstruction}
          onDeactivateInstruction={handleDeactivateInstruction}
        />
      )}
    </div>
  );
}
