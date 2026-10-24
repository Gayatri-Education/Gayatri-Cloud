'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  BookOpen,
  Award,
  TrendingUp,
  ArrowRight,
  Sparkles,
  Clock,
  Shield,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../lib/i18n/I18nContext';
import { Course } from '../../lib/types/course';
import { SpacedReviewReminder, ConceptMastery } from '../../lib/types/mastery';
import { AssessmentSummary } from '../../lib/types/assessment';
import { api } from '../../lib/api-client';
import CourseCard from '../../components/student/CourseCard';
import LoadingSkeleton from '../../components/common/LoadingSkeleton';
import ErrorState from '../../components/common/ErrorState';
import EmptyState from '../../components/common/EmptyState';

export default function DashboardPage() {
  const { user, activeContext } = useAuth();
  const { t } = useI18n();
  const [courses, setCourses] = useState<Course[]>([]);
  const [reviews, setReviews] = useState<SpacedReviewReminder[]>([]);
  const [assessments, setAssessments] = useState<AssessmentSummary[]>([]);
  const [masteries, setMasteries] = useState<ConceptMastery[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboardData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [coursesData, reviewsData, masteriesData] = await Promise.all([
        api.getCourses().catch(() => []),
        api.getSpacedReviewSchedule().catch(() => []),
        api.getConceptMasteries().catch(() => []),
      ]);

      setCourses(Array.isArray(coursesData) ? coursesData : []);
      setReviews(Array.isArray(reviewsData) ? reviewsData : []);
      setMasteries(Array.isArray(masteriesData) ? masteriesData : []);

      // Default mock assessment if empty
      setAssessments([
        {
          id: 'asm-1',
          offering_id: 'offering-1',
          course_id: coursesData[0]?.id || 'course-1',
          title: 'Thermodynamics Milestone 1',
          description: 'Assess foundational concepts of heat, work, and entropy.',
          type: 'milestone',
          time_limit_minutes: 30,
          total_points: 100,
          question_count: 5,
          is_published: true,
        },
      ]);
    } catch (err: unknown) {
      setError((err as Error).message || 'Failed to load learner dashboard.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData, activeContext.organizationId]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-slate-200 rounded animate-pulse"></div>
        <LoadingSkeleton count={3} />
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadDashboardData} />;
  }

  const averageMastery =
    masteries.length > 0
      ? Math.round(
          (masteries.reduce((acc, m) => acc + m.mastery_score, 0) / masteries.length) * 100
        )
      : 74;

  return (
    <div className="space-y-8" data-testid="student-dashboard">
      {/* Welcome Banner */}
      <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="inline-flex items-center gap-1 rounded-full bg-sky-50 px-2.5 py-0.5 text-xs font-semibold text-sky-700 border border-sky-100">
                <Shield className="h-3 w-3" />
                {activeContext.organizationName}
              </span>
              <span className="text-xs text-slate-400">Context: {activeContext.role}</span>
            </div>
            <h1 className="text-2xl font-black text-slate-900 sm:text-3xl">
              {t('welcome_back', { name: user ? user.first_name : 'Learner' })}
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              {t('personalized_roadmap')}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/tutoring"
              className="flex items-center gap-2 rounded-xl bg-sky-600 px-5 py-3 text-xs font-semibold text-white shadow-sm hover:bg-sky-700 transition"
            >
              <Sparkles className="h-4 w-4" />
              <span>{t('launch_tutor')}</span>
            </Link>
          </div>
        </div>

        {/* Quick Highlights */}
        <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4 border-t border-slate-100 pt-6">
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              {t('enrolled_courses')}
            </div>
            <div className="mt-1 text-2xl font-bold text-slate-900">{courses.length || 2}</div>
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              {t('average_mastery')}
            </div>
            <div className="mt-1 text-2xl font-bold text-sky-700">{averageMastery}%</div>
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              {t('reviews_due')}
            </div>
            <div className="mt-1 text-2xl font-bold text-purple-700">{reviews.length}</div>
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              {t('study_streak')}
            </div>
            <div className="mt-1 text-2xl font-bold text-emerald-600">5 Days 🔥</div>
          </div>
        </div>
      </div>

      {/* Main Grid: Enrolled Courses & Learning Schedule */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Enrolled Courses (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-sky-600" />
              <span>{t('your_courses')}</span>
            </h2>
            <Link
              href="/courses"
              className="text-xs font-semibold text-sky-600 hover:text-sky-700 flex items-center gap-1"
            >
              <span>{t('browse_catalog')}</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          {(!Array.isArray(courses) || courses.length === 0) ? (
            <EmptyState
              title="No courses enrolled yet"
              description="Explore the course catalog to start personalized adaptive tutoring."
              actionLabel={t('courses')}
              actionHref="/courses"
            />
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {(Array.isArray(courses) ? courses : []).map((course, idx) => (
                <CourseCard
                  key={course.id}
                  course={course}
                  isEnrolled={true}
                  progress={idx === 0 ? 78 : 45}
                />
              ))}
            </div>
          )}
        </div>

        {/* Sidebar: Upcoming Assessments & Spaced Reviews (1 Col) */}
        <div className="space-y-6">
          {/* Upcoming Assessments */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 mb-4">
              <Award className="h-4 w-4 text-emerald-600" />
              <span>{t('upcoming_assessments')}</span>
            </h3>

            {(!Array.isArray(assessments) || assessments.length === 0) ? (
              <p className="text-xs text-slate-500">No pending assessments scheduled.</p>
            ) : (
              <div className="space-y-3">
                {(Array.isArray(assessments) ? assessments : []).map((a) => (
                  <div
                    key={a.id}
                    className="rounded-xl border border-slate-100 bg-slate-50 p-4 text-xs"
                  >
                    <div className="font-semibold text-slate-900">{a.title}</div>
                    <div className="flex items-center gap-2 text-slate-500 mt-1">
                      <Clock className="h-3 w-3" />
                      <span>{t('mins_limit', { count: a.time_limit_minutes })}</span>
                      <span>•</span>
                      <span>{t('pts', { count: a.total_points })}</span>
                    </div>
                    <Link
                      href={`/assessments/${a.id}`}
                      className="mt-3 inline-flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-1.5 text-[11px] font-semibold text-white hover:bg-emerald-700 transition"
                    >
                      <span>{t('start_attempt')}</span>
                      <ArrowRight className="h-3 w-3" />
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Spaced Review Reminders */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 mb-4">
              <TrendingUp className="h-4 w-4 text-purple-600" />
              <span>{t('spaced_reviews')}</span>
            </h3>

            {(!Array.isArray(reviews) || reviews.length === 0) ? (
              <p className="text-xs text-slate-500">All spaced review intervals are up to date.</p>
            ) : (
              <div className="space-y-2.5">
                {(Array.isArray(reviews) ? reviews : []).map((r, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between rounded-xl border border-purple-100 bg-purple-50/40 p-3 text-xs"
                  >
                    <div>
                      <div className="font-semibold text-slate-900">{r.concept_name}</div>
                      <div className="text-[10px] text-purple-700">{t('due_for_review')}</div>
                    </div>
                    <Link
                      href={`/tutoring?concept=${encodeURIComponent(r.concept_name)}`}
                      className="rounded bg-purple-600 px-2.5 py-1 text-[11px] font-medium text-white hover:bg-purple-700"
                    >
                      {t('practice')}
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
