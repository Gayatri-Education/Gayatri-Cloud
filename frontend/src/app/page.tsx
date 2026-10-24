'use client';

import React from 'react';
import Link from 'next/link';
import {
  GraduationCap,
  School,
  HeartHandshake,
  Building2,
  ShieldAlert,
  Sparkles,
  BookOpen,
  Award,
  ArrowRight,
  TrendingUp,
  Cpu,
  DownloadCloud,
  CreditCard,
  Lock,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const PORTALS = [
  {
    id: 'student',
    title: 'Student Learner Portal',
    role: 'STUDENT',
    icon: GraduationCap,
    href: '/dashboard',
    color: 'from-sky-500 to-blue-600',
    lightColor: 'bg-sky-50 border-sky-200 text-sky-900',
    description:
      'Personalized adaptive tutoring, Socratic dialogue, syllabus roadmap, and practice assessments.',
    features: ['Socratic AI Tutor', 'Course Syllabus & RAG', 'Timed Assessments', 'Offline Reader'],
    demoAccount: { email: 'ananya.roy@iitb.ac.in', pass: 'DemoStudent123!', name: 'Ananya Roy' },
  },
  {
    id: 'teacher',
    title: 'Teacher Academic Cockpit',
    role: 'TEACHER',
    icon: School,
    href: '/teacher/dashboard',
    color: 'from-indigo-500 to-indigo-700',
    lightColor: 'bg-indigo-50 border-indigo-200 text-indigo-900',
    description:
      'Class cohort rosters, 5-tier instruction cascade, rubric evaluation, and AI Copilot diagnostics.',
    features: ['Class Roster & Mastery', '5-Tier Cascade Directives', 'Copilot Class Briefing', 'Rubric Grading'],
    demoAccount: { email: 'prof.sharma@iitb.ac.in', pass: 'DemoTeacher123!', name: 'Prof. Rajesh Sharma' },
  },
  {
    id: 'parent',
    title: 'Parent & Guardian Portal',
    role: 'PARENT',
    icon: HeartHandshake,
    href: '/parent/dashboard',
    color: 'from-rose-500 to-pink-600',
    lightColor: 'bg-rose-50 border-rose-200 text-rose-900',
    description:
      'Multi-child switcher, privacy-filtered learning progress radar, and completed test history.',
    features: ['Multi-Child Switcher', 'Privacy-Filtered Progress', 'Completed Exam History', 'School Notices'],
    demoAccount: { email: 'sunita.roy@gmail.com', pass: 'DemoParent123!', name: 'Sunita Roy' },
  },
  {
    id: 'admin',
    title: 'Organization Administration',
    role: 'ORG_ADMIN',
    icon: Building2,
    href: '/admin/dashboard',
    color: 'from-amber-500 to-amber-700',
    lightColor: 'bg-amber-50 border-amber-200 text-amber-900',
    description:
      'Multi-tenant governance, member role lifecycle, domain verification, and AI cost policy.',
    features: ['Member Management', 'Domain Proofs', 'AI Cost & Model Policy', 'Billing & Invoices'],
    demoAccount: { email: 'admin@iitb.ac.in', pass: 'DemoAdmin123!', name: 'IITB Admin' },
  },
  {
    id: 'observability',
    title: 'Platform Observability & Reliability',
    role: 'SUPER_ADMIN',
    icon: ShieldAlert,
    href: '/admin/observability',
    color: 'from-purple-500 to-purple-800',
    lightColor: 'bg-purple-50 border-purple-200 text-purple-900',
    description:
      'Real-time Prometheus telemetry, emergency circuit breaker kill-switches, and disaster recovery.',
    features: ['Circuit Breakers', 'Prometheus Feed', 'Deep Health Checks', 'Disaster Recovery'],
    demoAccount: { email: 'superadmin@gayatri.internal', pass: 'DemoAdmin123!', name: 'Super Admin' },
  },
];

export default function HomePage() {
  const { user, activeContext, login } = useAuth();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const displayUser = mounted ? user : null;

  const handleQuickSwitch = async (email: string, pass: string, href: string) => {
    try {
      await login(email, pass);
      window.location.href = href;
    } catch {
      window.location.href = href;
    }
  };

  return (
    <div className="space-y-12 pb-12">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-sky-950 to-slate-900 p-8 sm:p-12 text-white shadow-xl">
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 rounded-full bg-sky-500/20 px-3.5 py-1 text-xs font-semibold text-sky-300 border border-sky-400/30">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Course-Independent Adaptive Education Platform</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">
            Gayatri Cloud
          </h1>

          <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-2xl">
            Cloud-first adaptive tutoring system for independent learners and institutions.
            Server-side AI orchestration, course-independent RAG, immutable syllabi, and strict multi-tenant privacy.
          </p>

          {/* User Session Status */}
          <div className="pt-2 flex flex-wrap items-center gap-3">
            {displayUser ? (
              <div className="inline-flex items-center gap-2.5 rounded-xl bg-white/10 px-4 py-2 text-xs backdrop-blur border border-white/10">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>
                  Signed in as <strong>{displayUser.full_name || displayUser.email}</strong> ({activeContext.role})
                </span>
                <span className="text-slate-400">•</span>
                <span className="text-sky-300">{activeContext.organizationName}</span>
              </div>
            ) : (
              <div className="inline-flex items-center gap-2 rounded-xl bg-amber-500/20 px-4 py-2 text-xs text-amber-200 border border-amber-400/30">
                <span>Not signed in. Use the 1-click switcher below to launch any role instantly.</span>
              </div>
            )}
          </div>
        </div>

        {/* Decorative background glow */}
        <div className="absolute right-0 top-0 -mt-16 -mr-16 h-80 w-80 rounded-full bg-sky-500/20 blur-3xl pointer-events-none" />
      </section>

      {/* 1-Click Role Switcher Bar */}
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-amber-500" />
              <span>1-Click Demo Role Launcher</span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Select any role to instantly log in and access that portal directly:
            </p>
          </div>
          <Link
            href="/login"
            className="text-xs font-semibold text-sky-600 hover:text-sky-700 flex items-center gap-1 self-start sm:self-auto"
          >
            <span>Custom Login</span>
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {PORTALS.map((portal) => {
            const Icon = portal.icon;
            const isCurrent = activeContext.role === portal.role && user;
            return (
              <button
                key={portal.id}
                onClick={() =>
                  handleQuickSwitch(
                    portal.demoAccount.email,
                    portal.demoAccount.pass,
                    portal.href
                  )
                }
                className={`flex flex-col items-start p-3.5 rounded-xl border text-left transition hover:shadow-md ${
                  isCurrent
                    ? 'border-sky-500 bg-sky-50/70 shadow-sm ring-1 ring-sky-500'
                    : 'border-slate-200 bg-slate-50/60 hover:bg-white hover:border-slate-300'
                }`}
              >
                <div className="flex items-center justify-between w-full mb-2">
                  <div
                    className={`h-7 w-7 rounded-lg bg-gradient-to-br ${portal.color} text-white flex items-center justify-center`}
                  >
                    <Icon className="h-4 w-4" />
                  </div>
                  {isCurrent && (
                    <span className="text-[10px] font-bold text-sky-700 bg-sky-100 px-1.5 py-0.5 rounded-full">
                      ACTIVE
                    </span>
                  )}
                </div>
                <div className="text-xs font-bold text-slate-900">{portal.role}</div>
                <div className="text-[11px] text-slate-500 truncate w-full mt-0.5">
                  {portal.demoAccount.name}
                </div>
              </button>
            );
          })}
        </div>
      </section>

      {/* Main Portals Grid */}
      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-black text-slate-900">Explore Portals & Capabilities</h2>
          <p className="text-xs text-slate-500 mt-1">
            Choose a dedicated portal or navigate directly to specific learning tools.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {PORTALS.map((portal) => {
            const Icon = portal.icon;
            return (
              <div
                key={portal.id}
                className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md transition"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div
                      className={`h-11 w-11 rounded-xl bg-gradient-to-br ${portal.color} text-white flex items-center justify-center shadow-sm`}
                    >
                      <Icon className="h-6 w-6" />
                    </div>
                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${portal.lightColor}`}
                    >
                      {portal.role}
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-slate-900">{portal.title}</h3>
                  <p className="mt-2 text-xs text-slate-600 leading-relaxed">
                    {portal.description}
                  </p>

                  <div className="mt-4 pt-4 border-t border-slate-100">
                    <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      Key Capabilities:
                    </div>
                    <ul className="space-y-1.5 text-xs text-slate-700">
                      {portal.features.map((feat, i) => (
                        <li key={i} className="flex items-center gap-2">
                          <span className="h-1.5 w-1.5 rounded-full bg-sky-500 shrink-0" />
                          <span>{feat}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-100 flex items-center gap-2">
                  <button
                    onClick={() =>
                      handleQuickSwitch(
                        portal.demoAccount.email,
                        portal.demoAccount.pass,
                        portal.href
                      )
                    }
                    className="flex-1 flex items-center justify-center gap-1.5 rounded-xl bg-slate-900 py-2.5 px-4 text-xs font-semibold text-white hover:bg-sky-600 transition shadow-sm"
                  >
                    <span>Launch Portal</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Direct Feature Shortcuts */}
      <section className="rounded-2xl border border-slate-200 bg-slate-50/60 p-6">
        <h3 className="text-sm font-bold text-slate-900 mb-3">Quick Navigation Shortcuts</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <Link
            href="/courses"
            className="flex items-center gap-2 p-3 rounded-xl bg-white border border-slate-200 hover:border-sky-300 hover:shadow-sm transition font-medium text-slate-700"
          >
            <BookOpen className="h-4 w-4 text-sky-600" />
            <span>Course Catalog</span>
          </Link>
          <Link
            href="/tutoring"
            className="flex items-center gap-2 p-3 rounded-xl bg-white border border-slate-200 hover:border-sky-300 hover:shadow-sm transition font-medium text-slate-700"
          >
            <Sparkles className="h-4 w-4 text-purple-600" />
            <span>Socratic AI Tutor</span>
          </Link>
          <Link
            href="/assessments"
            className="flex items-center gap-2 p-3 rounded-xl bg-white border border-slate-200 hover:border-sky-300 hover:shadow-sm transition font-medium text-slate-700"
          >
            <Award className="h-4 w-4 text-emerald-600" />
            <span>Assessments</span>
          </Link>
          <Link
            href="/offline"
            className="flex items-center gap-2 p-3 rounded-xl bg-white border border-slate-200 hover:border-sky-300 hover:shadow-sm transition font-medium text-slate-700"
          >
            <DownloadCloud className="h-4 w-4 text-indigo-600" />
            <span>Offline Reader</span>
          </Link>
        </div>
      </section>
    </div>
  );
}
