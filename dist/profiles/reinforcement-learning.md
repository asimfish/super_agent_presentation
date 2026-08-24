# Research profile: reinforcement-learning

# Reinforcement-learning research profile

Load this profile for RL experiment reports, RL paper ideas, and source-grounded RL
paper presentations. Do not assume that practices from one benchmark transfer to
another.

## Protocol card

Report the environment/version; MDP or POMDP assumption; observation and action
spaces; reward and termination; horizon, discount, action repeat, reset policy;
online/offline data source; environment-step/frame convention; evaluation-policy
stochasticity; and train/evaluation separation.

Expose tuning budget, search space, tuning tasks/seeds, checkpoint selection, and
whether the same budget and implementation quality apply to every baseline. Count
all planned independent runs and disclose exclusions or failures; never select the
best seed as the method result.

## Result displays

- Learning curves: name x-axis interaction units, evaluation frequency, aggregation
  over runs, smoothing/window, and interval definition.
- Multi-task benchmarks: prefer interval estimates plus a robust aggregate such as
  IQM when appropriate; add performance profiles, probability of improvement, or
  optimality gap when they answer the claim. Do not prescribe one statistic when
  its assumptions do not fit.
- Tables: separate final performance, sample efficiency, wall-clock/compute, and
  per-task results. State normalization references and direction for every metric.

## Analysis contract

Distinguish final return, data efficiency, compute efficiency, stability, and task
coverage. Report tasks or seeds that contradict the aggregate. A point-estimate
difference without uncertainty is descriptive, not a reliable win. State whether
paired seeds, common environment instances, or other pairing were used.

Provenance IDs: RL-1 `Deep Reinforcement Learning that Matters`; RL-2 `Deep RL at
the Edge of the Statistical Precipice` and RLiable; RL-3 `Empirical Design in
Reinforcement Learning`. The portable source list is in `UPSTREAM.md`; the source
repository's detailed adoption ledger is `docs/TEMPLATE-SOURCES.md`.
