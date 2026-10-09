# Experiment report

Use this mode for benchmarks, ablations, controlled evaluations, model comparisons,
or empirical studies. Organize around research questions, not run order.

## Scientific argument

Lead with the answer to a research question, not a list of improved metrics.
Name the uncertainty, assumption, or limitation it addresses. A useful result can
narrow a hypothesis or rule out a route without improving a score.

For each main finding, connect the discriminating comparison to an interpretation
and scope. Say what changed in the working view and what remains unresolved.
Separate a measured effect from a proposed mechanism; an ablation can isolate a
component's contribution without establishing why it works. Name the strongest
plausible competing explanation when material; do not invent one to fill a slot.

Give the reader the comparison and practical consequence, not a recital of cells.
Keep counterexamples and decisive controls in the main reading path. Move full
sweeps, logs, and reproducibility detail to an appendix; omission must not hide
contradictory evidence or weaken the comparison basis.

End with a position, including "unresolved". If needed, propose a discriminating test:
what changes, what stays fixed, and how different outcomes change the decision.
"More seeds" addresses uncertainty; it does not by itself identify a mechanism.

## Semantic order

Finding/question -> decisive comparison -> interpretation/counterevidence ->
bounded conclusion -> next test if needed. Methods needed to read evidence go
beside it; full detail can follow. These are roles, not mandatory headings.

## Metric and uncertainty contract

For material metrics, make direction, unit, population/denominator, aggregation,
independent run count, and variability source/interval (SD, SEM, CI, quantiles)
recoverable. Define unfamiliar metrics only. Explain interval computation when
it affects interpretation. Statistical significance needs a stated analysis;
practical importance needs a research or decision criterion.

## Comparability and selection

- Rank only comparable protocols; disclose material data, supervision,
  pretraining, compute/hardware, tuning, test-time, and privileged-access differences.
- State hyperparameter, checkpoint, prompt, seed, and run selection. Account for
  exclusion counts/reasons and failed runs; never compare a best with a baseline mean.
- Distinguish zero, missing, not reported, failed, and not applicable.
- Disclose split construction, train-only preprocessing, duplicate/temporal
  checks, and pretrained contamination checks. "Not checked" is a valid status;
  an unresolved leak prevents an unqualified performance claim.

## Analysis discipline

- Separate descriptive, diagnostic, predictive, causal, and deployment claims.
- Untested uncertainty does not establish a winner or equivalence.
- Opposing metrics require a trade-off; a single ranking needs a stated utility,
  budget, or threshold. Name the closest relevant baseline before attributing gains.

## Avoid

- Metric recitation, unexplained boldface, or a leaderboard of incompatible tasks.
- A causal story inferred from a score increase; significance used as importance.
- `state of the art` without a verified benchmark and comparison set.
- Conclusions broader than the tested data, runs, or deployment conditions.
