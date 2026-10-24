'use client';

import React from 'react';
import Link from 'next/link';
import { AlertCircle, RefreshCw, Home, ShieldAlert, WifiOff } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message: string;
  statusCode?: number;
  onRetry?: () => void;
  actionLabel?: string;
}

export default function ErrorState({
  title,
  message,
  statusCode,
  onRetry,
  actionLabel = 'Try Again',
}: ErrorStateProps) {
  const isNetworkError = statusCode === 0 || message.toLowerCase().includes('network');
  const isPermissionDenied = statusCode === 403 || statusCode === 401;
  const isModelUnavailable = message.toLowerCase().includes('model') || message.toLowerCase().includes('quota');

  const displayTitle =
    title ||
    (isNetworkError
      ? 'Connection Interrupted'
      : isPermissionDenied
      ? 'Access Restricted'
      : isModelUnavailable
      ? 'AI Model Unavailable'
      : 'Something Went Wrong');

  return (
    <div
      className="flex flex-col items-center justify-center rounded-2xl border border-rose-100 bg-rose-50/50 p-8 text-center"
      data-testid="error-state-card"
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-rose-100 text-rose-600 mb-4">
        {isNetworkError ? (
          <WifiOff className="h-6 w-6" />
        ) : isPermissionDenied ? (
          <ShieldAlert className="h-6 w-6" />
        ) : (
          <AlertCircle className="h-6 w-6" />
        )}
      </div>

      <h3 className="text-lg font-semibold text-slate-900">{displayTitle}</h3>
      <p className="mt-2 max-w-md text-sm text-slate-600 leading-relaxed">{message}</p>

      {statusCode ? (
        <div className="mt-2 text-[11px] font-mono text-slate-400">Error Code: {statusCode}</div>
      ) : null}

      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        {onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-xs font-semibold text-white hover:bg-sky-700 transition"
            data-testid="error-retry-button"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>{actionLabel}</span>
          </button>
        )}

        {isModelUnavailable && (
          <Link
            href="/settings/ai-keys"
            className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
          >
            <span>Manage AI Keys</span>
          </Link>
        )}

        <Link
          href="/dashboard"
          className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
        >
          <Home className="h-3.5 w-3.5" />
          <span>Return to Dashboard</span>
        </Link>
      </div>
    </div>
  );
}
