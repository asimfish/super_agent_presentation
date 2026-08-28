# Finished examples: standards-based templates (2026-08-26)

Filled, audit-clean examples for the two templates absorbed from external
reporting standards. All facts are synthetic showcase data.

| Example | Template | Standard | Audit mode | Receipt |
|---|---|---|---|---|
| [sbar-handoff.md](sbar-handoff.md) | `sbar-handoff` | SBAR (IHI/AHRQ/WHO) | `incident-update` | [audits/sbar-handoff.json](audits/sbar-handoff.json) |
| [executive-onepager.md](executive-onepager.md) | `executive-onepager` | Minto pyramid principle | `decision-brief` | [audits/executive-onepager.json](audits/executive-onepager.json) |

Both receipts show zero errors and zero warnings, including the readability
warnings introduced with the standards absorption (`generic-heading`,
`heading-level-skip`, `long-sentence`, `deep-list-nesting`).

Regenerate a receipt with:

```bash
python3 skills/agentic-reporting/scripts/reportctl.py audit \
  --file examples/templates-20260826/<example>.md --mode <audit-mode> --json
```
