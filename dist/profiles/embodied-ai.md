# Research profile: embodied-ai

# Embodied-AI research profile

Load this profile for navigation, manipulation, mobile manipulation, and embodied
agent studies. Keep simulation, real-robot, and human-in-the-loop evidence separate.

## Protocol card

Identify the task, embodiment and hardware, environment/simulator version, scene
and object sets, sensor suite, observation history, action representation, control
frequency, action horizon, termination/success condition, reset procedure, safety
constraints, and operator interventions. State train/validation/test splits across
scenes, tasks, objects, layouts, language instructions, and embodiments.

For every success metric, specify the tolerance, time/step budget, denominator,
number of independent trials, initial-state sampling, retry policy, and whether a
human judged completion. Use benchmark-specific metrics such as SPL only with the
benchmark definition and protocol that make them comparable.

A success rate is a binomial estimate: report `k/n` with a Wilson or Clopper-Pearson
95% interval, never a bare percentage or a Wald `± SE` band. The interval fixes the
resolvable difference (7/10 versus 8/10 gives [0.40, 0.89] versus [0.49, 0.94]:
undetermined; 70/100 versus 80/100 gives [0.60, 0.78] versus [0.71, 0.87]), so
choose the trial count from the difference the claim must resolve, before running.

## Result displays

- Protocol table first: simulator versus real, robot, sensors, control rate, split,
  trials, success rule, and intervention policy.
- Quantitative tables grouped by identical protocol; do not rank real and simulated
  evaluations together.
- Generalization matrix across seen/unseen task, object, scene, language, and robot.
- Failure taxonomy with counts or denominators: perception, planning, contact,
  grasp, execution, timeout, safety stop, and ambiguous instruction as applicable.
- Qualitative sequences only with selected-case policy and a statement that images
  do not establish aggregate performance.

## Analysis contract

Separate task success from efficiency, robustness, safety, latency, and recovery.
Report resets, invalid trials, hardware failures, manual interventions, and the rule
used to include them. Bound conclusions to the tested embodiment and distribution.
Compare real-robot policies back-to-back on matched initial conditions in
interleaved or randomized order with a constant operator and hardware state, and
record drift (lighting, battery, wear, object substitution). Videos illustrate
behavior under a stated selection rule; they are not aggregate evidence.

Provenance IDs: EMB-1 Habitat challenge evaluation; EMB-2 CALVIN long-horizon
language-conditioned evaluation; EMB-3 binomial rollout bounds (Vincent et al.
2024); EMB-4 RoboArena pairwise real-robot protocol; STAT-1 binomial interval
choice (Brown, Cai & DasGupta 2001). See the portable `UPSTREAM.md`; the source
repository's detailed adoption ledger is `docs/TEMPLATE-SOURCES.md`.
