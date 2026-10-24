'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../lib/i18n/I18nContext';
import LanguageSelector from '../localization/LanguageSelector';
import AccessibilityControls from '../localization/AccessibilityControls';
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
  Heart,
  CreditCard,
  DownloadCloud,
  Shield,
  Menu,
  X,
  School,
  UserCheck,
  ShieldAlert,
  Users,
  Settings,
} from 'lucide-react';

export default function Navbar() {
  const { user, activeContext, memberships, switchOrganization, logout } = useAuth();
  const { t } = useI18n();
  const [mounted, setMounted] = useState(false);
  const [isOrgDropdownOpen, setIsOrgDropdownOpen] = useState(false);
  const [isMoreDropdownOpen, setIsMoreDropdownOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const role = mounted ? activeContext.role : 'STUDENT';
  const displayUser = mounted ? user : null;

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        
        {/* Brand Logo & Context Switcher */}
        <div className="flex items-center gap-4">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-sky-500 to-blue-600 text-white shadow-sm font-bold">
              <GraduationCap className="h-5 w-5" />
            </div>
            <span className="text-lg font-black tracking-tight text-slate-900 hidden sm:inline">
              Gayatri Cloud
            </span>
          </Link>

          {/* Active Context Badge with Switcher */}
          <div className="relative">
            <button
              onClick={() => {
                setIsOrgDropdownOpen(!isOrgDropdownOpen);
                setIsMoreDropdownOpen(false);
              }}
              className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 transition"
              data-testid="context-switcher-trigger"
            >
              <Building2 className="h-3.5 w-3.5 text-slate-500" />
              <span className="max-w-[130px] truncate">{activeContext.organizationName}</span>
              <span className="rounded-md bg-sky-100 px-1.5 py-0.5 text-[10px] font-bold text-sky-800 uppercase">
                {activeContext.role}
              </span>
              <ChevronDown className="h-3 w-3 text-slate-400" />
            </button>

            {isOrgDropdownOpen && (
              <div
                className="absolute left-0 mt-2 w-72 rounded-2xl border border-slate-200 bg-white p-2 shadow-xl z-50 animate-in fade-in slide-in-from-top-1"
                data-testid="context-dropdown-menu"
              >
                <div className="px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  Switch Learning Context
                </div>
                {/* Personal Option */}
                <button
                  onClick={() => {
                    switchOrganization(null);
                    setIsOrgDropdownOpen(false);
                  }}
                  className={`w-full flex items-center justify-between rounded-xl px-3 py-2 text-xs text-left transition ${
                    activeContext.isPersonal
                      ? 'bg-sky-50 text-sky-900 font-semibold'
                      : 'text-slate-700 hover:bg-slate-50'
                  }`}
                  data-testid="context-select-personal"
                >
                  <div className="flex items-center gap-2">
                    <GraduationCap className="h-4 w-4 text-sky-600" />
                    <span>Personal Learning Space</span>
                  </div>
                  {activeContext.isPersonal && <span className="text-sky-600 font-bold">✓</span>}
                </button>

                {/* Organization Memberships */}
                {memberships.map((m) => (
                  <button
                    key={m.organization_id}
                    onClick={() => {
                      switchOrganization(m.organization_id);
                      setIsOrgDropdownOpen(false);
                    }}
                    className={`w-full flex items-center justify-between rounded-xl px-3 py-2 text-xs text-left transition ${
                      activeContext.organizationId === m.organization_id
                        ? 'bg-sky-50 text-sky-900 font-semibold'
                        : 'text-slate-700 hover:bg-slate-50'
                    }`}
                    data-testid={`context-select-${m.organization_id}`}
                  >
                    <div className="flex items-center gap-2">
                      <Building2 className="h-4 w-4 text-slate-500" />
                      <div>
                        <div className="font-medium text-slate-900">{m.organization_name}</div>
                        <span className="text-[10px] text-slate-500">{m.role}</span>
                      </div>
                    </div>
                    {activeContext.organizationId === m.organization_id && (
                      <span className="text-sky-600 font-bold">✓</span>
                    )}
                  </button>
                ))}

                <div className="mt-2 pt-2 border-t border-slate-100 px-2">
                  <Link
                    href="/login"
                    onClick={() => setIsOrgDropdownOpen(false)}
                    className="flex items-center gap-1.5 text-xs font-semibold text-sky-600 hover:text-sky-700"
                  >
                    <UserCheck className="h-3.5 w-3.5" />
                    <span>Switch Demo Role (1-Click)</span>
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Clean Context-Aware Navigation Links */}
        <nav className="hidden lg:flex items-center gap-1 text-xs font-semibold text-slate-600">
          {/* Universal Home link */}
          <Link
            href="/"
            className="rounded-lg px-2.5 py-1.5 hover:bg-slate-100 hover:text-slate-900 transition"
          >
            {t('portal_hub')}
          </Link>

          {/* Student Links */}
          {(role === 'STUDENT' || activeContext.isPersonal) && (
            <>
              <Link
                href="/dashboard"
                className="rounded-lg px-2.5 py-1.5 hover:bg-slate-100 hover:text-slate-900 transition"
              >
                {t('dashboard')}
              </Link>
              <Link
                href="/courses"
                className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 hover:bg-slate-100 hover:text-slate-900 transition"
              >
                <BookOpen className="h-3.5 w-3.5" />
                <span>{t('courses')}</span>
              </Link>
              <Link
                href="/tutoring"
                className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-sky-700 bg-sky-50 hover:bg-sky-100 transition"
              >
                <MessageSquare className="h-3.5 w-3.5" />
                <span>{t('tutor')}</span>
              </Link>
              <Link
                href="/assessments"
                className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 hover:bg-slate-100 hover:text-slate-900 transition"
              >
                <Award className="h-3.5 w-3.5" />
                <span>{t('assessments')}</span>
              </Link>
              <Link
                href="/mastery"
                className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 hover:bg-slate-100 hover:text-slate-900 transition"
              >
                <TrendingUp className="h-3.5 w-3.5" />
                <span>{t('mastery')}</span>
              </Link>
            </>
          )}

          {/* Teacher Links */}
          {role === 'TEACHER' && (
            <>
              <Link
                href="/teacher/dashboard"
                className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 bg-indigo-50 text-indigo-700 font-bold hover:bg-indigo-100 transition"
                data-testid="nav-teacher-portal"
              >
                <School className="h-3.5 w-3.5" />
                <span>{t('teacher_cockpit')}</span>
              </Link>
              <Link
                href="/teacher/roster"
                className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 hover:bg-slate-100 hover:text-slate-900 transition"
              >
                <Users className="h-3.5 w-3.5" />
                <span>{t('roster')}</span>
              </Link>
              <Link
                href="/teacher/instructions"
                className="rounded-lg px-2.5 py-1.5 hover:bg-slate-100 hover:text-slate-900 transition"
              >
                {t('instructions')}
              </Link>
              <Link
                href="/teacher/analytics"
                className="rounded-lg px-2.5 py-1.5 hover:bg-slate-100 hover:text-slate-900 transition"
              >
                {t('analytics')}
              </Link>
            </>
          )}

          {/* Parent Links */}
          {role === 'PARENT' && (
            <>
              <Link
                href="/parent/dashboard"
                className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 bg-rose-50 text-rose-700 font-bold hover:bg-rose-100 transition"
                data-testid="nav-parent-portal"
              >
                <Heart className="h-3.5 w-3.5" />
                <span>{t('parent_portal')}</span>
              </Link>
              <Link
                href="/parent/children"
                className="rounded-lg px-2.5 py-1.5 hover:bg-slate-100 hover:text-slate-900 transition"
              >
                {t('children')}
              </Link>
              <Link
                href="/parent/assessments"
                className="rounded-lg px-2.5 py-1.5 hover:bg-slate-100 hover:text-slate-900 transition"
              >
                {t('assessments')}
              </Link>
            </>
          )}

          {/* Admin Links */}
          {(role === 'ORG_ADMIN' || role === 'SUPER_ADMIN') && (
            <>
              <Link
                href="/admin/dashboard"
                className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 bg-amber-50 text-amber-800 font-bold hover:bg-amber-100 transition"
                data-testid="nav-admin-portal"
              >
                <Shield className="h-3.5 w-3.5" />
                <span>{t('admin_console')}</span>
              </Link>
              <Link
                href="/admin/members"
                className="rounded-lg px-2.5 py-1.5 hover:bg-slate-100 hover:text-slate-900 transition"
              >
                {t('members')}
              </Link>
              <Link
                href="/admin/ai-policy"
                className="rounded-lg px-2.5 py-1.5 hover:bg-slate-100 hover:text-slate-900 transition"
              >
                {t('ai_policy')}
              </Link>
              <Link
                href="/admin/observability"
                className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-purple-700 hover:bg-purple-50 transition"
              >
                <ShieldAlert className="h-3.5 w-3.5" />
                <span>{t('observability')}</span>
              </Link>
            </>
          )}

          {/* More Utilities Dropdown */}
          <div className="relative">
            <button
              onClick={() => {
                setIsMoreDropdownOpen(!isMoreDropdownOpen);
                setIsOrgDropdownOpen(false);
              }}
              className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 hover:bg-slate-100 hover:text-slate-900 transition"
            >
              <span>{t('more')}</span>
              <ChevronDown className="h-3 w-3 text-slate-400" />
            </button>

            {isMoreDropdownOpen && (
              <div className="absolute right-0 mt-2 w-56 rounded-2xl border border-slate-200 bg-white p-2 shadow-xl z-50 animate-in fade-in slide-in-from-top-1">
                <Link
                  href="/billing"
                  onClick={() => setIsMoreDropdownOpen(false)}
                  className="flex items-center gap-2 rounded-xl px-3 py-2 text-xs text-slate-700 hover:bg-slate-50 transition"
                >
                  <CreditCard className="h-4 w-4 text-emerald-600" />
                  <span>{t('billing')}</span>
                </Link>
                <Link
                  href="/offline"
                  onClick={() => setIsMoreDropdownOpen(false)}
                  className="flex items-center gap-2 rounded-xl px-3 py-2 text-xs text-slate-700 hover:bg-slate-50 transition"
                >
                  <DownloadCloud className="h-4 w-4 text-sky-600" />
                  <span>{t('offline_library')}</span>
                </Link>
                <Link
                  href="/settings/ai-keys"
                  onClick={() => setIsMoreDropdownOpen(false)}
                  className="flex items-center gap-2 rounded-xl px-3 py-2 text-xs text-slate-700 hover:bg-slate-50 transition"
                >
                  <Key className="h-4 w-4 text-amber-600" />
                  <span>BYOK AI Keys</span>
                </Link>
                <Link
                  href="/settings/privacy"
                  onClick={() => setIsMoreDropdownOpen(false)}
                  className="flex items-center gap-2 rounded-xl px-3 py-2 text-xs text-slate-700 hover:bg-slate-50 transition"
                >
                  <Settings className="h-4 w-4 text-purple-600" />
                  <span>{t('settings')}</span>
                </Link>
              </div>
            )}
          </div>
        </nav>

        {/* Right Tools, User Profile & Actions */}
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="flex items-center gap-1.5 sm:gap-2">
            <div className="hidden sm:block">
              <AccessibilityControls />
            </div>
            <LanguageSelector />
          </div>

          {displayUser ? (
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="hidden sm:inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
                title={t('switch_role')}
              >
                <UserCheck className="h-3.5 w-3.5 text-sky-600" />
                <span>{t('switch_role')}</span>
              </Link>

              <button
                onClick={logout}
                className="flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-rose-50 hover:text-rose-600 hover:border-rose-200 transition"
                title={t('logout')}
              >
                <LogOut className="h-3.5 w-3.5" />
                <span className="hidden md:inline">{t('logout')}</span>
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="rounded-xl bg-sky-600 px-3.5 py-1.5 text-xs font-bold text-white shadow-sm hover:bg-sky-700 transition"
            >
              {t('sign_in')}
            </Link>
          )}

          {/* Mobile Menu Toggle Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="flex lg:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100"
          >
            {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Drawer */}
      {isMobileMenuOpen && (
        <div className="lg:hidden border-t border-slate-200 bg-white px-4 pt-3 pb-6 space-y-3">
          <div className="grid grid-cols-2 gap-2 text-xs font-semibold">
            <Link
              href="/"
              onClick={() => setIsMobileMenuOpen(false)}
              className="p-2 rounded-lg bg-slate-50 text-slate-800"
            >
              {t('portal_hub')}
            </Link>
            <Link
              href="/dashboard"
              onClick={() => setIsMobileMenuOpen(false)}
              className="p-2 rounded-lg bg-slate-50 text-slate-800"
            >
              {t('dashboard')}
            </Link>
            <Link
              href="/courses"
              onClick={() => setIsMobileMenuOpen(false)}
              className="p-2 rounded-lg bg-slate-50 text-slate-800"
            >
              {t('courses')}
            </Link>
            <Link
              href="/tutoring"
              onClick={() => setIsMobileMenuOpen(false)}
              className="p-2 rounded-lg bg-sky-50 text-sky-700"
            >
              {t('tutor')}
            </Link>
            <Link
              href="/teacher/dashboard"
              onClick={() => setIsMobileMenuOpen(false)}
              className="p-2 rounded-lg bg-indigo-50 text-indigo-700"
            >
              {t('teacher_cockpit')}
            </Link>
            <Link
              href="/parent/dashboard"
              onClick={() => setIsMobileMenuOpen(false)}
              className="p-2 rounded-lg bg-rose-50 text-rose-700"
            >
              {t('parent_portal')}
            </Link>
            <Link
              href="/admin/dashboard"
              onClick={() => setIsMobileMenuOpen(false)}
              className="p-2 rounded-lg bg-amber-50 text-amber-800"
            >
              {t('admin_console')}
            </Link>
            <Link
              href="/admin/observability"
              onClick={() => setIsMobileMenuOpen(false)}
              className="p-2 rounded-lg bg-purple-50 text-purple-700"
            >
              {t('observability')}
            </Link>
          </div>

          <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
            <AccessibilityControls />
            <LanguageSelector />
          </div>
        </div>
      )}
    </header>
  );
}
