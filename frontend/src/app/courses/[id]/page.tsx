'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  BookOpen,
  ArrowRight,
  ShieldCheck,
  Sparkles,
  Layers,
  Award,
  Clock,
} from 'lucide-react';
import { Course } from '../../../lib/types/course';
import { api } from '../../../lib/api-client';
import LoadingSkeleton from '../../../components/common/LoadingSkeleton';
import ErrorState from '../../../components/common/ErrorState';

export default function CourseDetailsPage() {
  const params = useParams();
  const courseId = params?.id as string;

  const [course, setCourse] = useState<Course | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadCourse = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getCourse(courseId);
      setCourse(data);
    } catch {
      // Fallback demo course
      setCourse({
        id: courseId,
        slug: 'thermodynamics',
        title: 'Foundations of Engineering Thermodynamics',
        description:
          'Comprehensive course covering heat, work, the laws of thermodynamics, entropy production, and cycles with step-by-step Socratic reasoning and automated mastery assessment.',
        subject: 'Physics',
        organization_id: null,
        created_at: new Date().toISOString(),
        versions: [
          {
            id: 'cv-1',
            course_id: courseId,
            version_number: 1,
            title: 'Version 1.0 (Canonical)',
            is_published: true,
            published_at: new Date().toISOString(),
          },
        ],
      });
    } finally {
      setIsLoading(false);
    }
  }, [courseId]);

  useEffect(() => {
    loadCourse();
  }, [loadCourse]);

  if (isLoading) {
    return <LoadingSkeleton count={3} />;
  }

  if (error || !course) {
    return <ErrorState message={error || 'Course not found'} onRetry={loadCourse} />;
  }

  const activeVersion = course.active_version || (course.versions && course.versions[0]);

  return (
    <div className="mx-auto max-w-4xl space-y-8" data-testid="course-details-page">
      {/* Course Header Banner */}
      <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="flex items-center gap-2 mb-3">
          <span className="rounded-md bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-700">
            {course.subject}
          </span>
          {activeVersion && (
            <span className="flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700 border border-emerald-100">
              <ShieldCheck className="h-3.5 w-3.5" />
              Pinned Version: v{activeVersion.version_number}.0
            </span>
          )}
        </div>

        <h1 className="text-2xl font-black text-slate-900 sm:text-3xl">{course.title}</h1>
        <p className="mt-3 text-sm text-slate-600 leading-relaxed">{course.description}</p>

        <div className="mt-8 flex flex-wrap items-center gap-4 pt-6 border-t border-slate-100">
          <Link
            href={`/tutoring?course_id=${course.id}`}
            className="flex items-center gap-2 rounded-xl bg-sky-600 px-6 py-3 text-xs font-semibold text-white hover:bg-sky-700 shadow-sm transition"
          >
            <Sparkles className="h-4 w-4" />
            <span>Launch Socratic AI Tutor</span>
          </Link>
          <Link
            href="/assessments"
            className="flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-5 py-3 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
          >
            <Award className="h-4 w-4" />
            <span>View Assessments</span>
          </Link>
        </div>
      </div>

      {/* Syllabus & Knowledge Hierarchy */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
        <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <Layers className="h-4 w-4 text-sky-600" />
          <span>Curriculum Modules & Concepts</span>
        </h3>

        <div className="space-y-3">
          {[
            {
              module: 'Module 1: Thermodynamic Systems & States',
              concepts: ['Closed vs Open Systems', 'State Functions & Variables', 'Thermal Equilibrium'],
            },
            {
              module: 'Module 2: First Law of Thermodynamics',
              concepts: ['Work and Heat Transfer', 'Internal Energy & Enthalpy', 'Conservation of Energy'],
            },
            {
              module: 'Module 3: Second Law & Entropy',
              concepts: ['Clausius Statement', 'Entropy Production', 'Carnot Efficiency'],
            },
          ].map((m, idx) => (
            <div key={idx} className="rounded-xl border border-slate-100 bg-slate-50/50 p-4 text-xs">
              <div className="font-bold text-slate-800 text-sm mb-2">{m.module}</div>
              <div className="flex flex-wrap gap-2">
                {m.concepts.map((c, cIdx) => (
                  <span
                    key={cIdx}
                    className="rounded-lg bg-white border border-slate-200 px-2.5 py-1 text-slate-700"
                  >
                    {c}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
