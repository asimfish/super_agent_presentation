# Experiment report

Use this mode for benchmarks, ablations, controlled evaluations, model comparisons,
or empirical studies. Organize the report around research questions rather than the
order in which experiments were run.

## Semantic order

1. **Main result:** state the supported result and its most important trade-off or
   qualification.
2. **Research question:** define the proposition each experiment tests.
3. **Protocol:** identify methods, baselines, data, splits, selection procedure,
   metrics, compute, and material controls.
4. **Results:** present exact evidence with the tables or visuals required to read
   it.
5. **Analysis:** explain patterns, exceptions, practical magnitude, and competing
   interpretations.
6. **Boundary:** report uncertainty, null results, failed runs, limitations, and the
   domain in which the evidence applies.
7. **Conclusion and next experiment:** state only what the protocol supports.

## Metric and uncertainty contract

For every decision-relevant metric, state:

- definition, unit, and higher-is-better or lower-is-better direction;
- evaluation population, denominator, and aggregation level;
- number of independent runs, seeds, trials, samples, or tasks;
- variability source and whether the interval is SD, SEM, CI, quantiles, or another
  statistic;
- interval computation and assumptions when they affect interpretation.

Do not call a difference statistically significant without a defined analysis that
supports that statement. Do not equate statistical significance with practical
importance.

## Comparability and selection

- Rank or highlight methods only inside a shared evaluation protocol.
- Expose material differences in data, supervision, pretraining, compute, hardware,
  tuning budget, test-time resources, and access to privileged information.
- State how hyperparameters, checkpoints, prompts, seeds, and reported runs were
  selected. Do not compare a selected best run with a baseline mean without making
  the mismatch explicit.
- Keep zero, missing, not reported, failed, and not applicable distinct.

## Analysis discipline

- Report verified values before explaining them.
- Discuss results that contradict the main narrative, not only the best row.
- Treat nearly equal observed means with overlapping or untested uncertainty as a
  trade-off or unresolved comparison, not a universal winner.
- With opposing metrics, report the Pareto trade-off. Do not collapse it into an
  overall balance ranking unless the decision supplies a utility function, budget,
  constraint, or minimum acceptable threshold.
- Separate descriptive, diagnostic, predictive, causal, and deployment claims.
- State compute and resource requirements when they affect reproducibility or the
  comparison.

## Avoid

- A global leaderboard built from different tasks or protocols.
- Boldface as a substitute for analysis.
- `state of the art` without a named benchmark, metric, comparison set, and verified
  result.
- A conclusion broader than the tested datasets, seeds, environments, or deployment
  conditions.
