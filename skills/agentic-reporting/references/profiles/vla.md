# Vision-language-action research profile

Load this profile for VLA pretraining, fine-tuning, action tokenization/chunking,
cross-embodiment transfer, and VLA deployment studies.

## System and data card

Report the vision/language backbone and version; trainable/frozen components;
pretraining and fine-tuning dataset mixture; dataset units and filtering; robot
morphologies; camera views and proprioception; language source; action space,
normalization, tokenizer or continuous head; action chunk/horizon; control
frequency; inference latency; and deployment hardware.

State whether data overlap exists across robots, tasks, objects, scenes, or language
templates. Separate zero-shot, in-context, fine-tuned, and jointly trained results.
Report the contamination check explicitly: whether evaluation scenes, objects,
instructions, or episodes can appear in the pretraining or fine-tuning mixture
(public mixtures contain many public evaluation suites), how this was checked, or
`not checked`.

## Evaluation card

For simulation and real robot separately, report benchmark/version, embodiment,
task suite, seen/unseen axes, rollouts per task, seeds or independent training runs,
initial-state distribution, success definition, reset/retry rule, interventions,
safety stops, and checkpoint selection. Do not hide morphology-specific adaptation
inside a “generalist” label.

## Result displays

- Data/training table: mixtures, episodes/trajectories, embodiments, task coverage,
  updates, compute, and selection.
- Evaluation table: protocol group, task count, trials, success as `k/n` with a
  small-sample binomial interval (Wilson or Clopper-Pearson; see the embodied-AI
  profile for the resolvable-difference rule), and failure count; never rank
  incompatible robots or success definitions. Real-robot comparisons state the
  back-to-back, matched-initial-condition, interleaved-order protocol or its absence.
- Generalization matrix: new task, object, scene, instruction, camera, embodiment,
  and perturbation.
- Deployment table: latency, control rate, action horizon, hardware, recovery, and
  safety interventions.
- Failure taxonomy: language grounding, visual ambiguity, action discretization,
  contact/grasp, temporal drift, planning, latency, and unsafe/invalid output where
  observed.

Provenance IDs: VLA-1 Open X-Embodiment/RT-X data standardization; VLA-2 OpenVLA
reproduction and rollout accounting; EMB-2 CALVIN closed-loop protocol; EMB-3
binomial confidence bounds for rollouts; EMB-4 RoboArena pairwise real-robot
protocol; GEN-5 benchmark-contamination reporting. See the portable `UPSTREAM.md`;
the source repository's detailed adoption ledger is `docs/TEMPLATE-SOURCES.md`.
