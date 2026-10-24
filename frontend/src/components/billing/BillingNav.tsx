'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { CreditCard, Sparkles, Building2, Receipt } from 'lucide-react';

const BILLING_LINKS = [
  { href: '/billing', label: 'Overview', icon: CreditCard },
  { href: '/billing/plans', label: 'Subscription Plans', icon: Sparkles },
  { href: '/billing/fees', label: 'Institution Fees', icon: Building2 },
  { href: '/billing/invoices', label: 'Invoices & Receipts', icon: Receipt },
];

export default function BillingNav() {
  const pathname = usePathname();

  return (
    <nav className="flex space-x-1 border-b border-slate-200 pb-2 mb-6 overflow-x-auto" data-testid="billing-subnav">
      {BILLING_LINKS.map((link) => {
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
            data-testid={`billing-nav-${link.label.toLowerCase().replace(/\s+/g, '-')}`}
          >
            <Icon className="h-4 w-4" />
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
