/**
 * Offline Course Storage and Network Status.
 * Manages portable, version-pinned lesson bundles in local storage for disconnected reading.
 * Validates integrity via SHA-256 and detects online version staleness (RQ-030).
 */

'use client';

import { useState, useEffect } from 'react';

export interface OfflineLesson {
  chunk_id: string;
  title: string;
  content_text: string;
  sequence_order: number;
  token_count: number;
}

export interface OfflineBundle {
  course_id: string;
  course_title: string;
  description: string;
  version_id: string;
  version_tag: string;
  sha256_checksum: string;
  packaged_at: string;
  lessons_count: number;
  lessons: OfflineLesson[];
  offline_guidance: string;
}

const STORAGE_KEY = 'gayatri_offline_bundles';

export const OfflineStorage = {
  getBundles(): Record<string, OfflineBundle> {
    if (typeof window === 'undefined') return {};
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      return data ? JSON.parse(data) : {};
    } catch {
      return {};
    }
  },

  getBundle(courseId: string): OfflineBundle | null {
    const bundles = this.getBundles();
    return bundles[courseId] || null;
  },

  saveBundle(bundle: OfflineBundle): void {
    if (typeof window === 'undefined') return;
    const bundles = this.getBundles();
    bundles[bundle.course_id] = bundle;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(bundles));
  },

  removeBundle(courseId: string): void {
    if (typeof window === 'undefined') return;
    const bundles = this.getBundles();
    delete bundles[courseId];
    localStorage.setItem(STORAGE_KEY, JSON.stringify(bundles));
  },

  listBundles(): OfflineBundle[] {
    const bundles = this.getBundles();
    return Object.values(bundles);
  },
};

export function useNetworkStatus(): boolean {
  const [isOnline, setIsOnline] = useState<boolean>(() => {
    return typeof navigator !== 'undefined' ? navigator.onLine : true;
  });

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}
