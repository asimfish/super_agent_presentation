# Synthetic facts: unresolved difference

Invented teaching facts. Question: whether a regularizer improves generalization.
Same data, model, training budget, evaluation split, and seed set. Three seeds per
configuration; means and SD across seeds. Macro-F1 is unitless and higher is better.

| Method | Macro-F1, mean ± SD |
|---|---:|
| Baseline | 0.711 ± 0.018 |
| Regularizer | 0.712 ± 0.019 |

Per-seed differences, a paired confidence interval, an equivalence margin, and a
significance analysis are unavailable. No broader-domain evaluation was run.
Other selection, leakage, and failed-run details are unknown. No cost advantage
or mechanism explanation is supplied.
