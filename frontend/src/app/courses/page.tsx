'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { BookOpen, Search, Filter } from 'lucide-react';
import { Course } from '../../lib/types/course';
import { api } from '../../lib/api-client';
import CourseCard from '../../components/student/CourseCard';
import LoadingSkeleton from '../../components/common/LoadingSkeleton';
import ErrorState from '../../components/common/ErrorState';
import EmptyState from '../../components/common/EmptyState';
import { useAuth } from '../../context/AuthContext';

export default function CoursesPage() {
  const { activeContext } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [search, setSearch] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadCourses = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getCourses();
      if (data && data.length > 0) {
        setCourses(data);
      } else {
        // Fallback demo courses
        setCourses([
          {
            id: 'c-thermo-101',
            slug: 'thermodynamics',
            title: 'Foundations of Engineering Thermodynamics',
            description:
              'Master the first and second laws of thermodynamics, entropy, enthalpy, and reversible heat engine cycles with Socratic guidance.',
            subject: 'Physics',
            organization_id: activeContext.organizationId,
            created_at: new Date().toISOString(),
            versions: [
              {
                id: 'cv-1',
                course_id: 'c-thermo-101',
                version_number: 1,
                title: 'v1.0 Canonical',
                is_published: true,
              },
            ],
          },
          {
            id: 'c-dsa-201',
            slug: 'data-structures',
            title: 'Data Structures and Algorithmic Analysis',
            description:
              'Explore trees, balanced graphs, asymptotic complexity, and dynamic programming through interactive coding challenges.',
            subject: 'Computer Science',
            organization_id: activeContext.organizationId,
            created_at: new Date().toISOString(),
            versions: [
              {
                id: 'cv-2',
                course_id: 'c-dsa-201',
                version_number: 2,
                title: 'v2.0 Rigorous',
                is_published: true,
              },
            ],
          },
        ]);
      }
    } catch (err: unknown) {
      setError((err as Error).message || 'Failed to load courses.');
    } finally {
      setIsLoading(false);
    }
  }, [activeContext.organizationId]);

  useEffect(() => {
    loadCourses();
  }, [loadCourses]);

  const safeCourses = Array.isArray(courses) ? courses : [];
  const subjects = ['all', ...Array.from(new Set(safeCourses.map((c) => c.subject).filter(Boolean)))];

  const filteredCourses = safeCourses.filter((c) => {
    const matchesSearch =
      (c.title || '').toLowerCase().includes(search.toLowerCase()) ||
      (c.description || '').toLowerCase().includes(search.toLowerCase());
    const matchesSubject = selectedSubject === 'all' || c.subject === selectedSubject;
    return matchesSearch && matchesSubject;
  });

  return (
    <div className="space-y-6" data-testid="courses-catalog-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black text-slate-900 sm:text-3xl">Course Catalog</h1>
        <p className="mt-1 text-sm text-slate-500">
          Course-independent curricula with approved pinned versions and verified mastery models.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search courses or keywords..."
            className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-10 pr-4 text-xs text-slate-800 focus:border-sky-500 focus:bg-white focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-600">Subject:</span>
          <select
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 focus:border-sky-500 focus:outline-none"
          >
            {subjects.map((sub) => (
              <option key={sub} value={sub}>
                {sub.charAt(0).toUpperCase() + sub.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Grid */}
      {isLoading ? (
        <LoadingSkeleton count={4} />
      ) : error ? (
        <ErrorState message={error} onRetry={loadCourses} />
      ) : filteredCourses.length === 0 ? (
        <EmptyState
          title="No courses match your query"
          description="Try clearing your search filters or browse other subjects."
          actionLabel="Clear Filters"
          onAction={() => {
            setSearch('');
            setSelectedSubject('all');
          }}
        />
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filteredCourses.map((c) => (
            <CourseCard key={c.id} course={c} isEnrolled={false} />
          ))}
        </div>
      )}
    </div>
  );
}
