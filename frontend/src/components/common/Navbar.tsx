'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '../../context/AuthContext';
import {
  GraduationCap,
  BookOpen,
  MessageSquare,
  Award,
  TrendingUp,
  Key,
  LogOut,
  Building2,
  ChevronDown,
} from 'lucide-react';

export default function Navbar() {
  const { user, activeContext, memberships, switchOrganization, logout } = useAuth();
  const [isOrgDropdownOpen, setIsOrgDropdownOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand & Active Context */}
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-sky-600 text-white font-bold">
              <GraduationCap className="h-5 w-5" />
            </div>
            <span className="text-xl font-bold tracking-tight text-slate-900">
              Gayatri Cloud
            </span>
          </Link>

          {/* Active Context Badge with Switcher */}
          <div className="relative">
            <button
              onClick={() => setIsOrgDropdownOpen(!isOrgDropdownOpen)}
              className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 transition"
              data-testid="context-switcher-trigger"
            >
              <Building2 className="h-3.5 w-3.5 text-slate-500" />
              <span>{activeContext.organizationName}</span>
              <span className="rounded bg-sky-100 px-1.5 py-0.5 text-[10px] font-semibold text-sky-800">
                {activeContext.role}
              </span>
              <ChevronDown className="h-3 w-3 text-slate-400" />
            </button>

            {isOrgDropdownOpen && (
              <div
                className="absolute left-0 mt-2 w-64 rounded-xl border border-slate-200 bg-white p-2 shadow-lg"
                data-testid="context-dropdown-menu"
              >
                <div className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  Switch Learning Context
                </div>
                {/* Personal Option */}
                <button
                  onClick={() => {
                    switchOrganization(null);
                    setIsOrgDropdownOpen(false);
                  }}
                  className={`w-full flex items-center justify-between rounded-lg px-2.5 py-2 text-xs text-left transition ${
                    activeContext.isPersonal
                      ? 'bg-sky-50 text-sky-900 font-semibold'
                      : 'text-slate-700 hover:bg-slate-50'
                  }`}
                  data-testid="context-select-personal"
                >
                  <span>Personal Learning Space</span>
                  {activeContext.isPersonal && <span className="text-sky-600">✓</span>}
                </button>

                {/* Organization Memberships */}
                {memberships.map((m) => (
                  <button
                    key={m.organization_id}
                    onClick={() => {
                      switchOrganization(m.organization_id);
                      setIsOrgDropdownOpen(false);
                    }}
                    className={`w-full flex items-center justify-between rounded-lg px-2.5 py-2 text-xs text-left transition ${
                      activeContext.organizationId === m.organization_id
                        ? 'bg-sky-50 text-sky-900 font-semibold'
                        : 'text-slate-700 hover:bg-slate-50'
                    }`}
                    data-testid={`context-select-${m.organization_id}`}
                  >
                    <div>
                      <div>{m.organization_name}</div>
                      <span className="text-[10px] text-slate-400">{m.role}</span>
                    </div>
                    {activeContext.organizationId === m.organization_id && (
                      <span className="text-sky-600">✓</span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-1 text-sm font-medium text-slate-600">
          <Link
            href="/dashboard"
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 hover:bg-slate-50 hover:text-slate-900 transition"
          >
            Dashboard
          </Link>
          <Link
            href="/courses"
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 hover:bg-slate-50 hover:text-slate-900 transition"
          >
            <BookOpen className="h-4 w-4" />
            Courses
          </Link>
          <Link
            href="/tutoring"
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 hover:bg-slate-50 hover:text-slate-900 transition"
          >
            <MessageSquare className="h-4 w-4" />
            AI Tutor
          </Link>
          <Link
            href="/assessments"
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 hover:bg-slate-50 hover:text-slate-900 transition"
          >
            <Award className="h-4 w-4" />
            Assessments
          </Link>
          <Link
            href="/mastery"
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 hover:bg-slate-50 hover:text-slate-900 transition"
          >
            <TrendingUp className="h-4 w-4" />
            Mastery
          </Link>
          <Link
            href="/settings/ai-keys"
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 hover:bg-slate-50 hover:text-slate-900 transition"
          >
            <Key className="h-4 w-4" />
            AI Keys
          </Link>
        </nav>

        {/* User / Logout */}
        <div className="flex items-center gap-3">
          {user ? (
            <div className="flex items-center gap-3">
              <span className="text-xs font-medium text-slate-700 hidden sm:inline">
                {user.first_name} {user.last_name}
              </span>
              <button
                onClick={logout}
                className="flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 transition"
                title="Log out"
              >
                <LogOut className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="rounded-lg bg-sky-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-sky-700 transition"
            >
              Sign In
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
