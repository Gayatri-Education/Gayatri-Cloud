'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  GraduationCap,
  Lock,
  Mail,
  Shield,
  ArrowRight,
  UserCheck,
  Building,
  School,
  HeartHandshake,
  AlertCircle,
  Loader2,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface DemoAccount {
  role: string;
  name: string;
  email: string;
  pass: string;
  icon: React.ElementType;
  badgeColor: string;
  targetUrl: string;
  description: string;
}

const DEMO_ACCOUNTS: DemoAccount[] = [
  {
    role: 'STUDENT',
    name: 'Ananya Roy',
    email: 'ananya.roy@iitb.ac.in',
    pass: 'DemoStudent123!',
    icon: GraduationCap,
    badgeColor: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    targetUrl: '/dashboard',
    description: 'Learner dashboard, adaptive Socratic tutoring, assessments, and offline bundles.',
  },
  {
    role: 'TEACHER',
    name: 'Prof. Rajesh Sharma',
    email: 'prof.sharma@iitb.ac.in',
    pass: 'DemoTeacher123!',
    icon: School,
    badgeColor: 'bg-indigo-100 text-indigo-800 border-indigo-200',
    targetUrl: '/teacher/dashboard',
    description: 'Cohort rosters, 5-tier instruction cascade, rubric evaluation, and AI Copilot.',
  },
  {
    role: 'PARENT',
    name: 'Sunita Roy',
    email: 'sunita.roy@gmail.com',
    pass: 'DemoParent123!',
    icon: HeartHandshake,
    badgeColor: 'bg-pink-100 text-pink-800 border-pink-200',
    targetUrl: '/parent/dashboard',
    description: 'Multi-child switcher, privacy-filtered mastery radar, and completed tests.',
  },
  {
    role: 'ORG_ADMIN',
    name: 'IITB Academy Admin',
    email: 'admin@iitb.ac.in',
    pass: 'DemoAdmin123!',
    icon: Building,
    badgeColor: 'bg-amber-100 text-amber-800 border-amber-200',
    targetUrl: '/admin/dashboard',
    description: 'Institutional management, membership lifecycle, domain proofs, and billing.',
  },
  {
    role: 'SUPER_ADMIN',
    name: 'Gayatri Super Admin',
    email: 'superadmin@gayatri.internal',
    pass: 'DemoAdmin123!',
    icon: Shield,
    badgeColor: 'bg-purple-100 text-purple-800 border-purple-200',
    targetUrl: '/admin/observability',
    description: 'Platform circuit breakers, Prometheus telemetry, and disaster recovery drills.',
  },
];

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (loginEmail: string, loginPass: string, redirectUrl: string = '/dashboard') => {
    setIsLoading(true);
    setError(null);
    try {
      await login(loginEmail, loginPass);
      router.push(redirectUrl);
    } catch (err: unknown) {
      setError((err as Error).message || 'Invalid email or password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }
    // Determine default redirect based on email if recognized
    const matchedDemo = DEMO_ACCOUNTS.find((d) => d.email.toLowerCase() === email.toLowerCase());
    const target = matchedDemo ? matchedDemo.targetUrl : '/dashboard';
    handleLogin(email, password, target);
  };

  return (
    <div className="min-h-[85vh] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-sky-600 text-white shadow-md mb-4">
          <GraduationCap className="h-8 w-8" />
        </div>
        <h2 className="text-3xl font-black tracking-tight text-slate-900">
          Sign In to Gayatri Cloud
        </h2>
        <p className="mt-2 text-sm text-slate-600">
          Adaptive education platform with zero server-side secret exposure
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-4xl">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Manual Sign-In Form */}
          <div className="lg:col-span-5 bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
            <h3 className="text-lg font-bold text-slate-900 mb-1">Account Credentials</h3>
            <p className="text-xs text-slate-500 mb-6">Enter your registered credentials below</p>

            {error && (
              <div className="mb-5 flex items-start gap-2.5 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5 text-rose-600" />
                <span className="leading-relaxed">{error}</span>
              </div>
            )}

            <form onSubmit={handleFormSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Email Address
                </label>
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
                    <Mail className="h-4 w-4" />
                  </div>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    placeholder="user@example.com"
                    className="block w-full rounded-xl border border-slate-300 py-2.5 pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
                    <Lock className="h-4 w-4" />
                  </div>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    placeholder="••••••••••••"
                    className="block w-full rounded-xl border border-slate-300 py-2.5 pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 transition"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-sky-600 py-2.5 px-4 text-sm font-semibold text-white shadow-sm hover:bg-sky-700 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-2 disabled:opacity-50 transition"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Verifying Credentials...</span>
                  </>
                ) : (
                  <>
                    <span>Sign In</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </form>
          </div>

          {/* 1-Click Demo Accounts Selector */}
          <div className="lg:col-span-7 bg-slate-50/80 p-8 rounded-2xl border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-amber-500" />
                  <h3 className="text-lg font-bold text-slate-900">1-Click Demo Switcher</h3>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  Pre-configured accounts seeded in your local SQLite store (<code className="text-slate-700 font-mono">local_dev.db</code>)
                </p>
              </div>
              <span className="rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 border border-emerald-200">
                LOCAL STACK
              </span>
            </div>

            <div className="space-y-3">
              {DEMO_ACCOUNTS.map((acc) => {
                const IconComponent = acc.icon;
                return (
                  <button
                    key={acc.email}
                    onClick={() => {
                      setEmail(acc.email);
                      setPassword(acc.pass);
                      handleLogin(acc.email, acc.pass, acc.targetUrl);
                    }}
                    disabled={isLoading}
                    className="w-full text-left p-3.5 rounded-xl bg-white border border-slate-200 hover:border-sky-400 hover:shadow-sm transition flex items-start justify-between gap-3 group"
                  >
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-lg bg-slate-100 text-slate-700 group-hover:bg-sky-50 group-hover:text-sky-600 transition shrink-0 mt-0.5">
                        <IconComponent className="h-4 w-4" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-slate-900">{acc.name}</span>
                          <span
                            className={`rounded-full px-2 py-0.5 text-[10px] font-semibold border ${acc.badgeColor}`}
                          >
                            {acc.role}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 font-mono mt-0.5">{acc.email}</p>
                        <p className="text-[11px] text-slate-600 mt-1">{acc.description}</p>
                      </div>
                    </div>
                    <div className="shrink-0 flex items-center text-xs font-semibold text-sky-600 group-hover:translate-x-0.5 transition mt-2">
                      <span>Log in</span>
                      <ArrowRight className="h-3.5 w-3.5 ml-1" />
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="mt-4 pt-3 border-t border-slate-200 text-center">
              <span className="text-[11px] text-slate-400">
                Default password for all demo accounts: <code className="font-mono text-slate-600 font-semibold">DemoStudent123!</code> / <code className="font-mono text-slate-600 font-semibold">DemoAdmin123!</code>
              </span>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
