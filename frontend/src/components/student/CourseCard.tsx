import React from 'react';
import Link from 'next/link';
import { BookOpen, ArrowRight, CheckCircle2 } from 'lucide-react';
import { Course } from '../../lib/types/course';

interface CourseCardProps {
  course: Course;
  isEnrolled?: boolean;
  progress?: number;
}

export default function CourseCard({ course, isEnrolled = false, progress = 0 }: CourseCardProps) {
  const activeVersion = course.active_version || (course.versions && course.versions[0]);

  return (
    <div
      className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md transition"
      data-testid={`course-card-${course.id}`}
    >
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className="inline-flex items-center gap-1.5 rounded-md bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-700">
            <BookOpen className="h-3.5 w-3.5" />
            {course.subject}
          </span>
          {activeVersion && (
            <span
              className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-mono text-slate-600"
              title="Approved course version"
            >
              v{activeVersion.version_number}.0
            </span>
          )}
        </div>

        <h3 className="text-lg font-semibold text-slate-900 line-clamp-1">{course.title}</h3>
        <p className="mt-2 text-xs text-slate-500 line-clamp-3 leading-relaxed">
          {course.description || 'Adaptive course with personalized tutoring and verified mastery tracking.'}
        </p>

        {isEnrolled && (
          <div className="mt-4">
            <div className="flex items-center justify-between text-xs text-slate-600 mb-1">
              <span>Mastery Progress</span>
              <span className="font-semibold text-sky-700">{progress}%</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
              <div
                className="h-full bg-sky-600 rounded-full transition-all duration-300"
                style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
              ></div>
            </div>
          </div>
        )}
      </div>

      <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
        {isEnrolled ? (
          <Link
            href={`/tutoring?course_id=${course.id}`}
            className="flex items-center gap-1.5 text-xs font-semibold text-sky-600 hover:text-sky-700 transition"
          >
            <span>Continue Tutoring</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        ) : (
          <Link
            href={`/courses/${course.id}`}
            className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 hover:text-slate-900 transition"
          >
            <span>View Syllabus</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        )}

        {isEnrolled && (
          <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-600">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Enrolled
          </span>
        )}
      </div>
    </div>
  );
}
