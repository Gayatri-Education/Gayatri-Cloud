'use client';

import React, { useState } from 'react';
import { OfflineBundle } from '../../lib/offline/offline-storage';
import { ChevronLeft, ChevronRight, CheckCircle, ShieldAlert } from 'lucide-react';

interface Props {
  bundle: OfflineBundle;
  onRemove?: () => void;
}

export default function OfflineCourseReader({ bundle, onRemove }: Props) {
  const [currentLessonIndex, setCurrentLessonIndex] = useState(0);

  if (!bundle.lessons || bundle.lessons.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 text-center text-slate-500">
        No offline lessons found in this bundle.
      </div>
    );
  }

  const currentLesson = bundle.lessons[currentLessonIndex] || bundle.lessons[0];

  return (
    <div
      className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-6"
      data-testid={`offline-reader-${bundle.course_id}`}
    >
      {/* Header Info */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900">{bundle.course_title}</h2>
            <span className="rounded bg-sky-100 px-2 py-0.5 text-xs font-semibold text-sky-800">
              {bundle.version_tag}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">{bundle.description}</p>
        </div>

        <div className="flex items-center gap-2">
          {onRemove && (
            <button
              onClick={onRemove}
              className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-700 hover:bg-rose-100 transition"
              data-testid="remove-cached-bundle-btn"
            >
              Remove Cached
            </button>
          )}
        </div>
      </div>

      {/* Offline Guidance Callout */}
      <div className="flex items-start gap-2.5 rounded-xl border border-amber-200 bg-amber-50/70 p-3 text-xs text-amber-900">
        <ShieldAlert className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold">Offline Reading Mode: </span>
          <span>{bundle.offline_guidance}</span>
        </div>
      </div>

      {/* Lesson Content Area */}
      <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Section {currentLessonIndex + 1} of {bundle.lessons.length}
          </span>
          <span className="text-xs text-slate-400">
            ~{currentLesson.token_count} tokens
          </span>
        </div>

        <h3 className="text-lg font-bold text-slate-900">{currentLesson.title}</h3>

        <div
          className="prose prose-slate max-w-none text-slate-800 whitespace-pre-wrap leading-relaxed"
          data-testid="lesson-content-text"
        >
          {currentLesson.content_text}
        </div>
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center justify-between border-t border-slate-100 pt-4">
        <button
          type="button"
          onClick={() => setCurrentLessonIndex((prev) => Math.max(0, prev - 1))}
          disabled={currentLessonIndex === 0}
          className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
          data-testid="prev-lesson-btn"
        >
          <ChevronLeft className="h-4 w-4" />
          <span>Previous Section</span>
        </button>

        <div className="flex items-center gap-1">
          {bundle.lessons.map((_, idx) => (
            <button
              key={idx}
              onClick={() => setCurrentLessonIndex(idx)}
              className={`h-2.5 w-2.5 rounded-full transition ${
                idx === currentLessonIndex
                  ? 'bg-sky-600 w-5'
                  : 'bg-slate-200 hover:bg-slate-300'
              }`}
              title={`Go to section ${idx + 1}`}
              aria-label={`Go to section ${idx + 1}`}
            />
          ))}
        </div>

        <button
          type="button"
          onClick={() =>
            setCurrentLessonIndex((prev) => Math.min(bundle.lessons.length - 1, prev + 1))
          }
          disabled={currentLessonIndex === bundle.lessons.length - 1}
          className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
          data-testid="next-lesson-btn"
        >
          <span>Next Section</span>
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>

      {/* Checksum Badge */}
      <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
        <CheckCircle className="h-3.5 w-3.5 text-emerald-500" />
        <span>SHA-256 Verified Package:</span>
        <code className="rounded bg-slate-100 px-1 py-0.5 font-mono text-[10px]">
          {bundle.sha256_checksum.slice(0, 16)}...
        </code>
      </div>
    </div>
  );
}
