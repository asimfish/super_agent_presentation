# Fresh-agent forward-test record

Date: 2026-08-24

This directory records development-set forward tests performed with fresh agent
contexts. The agents received the case facts plus the installed reporting contract;
they did not receive the expected fixture text. These are same-model development
tests, not a human, cross-model, or public blind benchmark.

## Cases and final gate

| Case | Long-context pressure | Final candidate | Machine checks | Structural audit | Adversarial review |
|---|---|---|---:|---:|---|
| Experiment with a null significance boundary | No | `experiment-framework-v3.md` | 10/10 | 0 errors, 0 warnings | No critical error found |
| Engineering handoff with a late integration failure | Yes; checkpoint reloaded after distraction reads | `engineering-long-framework.md` | 10/10 | 0 errors, 0 warnings | No critical error found |
| Evidence-bounded paper synthesis | No | `paper-format-framework-v2.md` | 10/10 | 0 errors, 0 warnings | No critical error found |

The final adversarial assessment is `judge-3.json`. It explicitly identifies itself
as a same-model, non-human, non-blind development review.

The retained engineering checkpoint is a frozen schema-v1 development artifact from
that run. Current `route`/`bundle` commands can still read it, but it predates and
does not demonstrate the schema-v2 same-checkpoint final audit. The historical JSON
is intentionally not rewritten.

## What failed before the final candidates

The failed iterations are intentionally retained:

- `experiment-framework.md` used a two-hyphen Markdown separator. The original
  audit missed it; the audit and regression tests were strengthened.
- `experiment-framework-v2.md` passed the machine checks, but `judge-2.json`
  caught an unsupported cross-metric “balance” ranking without a utility function,
  budget, or threshold. The experiment and conclusion protocols now require a
  Pareto/trade-off statement instead; v3 was generated from the revised protocol.
- `paper-format-framework.md` changed “not reported” into an asserted absence and
  attributed the limitation to the paper. The academic protocols now require the
  original epistemic operator; v2 was generated from the revised protocol.
- The evaluator itself produced false negatives for a legitimate unit-test wording,
  coordinated limitation wording, and a negated state-of-the-art boundary. Those
  checks were narrowed and covered by regression tests instead of editing correct
  candidate prose to satisfy a brittle regex.

`judge-1.json` and `judge-2.json` preserve the two earlier reviews. Their findings
are part of the development trace; only `judge-3.json` evaluates all three final
candidates.

## Reproduce the deterministic portion

```bash
python3 scripts/presentation_benchmark.py check \
  --case experiment-null-result \
  --response evals/runs/forward/experiment-framework-v3.md
python3 scripts/presentation_benchmark.py check \
  --case engineering-late-failure \
  --response evals/runs/forward/engineering-long-framework.md
python3 scripts/presentation_benchmark.py check \
  --case paper-summary-bounded \
  --response evals/runs/forward/paper-format-framework-v2.md
```

The machine checks establish only that specified structural and lexical constraints
hold. With no untreated baseline, token telemetry, cross-model sample, or human blind
ratings, this record does **not** establish that the framework improves readability,
correctness, consistency, or efficiency in general.

The sanitized real-host integration record is documented in the
[Codex development pilot](../pilot/codex-20260824/README.md).
