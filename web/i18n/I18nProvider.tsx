"use client";

import { useEffect, useState } from "react";
import i18n from "i18next";

import {
  ensureLanguage,
  initI18n,
  normalizeLanguage,
  type AppLanguage,
} from "./init";

// Initialize i18next at module load (before any React render) so that the
// `init()` call — which fires `initialized` / `languageChanged` events that
// trigger setState on subscribed components — never happens during another
// component's render phase. Calling `initI18n` from the render body would
// produce the React warning:
//   "Cannot update a component (`X`) while rendering a different component
//   (`I18nProvider`)."
initI18n();

/** Direction of the document for a UI language; Arabic is the only RTL locale. */
export function documentDirection(language: AppLanguage | string): "rtl" | "ltr" {
  return normalizeLanguage(language) === "ar" ? "rtl" : "ltr";
}

// LTR fragments must not inherit RTL direction from ancestors. `isolate`
// prevents a number, URL, identifier or formula from leaking its direction
// into the surrounding Arabic text; `ltr` is applied only to fragments that
// are intrinsically LTR. Everything else uses CSS logical properties.
const RTL_LTR_ISOLATION_CSS = `
[dir="rtl"] :is(code, kbd, samp, pre, .katex, .katex-display, [dir="ltr"], [data-dir="ltr"], a[href^="http"]) {
  direction: ltr;
  unicode-bidi: isolate;
}
`;

export function I18nProvider({
  language,
  enabled = true,
  children,
}: {
  language: AppLanguage | string;
  enabled?: boolean;
  children: React.ReactNode;
}) {
  const nextLang = normalizeLanguage(language);
  const isRtl = documentDirection(nextLang) === "rtl";
  const [readyLanguage, setReadyLanguage] = useState<AppLanguage | null>(() =>
    enabled &&
    i18n.language === nextLang &&
    i18n.hasResourceBundle(nextLang, "app")
      ? nextLang
      : null,
  );

  useEffect(() => {
    let cancelled = false;
    if (!enabled) return () => undefined;
    void ensureLanguage(nextLang).then(async () => {
      if (cancelled) return;
      if (i18n.language !== nextLang) {
        await i18n.changeLanguage(nextLang);
      }
      if (cancelled) return;
      // Keep <html lang/dir> in sync for accessibility, Intl defaults and RTL.
      // Setting dir back to ltr matters when switching from ar to another UI
      // language in the same session.
      document.documentElement.lang = nextLang;
      document.documentElement.dir = isRtl ? "rtl" : "ltr";
      setReadyLanguage(nextLang);
    });
    return () => {
      cancelled = true;
    };
  }, [enabled, nextLang, isRtl]);

  if (!enabled || readyLanguage !== nextLang) {
    return (
      <div
        aria-busy="true"
        aria-hidden="true"
        className="min-h-dvh bg-[var(--background)]"
      />
    );
  }
  return (
    <>
      {isRtl ? <style data-deeptutor-rtl>{RTL_LTR_ISOLATION_CSS}</style> : null}
      {children}
    </>
  );
}
