import { APP_LANGUAGES } from "@/i18n/languages";

const LANGUAGE_STORAGE_KEY = "deeptutor-language"; // context/app-shell-storage.ts

/**
 * LanguageScript - Initializes <html lang/dir> from localStorage before React
 * hydration, the same way ThemeScript paints the theme. Without this, Arabic
 * users see an LTR/`lang="en"` frame before AppShellContext hydrates.
 *
 * Must be a Server Component: in Next.js / React 19, <script> tags rendered
 * by Client Components are inert on the client. Rendering it from the server
 * inlines the snippet into the SSR HTML so the browser executes it before
 * hydration. `suppressHydrationWarning` on <html> covers the attribute change.
 */
export default function LanguageScript() {
  const supportedCodes = JSON.stringify(APP_LANGUAGES.map(({ code }) => code));
  const languageScript = `
    (function() {
      // Only the public UI-language preference is read here.
      var supported = ${supportedCodes};
      var lang = 'en';
      try {
        var stored = localStorage.getItem('${LANGUAGE_STORAGE_KEY}');
        if (typeof stored === 'string') {
          var code = stored.trim().toLowerCase().replace(/_/g, '-');
          lang = code.split('-', 1)[0];
          // Arabic aliases accepted by normalizeLanguage; other aliases only
          // affect lang, which the client normalizes after mount anyway.
          if (code === 'arabic' || code === '\\u0627\\u0644\\u0639\\u0631\\u0628\\u064a\\u0629') {
            lang = 'ar';
          }
        }
      } catch (e) {
        /* localStorage may be disabled: keep the SSR default. */
      }
      if (supported.indexOf(lang) === -1) lang = 'en';
      document.documentElement.lang = lang;
      document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    })();
  `;

  return (
    <script
      dangerouslySetInnerHTML={{ __html: languageScript }}
      suppressHydrationWarning
    />
  );
}
