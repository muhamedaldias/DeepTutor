# Checkpoint — Arabic UI localization (baba / hermes)

- agent: baba-hermes (implementation agent; scope A + B + shard-A review)
- machine: baba (instabox sandbox, Linux)
- issue: Arabic UI localization — register `ar`, RTL, translate shard B, review shard A
- branch: feat/mcp-agent-bridge (base origin/main); nothing pushed
- status: SCOPE COMPLETE — code implemented and verified; primary shard-B run ended (superseded by orchestrator retries); shard-A review delivered
- updated UTC: 2026-11-26T15:23:03Z

## Understanding

Read in order: design doc `docs/superpowers/specs/2026-11-26-arabic-localization-design.md`, `tasks/plan.md`, `/data/home/.hermes/cache/scratch/ar-work/ar-glossary.md`, the i18n source files and `translate_ar.py`.

- English source: 6666 app keys; `keys-B.json` = 3333 keys, `keys-A.json` = 3376 entries / 3358 unique (18 duplicates). Work-dir English JSONs were byte-identical (md5) to the repo English catalogs at task start.
- `web/i18n/init.ts` loads only the `app` namespace for every language; `common.json` is a 43-key subset of `app.json` with no source importer, so no Arabic `common.json` import was added (it would be dead code and would reference a forbidden-to-create file).
- `language.arabic` did not exist initially; the orchestrator later added it to all 13 shipped catalogs with `add_endonym.py`, so the registry now uses the exact `language.*` pattern.
- `i18n-audit.spec.ts` and `reading-zoom.test.ts` derive shipped locales from the registry/init file, so registering `ar` before the orchestrator creates `web/locales/ar/` necessarily makes those two checks fail on a missing file.

## Decisions

- `languages.ts`: `{ code: "ar", labelKey: "language.arabic" }`; `normalizeLanguage` also accepts `ar`, `ar-*`, `Arabic`, `العربية`.
- `init.ts`: `ensureLanguage("ar")` dynamically imports `@/locales/ar/app.json` exactly like the other 13 languages. A `// @ts-ignore` (not `@ts-expect-error`) keeps `tsc` green in the pre-merge window and stays harmless after the file lands.
- `I18nProvider.tsx`: exported pure `documentDirection()`; the effect sets `document.documentElement.lang` and `dir` together — `rtl` for `ar`, `ltr` otherwise so switching back restores LTR. An RTL-only `<style data-deeptutor-rtl>` isolates intrinsically LTR fragments (`code`, `kbd`, `samp`, `pre`, `.katex`, `[dir="ltr"]`, http links) via `direction:ltr; unicode-bidi:isolate`.
- Added `web/tests/arabic-rtl.spec.tsx` (distinct from the other agent's `arabic-locale-quality.test.ts`).
- Did not create/edit `web/locales/ar/*`, shard A, other locale files, provider/model config or credentials; deleted nothing; no secrets read or printed.

## Files changed

- `web/i18n/languages.ts`, `web/i18n/init.ts`, `web/i18n/I18nProvider.tsx`
- `web/tests/arabic-rtl.spec.tsx` (new)
- `agent-memory/baba-hermes-ar-checkpoint.md`, `agent-memory/baba-hermes-issue-ar-review.md`, `agent-memory/baba-hermes-ar-shard-B-failures.txt`

## Tests & evidence

- `node -e "…i18next…"` → `t(language.arabic) => العربية`.
- `npm run typecheck` → exit 0. `npx eslint <4 changed source/test files>` → exit 0, no output.
- `npm run test:node` (full, 1407 tests) → 1406 pass, 1 fail: `reading-zoom.test.ts` "new copy is translated in every shipped locale", `ENOENT: locales/ar/app.json`; it checks only that English key strings exist, so it passes once the orchestrator creates the merged file.
- Real-config `npx vitest run tests/i18n-audit.spec.ts tests/partial-locale-fallback.spec.ts tests/i18n-colon-keys.spec.ts` → 2 suites fail Vite resolution of `@/locales/ar/app.json`, 1 suite / 6 tests pass. Same four specs plus `arabic-rtl.spec.tsx` through a **scratch-only** alias shim (`/data/home/.hermes/cache/scratch/ar-work/vitest-ar.config.mts`, real config untouched) → 4 files / 13 tests pass, including the RTL lang/dir/LTR-isolation/switch-back test.
- Shard B primary run: started 13:06Z (PID 934711, `translate_B.log`), `total=3333 done=0 pending=3333`; last log line `progress 2840/3333 failures=680` at 14:51Z; `grep -c '^FINISHED' translate_B.log` → 0. The gateway later reported the shell pipeline "completed normally (exit code 0)", but that is `tee`'s status — the Python never emitted FINISHED and stopped 493 keys short. PID 934711 was gone; the orchestrator superseded it with `--retry-failures` passes (modified `translate_ar.py` at 14:23Z). **Exact failure count from the primary run: 680 distinct keys**, derived from the 17 `batch … attempt 3` ranges in the log; full list in `agent-memory/baba-hermes-ar-shard-B-failures.txt`. At 15:23Z the orchestrator-owned `ar-shard-B.json` had 2758 keys / 40 markers — still converging.
- Shard A review: delivered at `agent-memory/baba-hermes-issue-ar-review.md`. Snapshot 15:05Z (2808-key union): 80 `__UNTRANSLATED__`, 2 Major English-residue keys (`Failed.`, `Follow-up`), 10 ASCII-comma instances, 1 brand transliteration (`Arxiv Search` → `بحث أرخايف`), 18 duplicate keys in `keys-A.json`, 0 placeholder drift. At 15:23Z: union 3152 keys / 40 markers, Major findings still present.

## Open issues

- `web/locales/ar/` still absent at 15:17Z; full real-config vitest / `npm run build` / live UI check cannot be run from my scope. Re-run after the orchestrator merges shards.
- Shard B and A retry passes were still running at 15:23Z; final key counts/failure counts are orchestrator-owned.
- The translation validator rejects whole 40-key batches when any value lacks Arabic script, so Latin-only brand/URL keys caused 680 collateral failures; orchestrator added `--retry-failures`. Suggest whitelisting URL/markup/brand-shape values in the validator.
- No PR opened; branch not pushed.

## Handoff

Orchestrator: merge A+B, add `language.arabic` to the ar catalog (already added to the other 13), then re-run `npm run test:node`, full `vitest run`, `npm run build` — the two missing-file failures should disappear. Apply the shard-A Major/Minor findings to the owner's shard. Baba's assigned scope is complete.
