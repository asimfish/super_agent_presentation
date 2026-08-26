# Examples

Real, end-to-end outputs produced by this framework, kept with their full
generation and audit receipts. Nothing here is a blank template: every report was
generated through the actual CLI workflow
(`route → checkpoint → bundle → write → strict audit → semantic oracle`) and the
receipts for each step are preserved next to the finished artifact.

## templates-20260826

Filled, audit-clean examples for the two standards-based templates added on
2026-08-26 (`sbar-handoff` from SBAR, `executive-onepager` from the Minto
pyramid principle), each with its zero-error, zero-warning audit receipt. See
[`templates-20260826/README.md`](templates-20260826/README.md).

## showcase-20260825

One finished sample for every core mode and research profile, plus one rendered
HTML academic deck. Final verdict of the run: **ALL PASS**
(16/16 strict audit, 16/16 semantic oracle, 9/9 HTML static gate, 11/11 real-render
checks, 7/7 manual page review).

| Entry point | What it shows |
|---|---|
| [`index.md`](showcase-20260825/index.md) | Human index of all 16 reports with per-report receipts |
| [`modes/`](showcase-20260825/modes/) | 12 finished core-mode reports (concise answer → postmortem) |
| [`profiles/`](showcase-20260825/profiles/) | 4 finished research-profile reports (RL, embodied AI, world models, VLA) |
| [`html/deck.html`](showcase-20260825/html/deck.html) | 7-page assertion–evidence academic talk built from the `academic-talk-html` template |
| [`render/academic-talk.pdf`](showcase-20260825/render/academic-talk.pdf) | The same deck printed to PDF through real Chrome |
| [`render/contact-sheet.png`](showcase-20260825/render/contact-sheet.png) | One-image overview of all 7 rendered pages |
| [`audit-summary.md`](showcase-20260825/audit-summary.md) | Aggregated acceptance summary with per-group numbers |
| [`first-failures.md`](showcase-20260825/first-failures.md) | Honest log of every first-attempt failure and how it was fixed |
| [`manifest.json`](showcase-20260825/manifest.json) | Machine-readable manifest binding reports, receipts, and verdicts |

The `routes/`, `checkpoints/`, `bundles/`, `audits/`, `oracles/`, and `inputs/`
directories keep the intermediate receipts for each report, and the
`*-commands.json` files record the exact CLI commands used, so the whole run can
be re-derived or spot-checked.

### Boundaries

Quoted from the run manifest, unchanged:

- All report facts are synthetic fixtures; no real research or production
  validity is claimed.
- Rendered only on macOS with Chrome 151.0.7922.172, current system fonts, and
  local Poppler.
- No Firefox, Safari, Linux, alternative CJK font, Quarto, or Reveal export was
  verified.

The showcase run's session-local orchestration scripts are not vendored here;
the command receipts above document what they executed. The sample reports are
written in Chinese because that was the requesting user's language — the
framework itself is language-neutral.

### Reproducing a sample

Any single report can be re-derived from the repository root, for example:

```bash
python3 skills/agentic-reporting/scripts/reportctl.py bundle \
  --task "Report a five-seed RL ablation with one result table" \
  --mode experiment-report --profile reinforcement-learning --module tables
python3 skills/agentic-reporting/scripts/reportctl.py audit \
  --file your-report.md --mode experiment-report --strict
```

See the repository [README](../README.md) and
[`docs/CATALOG.md`](../docs/CATALOG.md) for the full mode, profile, module, and
template catalog.
