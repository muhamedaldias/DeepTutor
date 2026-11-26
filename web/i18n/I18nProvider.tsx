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
[dir="rtl"] :is(code, kbd, samp, pre, .katex, .katex-display, [dir="ltr"], [data-dir="ltr"], a[href^="http"], a[href^="mailto:"], a[href^="tel:"]) {
  direction: ltr;
  unicode-bidi: isolate;
}

/* A few shared rules still use physical left/right. Mirror them here so the
   fix stays RTL-only and LTR locales are untouched. Scoped by [dir="rtl"] to
   outrank the single-class utilities in globals.css. */
[dir="rtl"] .dt-select {
  background-position: left 0.7rem center;
  padding-right: 0;
  padding-left: 2.15rem;
}
[dir="rtl"] :is(.prose ul, .prose ol, .prose dd) {
  margin-left: 0;
  margin-right: 1.5rem;
}
[dir="rtl"] .prose .footnotes ol {
  margin-left: 0;
  margin-right: 1rem;
}
[dir="rtl"] .prose blockquote {
  border-left: 0;
  border-right: 3px solid var(--muted-foreground);
  padding-left: 0;
  padding-right: 1rem;
}
[dir="rtl"] :is(.prose th, .watching-video-card) {
  text-align: start;
}
[dir="rtl"] .dt-answerer-name {
  margin-right: 0;
  margin-left: -4px;
}
[dir="rtl"] .dt-popup-up {
  transform-origin: bottom right;
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
