# Experiment report

Use this mode for benchmarks, ablations, controlled evaluations, model comparisons,
or empirical studies. Organize around research questions, not run order.

## Semantic order

1. **Main result:** state the supported result and its most important trade-off or
   caveat.
2. **Research question:** define the proposition each experiment tests.
3. **Protocol:** identify methods, baselines, data, splits, selection procedure,
   metrics, compute, and material controls.
4. **Results:** present exact evidence with the tables or visuals needed to read it.
5. **Analysis:** explain patterns, exceptions, practical magnitude, and competing
   interpretations.
6. **Boundary:** report uncertainty, null results, failed runs, limitations, and the
   domain the evidence covers.
7. **Conclusion and next experiment:** state only what the protocol supports.

## Metric and uncertainty contract

For every decision-relevant metric, state:

- definition, unit, and higher-is-better or lower-is-better direction;
- evaluation population, denominator, and aggregation level;
- number of independent runs, seeds, trials, samples, or tasks;
- variability source, interval type (SD, SEM, CI, quantiles), and its
  computation when that affects interpretation.

Call a difference statistically significant only with a defined supporting
analysis; significance is not practical importance.

## Comparability and selection

- Rank or highlight methods only within one evaluation protocol.
- Expose material differences in data, supervision, pretraining, compute, hardware,
  tuning budget, test-time resources, and privileged information.
- State how hyperparameters, checkpoints, prompts, seeds, and reported runs were
  selected; never compare a selected best run with a baseline mean silently.
- Account for every candidate run and sample: counts and reasons at each
  exclusion step.
- Keep zero, missing, not reported, failed, and not applicable distinct.
- Declare leakage controls: split construction, train-only fitting of
  data-dependent steps, duplicate and temporal checks, and the contamination
  check for pretrained components (`not checked` is an answer; omission is not).
  An unresolved leak makes a number an upper bound.

## Analysis discipline

- Report verified values before explaining them.
- Discuss results that contradict the narrative, not only the best row.
- Treat nearly equal means with untested uncertainty as unresolved, not a winner.
- With opposing metrics, report the Pareto trade-off; collapse it into one ranking
  only when the decision supplies a utility, budget, or threshold.
- Separate descriptive, diagnostic, predictive, causal, and deployment claims.
- State compute and resource needs when they affect reproducibility or
  comparison.

## Avoid

- A leaderboard mixing different tasks or protocols.
- Boldface as a substitute for analysis.
- `state of the art` without a named benchmark, metric, comparison set, and
  verified result.
- A conclusion broader than the tested data, seeds, environments, or
  deployment conditions.
