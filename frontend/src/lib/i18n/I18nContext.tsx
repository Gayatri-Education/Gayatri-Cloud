'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { SUPPORTED_LANGUAGES, TRANSLATIONS, LanguageInfo } from './catalogs';
import { api } from '../api-client';

type ContrastMode = 'normal' | 'high';
type FontScale = 'normal' | 'large' | 'xlarge';

interface I18nContextValue {
  locale: string;
  setLocale: (lang: string) => void;
  supportedLanguages: LanguageInfo[];
  t: (key: string, params?: Record<string, string | number>) => string;
  contrastMode: ContrastMode;
  toggleContrast: () => void;
  fontScale: FontScale;
  setFontScale: (scale: FontScale) => void;
}

const I18nContext = createContext<I18nContextValue | undefined>(undefined);

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<string>('en');
  const [contrastMode, setContrastMode] = useState<ContrastMode>('normal');
  const [fontScale, setFontScaleState] = useState<FontScale>('normal');

  useEffect(() => {
    // Load persisted settings
    try {
      const storedLocale = localStorage.getItem('gayatri_locale');
      if (storedLocale && TRANSLATIONS[storedLocale]) {
        setLocaleState(storedLocale);
        if (typeof document !== 'undefined') {
          document.documentElement.lang = storedLocale;
        }
      }
    } catch {
      // localStorage may fail in SSR/restricted environments
    }

    try {
      const storedContrast = localStorage.getItem('gayatri_contrast') as ContrastMode;
      if (storedContrast === 'high' || storedContrast === 'normal') {
        setContrastMode(storedContrast);
        if (storedContrast === 'high' && typeof document !== 'undefined') {
          document.documentElement.classList.add('contrast-high');
        }
      }
    } catch {
      // ignore
    }

    try {
      const storedScale = localStorage.getItem('gayatri_font_scale') as FontScale;
      if (['normal', 'large', 'xlarge'].includes(storedScale)) {
        setFontScaleState(storedScale);
      }
    } catch {
      // ignore
    }
  }, []);

  const setLocale = (lang: string) => {
    const valid = TRANSLATIONS[lang] ? lang : 'en';
    setLocaleState(valid);
    try {
      localStorage.setItem('gayatri_locale', valid);
    } catch {
      // ignore
    }
    if (typeof document !== 'undefined') {
      document.documentElement.lang = valid;
    }
    // Best-effort sync with backend if user has session
    try {
      api.updateLanguagePreference(valid).catch(() => {});
    } catch {
      // ignore
    }
  };

  const toggleContrast = () => {
    const nextMode: ContrastMode = contrastMode === 'normal' ? 'high' : 'normal';
    setContrastMode(nextMode);
    localStorage.setItem('gayatri_contrast', nextMode);
    if (nextMode === 'high') {
      document.documentElement.classList.add('contrast-high');
    } else {
      document.documentElement.classList.remove('contrast-high');
    }
  };

  const setFontScale = (scale: FontScale) => {
    setFontScaleState(scale);
    localStorage.setItem('gayatri_font_scale', scale);
  };

  const t = (key: string, params?: Record<string, string | number>): string => {
    const dict = TRANSLATIONS[locale] || TRANSLATIONS.en;
    let text = dict[key] || TRANSLATIONS.en[key] || key;

    if (params) {
      for (const [pKey, pVal] of Object.entries(params)) {
        text = text.replace(new RegExp(`\\{${pKey}\\}`, 'g'), String(pVal));
      }
    }
    return text;
  };

  return (
    <I18nContext.Provider
      value={{
        locale,
        setLocale,
        supportedLanguages: SUPPORTED_LANGUAGES,
        t,
        contrastMode,
        toggleContrast,
        fontScale,
        setFontScale,
      }}
    >
      <div
        className={
          fontScale === 'xlarge'
            ? 'text-lg leading-relaxed'
            : fontScale === 'large'
            ? 'text-base leading-relaxed'
            : 'text-sm'
        }
      >
        {children}
      </div>
    </I18nContext.Provider>
  );
}

export function useI18n(): I18nContextValue {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
}
