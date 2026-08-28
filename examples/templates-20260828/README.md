# Finished examples: survey-absorbed templates (2026-08-28)

Filled, audit-clean examples for the two templates absorbed from the
scientific-reporting literature survey. All facts are synthetic showcase data.

| Example | Template | Standard | Audit mode | Receipt |
|---|---|---|---|---|
| [rebuttal-response.md](rebuttal-response.md) | `rebuttal-response` | Peer-review response norms (point-by-point, outcome-first, no unverifiable promises) | `review-report` | [audits/rebuttal-response.json](audits/rebuttal-response.json) |
| [release-card.md](release-card.md) | `release-card` | Model cards (Mitchell et al.) and datasheets (Gebru et al.) | `implementation-handoff` | [audits/release-card.json](audits/release-card.json) |

Both receipts show zero errors and zero warnings, including the readability
warnings (`generic-heading`, `heading-level-skip`, `long-sentence`,
`deep-list-nesting`, `cjk-halfwidth-punctuation`).

Regenerate a receipt with:

```bash
python3 skills/agentic-reporting/scripts/reportctl.py audit \
  --file examples/templates-20260828/<example>.md --mode <audit-mode> --json
```
