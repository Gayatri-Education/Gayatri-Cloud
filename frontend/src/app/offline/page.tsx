'use client';

import React, { useState, useEffect } from 'react';
import { OfflineStorage, OfflineBundle, useNetworkStatus } from '../../lib/offline/offline-storage';
import OfflineCourseReader from '../../components/localization/OfflineCourseReader';
import { BookOpen, RefreshCw, WifiOff, Wifi, AlertTriangle } from 'lucide-react';
import { useI18n } from '../../lib/i18n/I18nContext';

export default function OfflineLibraryPage() {
  const isOnline = useNetworkStatus();
  const { t } = useI18n();
  const [bundles, setBundles] = useState<OfflineBundle[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<string | null>(null);
  const [stalenessMap, setStalenessMap] = useState<Record<string, boolean>>({});
  const [checkingStaleness, setCheckingStaleness] = useState(false);

  useEffect(() => {
    const list = OfflineStorage.listBundles();
    setBundles(list);
    if (list.length > 0 && !selectedCourseId) {
      setSelectedCourseId(list[0].course_id);
    }
  }, [selectedCourseId]);

  const activeBundle = bundles.find((b) => b.course_id === selectedCourseId) || null;

  const handleRemoveBundle = (courseId: string) => {
    OfflineStorage.removeBundle(courseId);
    const updated = OfflineStorage.listBundles();
    setBundles(updated);
    if (selectedCourseId === courseId) {
      setSelectedCourseId(updated.length > 0 ? updated[0].course_id : null);
    }
  };

  const handleCheckStaleness = async () => {
    if (!isOnline || bundles.length === 0) return;
    setCheckingStaleness(true);
    const newMap: Record<string, boolean> = {};

    for (const b of bundles) {
      try {
        const res = await fetch(`/api/v1/localization/offline-bundle/${b.course_id}/staleness?local_version_tag=${b.version_tag}`);
        if (res.ok) {
          const data = await res.json();
          newMap[b.course_id] = Boolean(data.is_stale);
        }
      } catch {
        // network error / offline
      }
    }
    setStalenessMap(newMap);
    setCheckingStaleness(false);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <BookOpen className="h-6 w-6 text-sky-600" />
            <span>{t('offline_library')}</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Access downloaded course materials even when disconnected from the internet.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${
              isOnline
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'bg-amber-50 text-amber-800 border border-amber-200'
            }`}
            data-testid="network-status-badge"
          >
            {isOnline ? (
              <>
                <Wifi className="h-3.5 w-3.5 text-emerald-600" />
                <span>Connected Online</span>
              </>
            ) : (
              <>
                <WifiOff className="h-3.5 w-3.5 text-amber-600" />
                <span>Working Offline</span>
              </>
            )}
          </div>

          {isOnline && (
            <button
              onClick={handleCheckStaleness}
              disabled={checkingStaleness}
              className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
              data-testid="check-staleness-btn"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${checkingStaleness ? 'animate-spin' : ''}`} />
              <span>Check for Updates</span>
            </button>
          )}
        </div>
      </div>

      {bundles.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center space-y-3">
          <BookOpen className="mx-auto h-10 w-10 text-slate-300" />
          <h3 className="text-base font-bold text-slate-800">No Offline Courses Downloaded</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            When connected online, click &ldquo;Download for Offline Reading&rdquo; on any enrolled course to save lessons locally.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar Course List */}
          <div className="lg:col-span-1 space-y-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 px-1">
              Downloaded Courses ({bundles.length})
            </h2>
            <div className="space-y-1.5">
              {bundles.map((b) => {
                const isStale = stalenessMap[b.course_id];
                const isSelected = b.course_id === selectedCourseId;
                return (
                  <button
                    key={b.course_id}
                    onClick={() => setSelectedCourseId(b.course_id)}
                    className={`w-full text-left rounded-xl p-3 border transition ${
                      isSelected
                        ? 'border-sky-500 bg-sky-50/70 text-sky-950 font-semibold shadow-xs'
                        : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                    }`}
                    data-testid={`bundle-select-${b.course_id}`}
                  >
                    <div className="text-xs font-bold truncate">{b.course_title}</div>
                    <div className="flex items-center justify-between text-[11px] text-slate-500 mt-1">
                      <span>{b.version_tag}</span>
                      <span>{b.lessons_count} sections</span>
                    </div>
                    {isStale && (
                      <div className="flex items-center gap-1 text-[10px] font-semibold text-amber-700 mt-1.5">
                        <AlertTriangle className="h-3 w-3" />
                        <span>Update available</span>
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active Reader */}
          <div className="lg:col-span-3">
            {activeBundle ? (
              <OfflineCourseReader
                bundle={activeBundle}
                onRemove={() => handleRemoveBundle(activeBundle.course_id)}
              />
            ) : (
              <div className="rounded-xl border border-slate-200 bg-white p-6 text-center text-slate-500">
                Select a course on the left to start reading.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
