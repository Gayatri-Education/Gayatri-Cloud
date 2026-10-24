'use client';

import React, { useState } from 'react';
import { useI18n } from '../../lib/i18n/I18nContext';
import { Globe, ChevronDown } from 'lucide-react';

export default function LanguageSelector() {
  const { locale, setLocale, supportedLanguages } = useI18n();
  const [isOpen, setIsOpen] = useState(false);

  const currentLang = supportedLanguages.find((l) => l.code === locale) || supportedLanguages[0];

  return (
    <div className="relative inline-block text-left" data-testid="language-selector">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 transition"
        aria-expanded={isOpen}
        aria-haspopup="true"
        aria-label="Select language"
        data-testid="language-selector-trigger"
      >
        <Globe className="h-3.5 w-3.5 text-slate-500" />
        <span className="font-semibold">{currentLang.nativeLabel}</span>
        <span className="text-[10px] text-slate-400">({currentLang.code.toUpperCase()})</span>
        <ChevronDown className="h-3 w-3 text-slate-400" />
      </button>

      {isOpen && (
        <div
          className="absolute right-0 mt-1.5 w-44 rounded-xl border border-slate-200 bg-white p-1.5 shadow-lg z-50"
          role="menu"
          data-testid="language-menu"
        >
          <div className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            UI Language
          </div>
          {supportedLanguages.map((lang) => (
            <button
              key={lang.code}
              type="button"
              onClick={() => {
                setLocale(lang.code);
                setIsOpen(false);
              }}
              className={`w-full flex items-center justify-between rounded-lg px-2 py-1.5 text-xs text-left transition ${
                locale === lang.code
                  ? 'bg-sky-50 text-sky-900 font-bold'
                  : 'text-slate-700 hover:bg-slate-50'
              }`}
              role="menuitem"
              data-testid={`lang-option-${lang.code}`}
            >
              <div>
                <span>{lang.nativeLabel}</span>
                <span className="ml-1 text-[10px] text-slate-400">{lang.englishName}</span>
              </div>
              {locale === lang.code && <span className="text-sky-600 font-bold">✓</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
