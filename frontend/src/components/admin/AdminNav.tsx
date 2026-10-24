'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Users, Cpu, FileText, Settings } from 'lucide-react';

const ADMIN_LINKS = [
  { href: '/admin/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/admin/members', label: 'Members & Roles', icon: Users },
  { href: '/admin/ai-policy', label: 'AI Policy', icon: Cpu },
  { href: '/admin/audit', label: 'Audit Trail', icon: FileText },
  { href: '/admin/settings', label: 'Tenant Settings', icon: Settings },
];

export default function AdminNav() {
  const pathname = usePathname();

  return (
    <nav className="flex space-x-1 border-b border-slate-200 pb-2 mb-6 overflow-x-auto" data-testid="admin-subnav">
      {ADMIN_LINKS.map((link) => {
        const Icon = link.icon;
        const isActive = pathname === link.href;
        return (
          <Link
            key={link.href}
            href={link.href}
            className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition whitespace-nowrap ${
              isActive
                ? 'bg-slate-900 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
            data-testid={`admin-nav-${link.label.toLowerCase().replace(/\s+/g, '-')}`}
          >
            <Icon className="h-4 w-4" />
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
