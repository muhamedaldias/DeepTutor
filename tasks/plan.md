# Implementation Plan: Arabic UI localization for DeepTutor

## Overview
Add a complete Arabic UI locale (app.json + common.json), RTL support, glossary, locale-quality test, and deploy the result on baba's fork with a verified public URL. Work is split 50/50 between two fresh Hermes sessions with reciprocal review.

## Architecture decisions
- Translation is data-only: English keys are immutable; only values are translated.
- One shared glossary (`docs/i18n/ar-glossary.md`) is authoritative for both translators.
- Two shards, deterministic sorted-key split, merged by a validation script that enforces exact key parity.
- RTL is implemented in the i18n provider, not per-component.

## Task list

### Phase 1 — Foundation
- [ ] Task 1: Snapshot English key inventory; create `docs/i18n/ar-glossary.md` with pinned terms (DeepTutor, Hermes, Codex, OpenCode, provider, model, agents, etc.).
  - Acceptance: sorted key list stored; glossary covers all domain terms and is referenced by both sessions.
  - Verification: `python3` count matches 6666/2 keys split; no missing key in union.
- [ ] Task 2: Register `ar` in `web/i18n/languages.ts` + `init.ts` and add RTL direction handling in `I18nProvider`.
  - Acceptance: `ar` appears in Settings picker, persists across reload, `dir="rtl"` active.
  - Verification: focused i18n tests + UI check.
- Checkpoint: registry and RTL verified; no build break.

### Phase 2 — Translation (two parallel fresh sessions)
- [ ] Task 3: Session A translates shard A (~3333 keys) into MSA using the glossary.
- [ ] Task 4: Session B translates shard B (~3333 keys) into MSA using the glossary.
  - Acceptance for both: no `[LLM REQUIRED]`, no untranslated English sentences, placeholders/tags intact.
  - Verification: deterministic script checks; glossary adherence; spot-check 50 strings each.
- Checkpoint: merge shards, assert 100% key parity with English; zero placeholder markers.

### Phase 3 — Reciprocal review and quality gate
- [ ] Task 5: Each session reviews the other's shard; fix findings by name; record in `agent-memory/`.
  - Acceptance: no blocker/major findings remain; ≤3 fix rounds.
- [ ] Task 6: Add `web/tests/arabic-locale-quality.test.ts` modeled on existing locale-quality tests; run `i18n_parity.mjs` and `i18n_audit.mjs`.
  - Acceptance: all green.
- Checkpoint: full locale suite green.

### Phase 4 — Build, deploy, verify
- [ ] Task 7: `npm run build`, full relevant tests, live restart on baba.
- [ ] Task 8: Commit + push to `muhamedaldias/DeepTutor` branch; re-publish port 3782.
- [ ] Task 9: External verification of the URL and Arabic language switching in Settings (with screenshots/DOM evidence).
- Checkpoint: public URL returns 200 and Arabic is selectable and renders RTL.

## Risks and mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| Disk full (baba ~1 GiB free) | High | Monitor `df -h /data` before builds; clean only generated caches if needed |
| Key drift / missing keys | High | Automated parity check before merge |
| Translator quality variance | High | Shared glossary + reciprocal review + locale-quality test |
| RTL breaking layout | Medium | Logical properties + dir isolation for LTR fragments + UI check |
| Free-plan run timeout | Medium | Checkpoints in `agent-memory/`, fresh session relaunch |

## Open questions
None after user approval of approach 1, RTL, and fresh sessions.
