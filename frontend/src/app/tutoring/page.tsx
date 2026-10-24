'use client';

import React, { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import TutorChat from '../../components/student/TutorChat';

function TutoringContent() {
  const searchParams = useSearchParams();
  const courseId = searchParams.get('course_id') || 'c-thermo-101';
  const concept = searchParams.get('concept') || undefined;

  const sessionId = `session-${courseId}-${concept ? encodeURIComponent(concept) : 'general'}`;
  const courseTitle = concept
    ? `Concept Review: ${concept}`
    : 'Foundations of Engineering Thermodynamics';

  return (
    <div className="mx-auto max-w-5xl" data-testid="tutoring-page">
      <TutorChat sessionId={sessionId} courseTitle={courseTitle} />
    </div>
  );
}

export default function TutoringPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-slate-500">Loading AI Tutor...</div>}>
      <TutoringContent />
    </Suspense>
  );
}
