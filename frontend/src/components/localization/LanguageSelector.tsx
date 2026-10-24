'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useI18n } from '../../lib/i18n/I18nContext';
import { Globe, ChevronDown, Check } from 'lucide-react';

export default function LanguageSelector() {
  const { locale, setLocale, supportedLanguages, t } = useI18n();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const currentLang = supportedLanguages.find((l) => l.code === locale) || supportedLanguages[0];

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div ref={containerRef} className="relative inline-block text-left" data-testid="language-selector">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 transition shadow-sm"
        aria-expanded={isOpen}
        aria-haspopup="true"
        aria-label="Select language"
        data-testid="language-selector-trigger"
      >
        <Globe className="h-3.5 w-3.5 text-sky-600" />
        <span className="font-semibold text-slate-900">{currentLang.nativeLabel}</span>
        <span className="text-[10px] text-slate-400 font-mono">({currentLang.code.toUpperCase()})</span>
        <ChevronDown className="h-3 w-3 text-slate-400" />
      </button>

      {isOpen && (
        <div
          className="absolute right-0 mt-1.5 w-48 rounded-xl border border-slate-200 bg-white p-1.5 shadow-xl z-50 animate-in fade-in slide-in-from-top-1"
          role="menu"
          data-testid="language-menu"
        >
          <div className="px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100 mb-1">
            {t('ui_language')}
          </div>
          <div className="max-h-64 overflow-y-auto space-y-0.5">
            {supportedLanguages.map((lang) => {
              const isSelected = locale === lang.code;
              return (
                <button
                  key={lang.code}
                  type="button"
                  onClick={() => {
                    setLocale(lang.code);
                    setIsOpen(false);
                  }}
                  className={`w-full flex items-center justify-between rounded-lg px-2.5 py-2 text-xs text-left transition ${
                    isSelected
                      ? 'bg-sky-50 text-sky-900 font-bold'
                      : 'text-slate-700 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                  role="menuitem"
                  data-testid={`lang-option-${lang.code}`}
                >
                  <div className="flex flex-col">
                    <span className="font-medium">{lang.nativeLabel}</span>
                    <span className="text-[10px] text-slate-400">{lang.englishName}</span>
                  </div>
                  {isSelected && <Check className="h-3.5 w-3.5 text-sky-600 font-bold shrink-0" />}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
