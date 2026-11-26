# RTL implementation checkpoint — baba-hermes-rtl-implementation

- agent: baba (RTL implementation agent, fresh session)
- repo /data/workspace/DeepTutor, branch feat/mcp-agent-bridge
- source review: agent-memory/baba-hermes-rtl-review.md
- updated UTC: 2026-11-26T00:00:00Z (initial milestone)

## Findings before edits

- Disk: `/dev/vdb 20G 19G 1007M 95% /data` — ~0.98 GiB free. Build deferred; skip if still <~1.5 GiB.
- Git status: modified I18nProvider.tsx, locales/ar/{app,common}.json, arabic-locale-quality.test.ts, arabic-rtl.spec.tsx; untracked review file. Locale files belong to another agent — untouched.
- LANGUAGE_STORAGE_KEY = `deeptutor-language` (web/context/app-shell-storage.ts:75). Written with canonical AppLanguage codes; client normalizes via `normalizeLanguage`.
- Only `ar` maps to RTL (`web/i18n/I18nProvider.tsx:22-25`); its effect sets html lang/dir after mount (lines 99-105).
- Viewer panel carries Tailwind `right-0` (SessionViewerPanel.tsx:1372); Tailwind utilities are emitted at globals.css:1-3, before custom rules, so custom CSS of equal specificity still wins. For RTL I will use explicit `[dir=rtl]` overrides with higher specificity rather than mixing physical utility `right-0` with logical `inset-inline-end`.
- TooltipLayer's `left` is JS-computed from DOMRects (`tooltip-position.ts:19-46,75-85`); switching it to logical inset would be incorrect without rewriting that math — deliberately left alone. Only its `text-left` class is converted.
- ComposerTrayMenu sets inline `left`/`right` from physical `getBoundingClientRect` (`ComposerTrayMenu.tsx:56-61,272-280`), so `.dt-tray-popover.is-start/.is-end` left/right CSS and their physical transform-origin are intentionally left unchanged.
- Tailwind 3.4.17 supports `text-start`, `ps-*`, `pe-*`, `start-*`, `end-*`.

## Planned edits (RTL-only)

1. globals.css: coupled squeeze/panel mirroring (logical padding; `[dir=rtl]` overrides for panel inset + slide sign).
2. New `web/components/LanguageScript.tsx` + layout.tsx `<head>`: pre-paint lang/dir from `deeptutor-language`.
3. ToastViewport.tsx: `right-6` → `end-6`.
4. modern.css / TooltipLayer.tsx / settings sections: isolated logical anchoring + text alignment.

## Verification (final)

All commands run from `/data/workspace/DeepTutor/web` after the last edit:

- `npm run typecheck` → EXIT=0.
- `npm run test:node` → 1410 tests, 1410 pass, 0 fail.
- `npm run test:unit` → 264 files, 1474 tests, all pass (includes the new spec).
- `npx vitest run tests/rtl-prepaint.spec.tsx` → 6/6 pass.
- `npm run i18n:check` → EXIT=0 (parity OK; audit informational only).
- `npx eslint <changed ts/tsx files>` → EXIT=0, 0 errors, 1 pre-existing warning at UsageSettingsSection.tsx:222 (untouched).
- `postcss.parse` on globals.css and modern.css → PARSED_OK for both.
- `npm run build` NOT run: `/data` had ~1006M free and existing `.next` is 1.4G; per task instruction, skipped to avoid ENOSPC.

Note: an intermediate `test:node` run had 1 failure — architecture contract "browser storage methods stay behind the shared boundary" flagged LanguageScript.tsx. Fixed by allowlisting the pre-paint script exactly like ThemeScript in tests/architecture-contracts.test.ts:35-45; final run is green.

## Files changed by this agent

- web/app/globals.css:1167-1170,1181-1205,1217-1254,1267-1284,1299
- web/components/LanguageScript.tsx (new), web/app/layout.tsx:7,57
- web/components/common/ToastViewport.tsx:46
- web/features/ui-layout/modern/modern.css:209-211,277,284,292,442-443,512
- web/shared/ui/TooltipLayer.tsx:71
- web/features/settings/sections/ToolsSettingsSection.tsx:264,271,275,378
- web/features/settings/sections/UsageSettingsSection.tsx:168,183,192-208
- web/tests/rtl-prepaint.spec.tsx (new), web/tests/architecture-contracts.test.ts:35-45

Locale JSONs, I18nProvider.tsx and arabic-*.test/spec were already modified by other agents; not edited here.

## Deliberately left unfixed

- TooltipLayer.tsx:68-70 inline `left` from JS DOMRect math (tooltip-position.ts:19-46,75-85): converting to a logical inset would misplace RTL tooltips without rewriting the placement algorithm.
- ComposerTrayMenu.tsx:272-280 inline physical `left`/`right` from roomFor() (lines 56-61): `.dt-tray-popover.is-start/.is-end` left/right CSS and physical transform-origin (modern.css:495-500) are overridden by those inline styles; changing them is a no-op or wrong, and the JS placement is physical by design.
- `.dt-popover` base `transform-origin: top left` (modern.css:285): a global RTL override would collide with feature-specific origins in note-library.css/note-workspace.css; only the named sort menu got a scoped override.
- No live browser/UI check (no public instance or credentials from this session); effects verified by source, CSS parse and automated tests only. RTL is not claimed visually complete.

## Next step

Run `npm run build` when >=2 GiB is free, then a live Arabic UI check (viewer/watching panels, sort menu, rail panel, toasts, tooltips, settings table) on a running instance; keep the locale quality gate owned by the other agent in view.
