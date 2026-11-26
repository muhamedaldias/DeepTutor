# Shard A review — read-only findings (baba-hermes)

- Reviewer: baba-hermes (baba)
- Date/UTC: 2026-11-26T15:05:40Z
- Source reviewed: `/data/home/.hermes/cache/scratch/ar-work/ar-shard-A.json` ∪ `ar-shard-A2.json` (read-only)
- References: `en-app.json` + `en-common.json`, `ar-glossary.md`, `keys-A.json`
- Snapshot caveat: the orchestrator is still running `--retry-failures` passes on shard A; counts below are for this snapshot and must be re-checked after the merge. A later check at 15:23:03Z showed union=3152 keys, 40 `__UNTRANSLATED__` markers; the Major findings 2–5 were still present at that time.

## Blocker

1. `ar-shard-A.json` / `ar-shard-A2.json`: 80 keys still carry the literal `__UNTRANSLATED__` prefix in this snapshot (examples: `Disable selected`, `Disabled`, `Discard`, `Discard unsent draft`, `Discard your changes?`, `Disconnect`, `Dismiss`, `Display a gutter with line numbers beside each code block.`).
   Why: the primary translator exhausted its 3 retries; the value is English with a failure marker, so it would ship as untranslated UI copy.
   Severity: Blocker.
   Suggested fix: owner agent (or the orchestrator's `--retry-failures` pass) must replace these values with MSA and assert zero `__UNTRANSLATED__` markers before merging. Do not edit from this review.

## Major

2. `ar-shard-A.json:Failed.` — value is exactly `Failed.` (unchanged English, no Arabic script).
   Why: a translatable UI status string was left in English; violates the "no English residue" gate and would fail the locale-quality test.
   Severity: Major.
   Suggested fix: translate to `فشل.` (keep the trailing period).

3. `ar-shard-A.json:Follow-up` — value is exactly `Follow-up` (unchanged English).
   Why: translatable label left in English.
   Severity: Major.
   Suggested fix: translate to `متابعة` (or `سؤال متابعة` if the UI label means a follow-up question).

## Minor

4. 10 values mix the ASCII comma `,` into Arabic prose (e.g. `ar-shard-A.json:Already in your library as “{{title}}”, used by {{where}}. It will be reused, with its annotations.` → `..., ويستخدمه {{where}}. سيتم إعادة استخدامه, مع تعليقاته...`; also `An administrator installs these, then assigns them to accounts.`, `Choose which messages to include, pick one or more notebooks, and a su...`, `Chunking, budget, dedup, and reference policies`, `Language, embedding, search, voice, and generation models`).
   Why: MSA typography uses the Arabic comma `،`; the English comma inside Arabic text is a visible editorial inconsistency (8 values similarly use ASCII `;`).
   Severity: Minor.
   Suggested fix: replace the separators with `،` and `؛` (preserve placeholders and any Latin/URL fragments byte-for-byte).

5. `ar-shard-A.json:Arxiv Search` → `بحث أرخايف`.
   Why: the glossary keeps product/brand names in Latin script; `أرخايف` transliterates the `arXiv` brand.
   Severity: Minor.
   Suggested fix: use `بحث arXiv`.

## Informational / not defects

6. `*.md`, `<h2>...</h2>`, `Chart.js`, `Bilibili`, `Claude Code`, `Codex`, `Docker`, `GeoGebra`, `GitHub`, `Glob`, `Grok CLI`, `HTML`, `MCP`, `Markdown`, `N/A`, `language.chinese` (value `中文`) are unchanged Latin/markup-only strings. These are correct per the glossary and the "never translate identifiers / URLs" rule. They trip the translation script's naive "must contain Arabic script" validator, but should NOT be "fixed" by adding Arabic text. Suggested fix: whitelist value-shape-only keys (URL, markup, brand, numeric) in the validator instead.

7. `Invidious API URL` and `LightRAG server URL placeholder` have English *keys* but URL *values* (`http://127.0.0.1:3000`, `http://localhost:9621`). Leaving the values unchanged is correct; keys are immutable.

8. `keys-A.json` has 3376 entries but only 3358 unique keys — 18 keys appear twice (e.g. `Account library`, `Assigned resources`, `Clear instructions`). Not a translation defect; suggested fix for the orchestrator: dedupe the key list before the parity gate so the union check is unambiguous.

9. Placeholder/tag preservation: 0 drift detected across the reviewed union (checked `{{name}}`, `{name}`, HTML tags and `%s`/`%d`). Glossary adherence for the high-frequency terms (provider → مزوّد, model → نموذج, agent → وكيل, knowledge base → قاعدة معرفة, notebook → دفتر ملاحظات, chat → محادثة) was correct in the sampled strings; plural/definite-article variants (e.g. `النماذج`, `إعدادات`) are legitimate morphology, not findings.

## What this review did NOT verify

- Did not edit shard A (hard scope boundary), shard B, locale files, provider/model config or credentials.
- Did not verify the final merged locale — the orchestrator's retry passes were still running at the time of review; re-run `review_A_union.py` after the last pass.
- Did not exhaustively proofread all 2808 reviewed values; sampled 30 random values plus targeted automated checks.
