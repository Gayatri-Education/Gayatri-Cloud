'use client';

import React from 'react';
import Link from 'next/link';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export default function EmptyState({
  title,
  description,
  actionLabel,
  actionHref,
  onAction,
  icon,
}: EmptyStateProps) {
  return (
    <div
      className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50/50 p-10 text-center"
      data-testid="empty-state-box"
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400 mb-4">
        {icon || <Inbox className="h-6 w-6" />}
      </div>
      <h3 className="text-base font-semibold text-slate-800">{title}</h3>
      <p className="mt-1.5 max-w-sm text-xs text-slate-500 leading-relaxed">{description}</p>

      {actionLabel && actionHref && (
        <div className="mt-5">
          <Link
            href={actionHref}
            className="rounded-lg bg-sky-600 px-4 py-2 text-xs font-semibold text-white hover:bg-sky-700 transition inline-block"
          >
            {actionLabel}
          </Link>
        </div>
      )}

      {actionLabel && onAction && !actionHref && (
        <div className="mt-5">
          <button
            onClick={onAction}
            className="rounded-lg bg-sky-600 px-4 py-2 text-xs font-semibold text-white hover:bg-sky-700 transition"
          >
            {actionLabel}
          </button>
        </div>
      )}
    </div>
  );
}
