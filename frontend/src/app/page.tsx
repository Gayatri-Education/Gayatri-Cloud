import React from 'react';

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 text-center">
      <div className="max-w-2xl rounded-2xl bg-white p-10 shadow-lg border border-slate-200">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-sky-50 text-sky-700 border border-sky-200 mb-6">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          Gayatri Cloud v0.1.0 • P01 Baseline
        </div>
        <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl">
          Gayatri Cloud
        </h1>
        <p className="mt-4 text-lg text-slate-600 leading-relaxed">
          Course-Independent Adaptive AI Tutoring Platform for independent learners, schools, and educational organizations.
        </p>

        <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-3 text-left">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
            <h3 className="font-semibold text-slate-900 text-sm">Learners</h3>
            <p className="text-xs text-slate-500 mt-1">Adaptive mastery, Socratic tutoring, concept maps.</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
            <h3 className="font-semibold text-slate-900 text-sm">Teachers</h3>
            <p className="text-xs text-slate-500 mt-1">5-tier instruction cascade, class copilot, diagnostics.</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
            <h3 className="font-semibold text-slate-900 text-sm">Institutions</h3>
            <p className="text-xs text-slate-500 mt-1">Multi-tenant isolation, course RAG, curriculum control.</p>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
          <span>Backend API: FastAPI (Python 3.12)</span>
          <span>Database: PostgreSQL + pgvector</span>
        </div>
      </div>
    </main>
  );
}
