"use client";

import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";
import { Locale, TranslationKey, translations } from "@/lib/i18n";

type I18nContextValue = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: TranslationKey) => string;
};

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en");

  useEffect(() => {
    const stored = window.localStorage.getItem("agentos-lite-locale");
    if (stored === "en" || stored === "zh") {
      setLocaleState(stored);
    }
  }, []);

  const value = useMemo<I18nContextValue>(() => {
    const setLocale = (nextLocale: Locale) => {
      setLocaleState(nextLocale);
      window.localStorage.setItem("agentos-lite-locale", nextLocale);
    };
    return {
      locale,
      setLocale,
      t: (key) => translations[locale][key] ?? translations.en[key],
    };
  }, [locale]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error("useI18n must be used inside I18nProvider");
  }
  return context;
}

