'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import TutorChat from '../../../components/student/TutorChat';

export default function TutoringSessionPage() {
  const params = useParams();
  const sessionId = params?.sessionId as string;

  return (
    <div className="mx-auto max-w-5xl" data-testid="tutoring-session-page">
      <TutorChat
        sessionId={sessionId || 'default-session'}
        courseTitle="Interactive AI Tutoring Session"
      />
    </div>
  );
}
