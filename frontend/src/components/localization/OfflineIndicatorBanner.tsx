'use client';

import React from 'react';
import Link from 'next/link';
import { useNetworkStatus } from '../../lib/offline/offline-storage';
import { useI18n } from '../../lib/i18n/I18nContext';
import { WifiOff, BookOpen } from 'lucide-react';

export default function OfflineIndicatorBanner() {
  const isOnline = useNetworkStatus();
  const { t } = useI18n();

  if (isOnline) {
    return null;
  }

  return (
    <div
      role="status"
      aria-live="polite"
      className="bg-amber-500 text-amber-950 px-4 py-2 text-xs font-medium border-b border-amber-600/20 shadow-sm"
      data-testid="offline-indicator-banner"
    >
      <div className="mx-auto max-w-7xl flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <WifiOff className="h-4 w-4 text-amber-900 shrink-0" />
          <span>{t('offline_reading_banner')}</span>
        </div>
        <Link
          href="/offline"
          className="inline-flex items-center gap-1 font-bold underline hover:text-black transition"
          data-testid="banner-offline-library-link"
        >
          <BookOpen className="h-3.5 w-3.5" />
          <span>{t('offline_library')}</span>
        </Link>
      </div>
    </div>
  );
}
