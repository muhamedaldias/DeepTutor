# Independent RTL review — baba-hermes (fresh session)

- agent: baba-hermes (independent RTL verification agent; did not write the implementation)
- machine: baba (instabox sandbox, Linux); repo /data/workspace/DeepTutor
- issue: audit Arabic RTL coordination in web UI
- branch: feat/mcp-agent-bridge (HEAD aea0602)
- status: COMPLETE — audit delivered; narrow RTL-only fix applied and verified
- updated UTC: 2026-11-26T17:00:00Z

## Understanding

- RTL implementation lives in `web/i18n/I18nProvider.tsx` (+ `languages.ts`, `init.ts`); design doc and plan state "RTL is implemented in the i18n provider, not per-component".
- `documentDirection()` maps only `ar` to rtl; the effect sets both `document.documentElement.lang` and `.dir` (`rtl`/`ltr`), including explicit switch-back. Verified by source + passing test.
- Before the fix, the ONLY RTL-specific CSS in web/ was the injected isolation string at `I18nProvider.tsx:31-36` (grep: 1 match). No global `[dir=rtl]` mirroring stylesheet exists — this is the root cause of the layout findings.
- Root layout hardcodes `<html lang="en">` with no `dir` (`app/layout.tsx:48-53`); language hydrates post-mount (`AppShellContext.tsx:95-96`). Theme has a pre-paint script, language does not → LTR/`lang=en` flash for Arabic users.
- Locale JSONs are owned by another agent and were modified concurrently; out of scope, not edited.

## Decisions

- Verified every subagent finding myself by reading the exact file:line before reporting.
- Fix limited to the RTL-only style block in `web/i18n/I18nProvider.tsx`; no locale JSON, layout.tsx, provider/model config, auth or unrelated product CSS edits.
- `rehype-dir-auto.test.ts` is excluded from vitest's include pattern but DOES run via `npm run test:node` (compiled `.test.js`) — not a dead test.
- No browser/live UI check performed (no credentials, no public instance from this session); visual effects inferred from code/CSS, flagged as such.

## Files changed

- `web/i18n/I18nProvider.tsx` — RTL-only style block: added mailto:/tel: to LTR-isolation selector; added RTL-scoped mirroring for `.dt-select`, prose lists/blockquote/table th/footnotes, `.dt-answerer-name`, `.dt-popup-up`.
- `web/tests/arabic-rtl.spec.tsx` — added 2 computed-style tests (inline fragment isolation incl. mailto; select padding mirroring). Now 4 tests.
- `agent-memory/baba-hermes-rtl-review.md` (this checkpoint).

## Tests & evidence

- `npm run typecheck` → EXIT=0 (after fix).
- `npx eslint i18n/I18nProvider.tsx tests/arabic-rtl.spec.tsx` → EXIT=0, no output.
- `npx vitest run tests/arabic-rtl.spec.tsx` → 1 file / 4 tests passed (was 2 before fix). Computed `direction:ltr` on `<code>` and `mailto:` link; select `paddingLeft>0` / `paddingRight=0` under RTL.
- `npm run i18n:check` → EXIT=0 (informational untranslated jsxText/placeholder list printed).
- `npm run test:node` → 1410 tests, 1409 pass, 1 fail: `Arabic values are translated and keep placeholders intact` — "Failed.: pass-through altered", "contextBudget.estimated: pass-through altered" (locale values; other agent's scope).
- `vitest.config.mts:19` includes only `.spec.ts/.spec.tsx`; `scripts/run-node-tests.mjs:34` collects `.test.js`.
- `git status` before edit: only `locales/ar/app.json` + `common.json` modified by the other agent.

## Open issues

- Blocker (other agent): locale quality gate red on two pass-through values.
- Blocker (RTL): no global mirroring; viewer/watching panels still dock physically right/left and will overlap content under RTL (`globals.css:1178-1278`).
- Major: SSR/hydration LTR flash; toasts pinned bottom-right (`ToastViewport.tsx:45`); popovers/menus anchored physically (`modern.css:209,272,279,490`); tables/forms use physical alignment (`TooltipLayer.tsx:71`, `ToolsSettingsSection.tsx:264-275`, `UsageSettingsSection.tsx:168-204`); charts have no direction handling (`components/visualize/*` grep: 0 matches).
- Major: bidi isolation misses plain numbers/`{{count}}` placeholders and Latin product names; `dir="auto"` is not isolation (`rehype-dir-auto.ts:41-43`).
- Tests do not cover computed-style bidi, alignment/mirroring, or the risky component surfaces; new tests cover only the two fixed cases.

## Handoff

Report delivered in chat. Owner must decide whether to add a full RTL mirroring layer (logical properties across feature CSS/TSX) and a pre-paint language script; both outside this review's edit scope. Do not treat RTL as complete until those are addressed and a live UI check runs.
