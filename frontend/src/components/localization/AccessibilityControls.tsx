'use client';

import React from 'react';
import { useI18n } from '../../lib/i18n/I18nContext';
import { Eye } from 'lucide-react';

export default function AccessibilityControls() {
  const { contrastMode, toggleContrast, fontScale, setFontScale } = useI18n();

  return (
    <div
      className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2 py-1"
      aria-label="Accessibility options"
      data-testid="accessibility-controls"
    >
      {/* High Contrast Toggle */}
      <button
        type="button"
        onClick={toggleContrast}
        className={`flex items-center gap-1 rounded px-2 py-1 text-xs font-semibold transition ${
          contrastMode === 'high'
            ? 'bg-slate-900 text-white shadow-sm'
            : 'text-slate-600 hover:bg-slate-100'
        }`}
        title="Toggle High Contrast Mode"
        aria-pressed={contrastMode === 'high'}
        data-testid="contrast-toggle-btn"
      >
        <Eye className="h-3 w-3" />
        <span className="hidden sm:inline">Contrast</span>
      </button>

      <span className="text-slate-200">|</span>

      {/* Font Size Scaling */}
      <div className="flex items-center gap-0.5" aria-label="Font scale controls">
        <button
          type="button"
          onClick={() => setFontScale('normal')}
          className={`rounded px-1.5 py-0.5 text-xs font-medium transition ${
            fontScale === 'normal'
              ? 'bg-sky-100 text-sky-800 font-bold'
              : 'text-slate-500 hover:bg-slate-100'
          }`}
          title="Normal text size"
          data-testid="font-scale-normal"
        >
          A
        </button>
        <button
          type="button"
          onClick={() => setFontScale('large')}
          className={`rounded px-1.5 py-0.5 text-xs font-bold transition ${
            fontScale === 'large'
              ? 'bg-sky-100 text-sky-800 font-extrabold'
              : 'text-slate-500 hover:bg-slate-100'
          }`}
          title="Large text size"
          data-testid="font-scale-large"
        >
          A+
        </button>
        <button
          type="button"
          onClick={() => setFontScale('xlarge')}
          className={`rounded px-1.5 py-0.5 text-xs font-black transition ${
            fontScale === 'xlarge'
              ? 'bg-sky-100 text-sky-800 font-black'
              : 'text-slate-500 hover:bg-slate-100'
          }`}
          title="Extra large text size"
          data-testid="font-scale-xlarge"
        >
          A++
        </button>
      </div>
    </div>
  );
}
