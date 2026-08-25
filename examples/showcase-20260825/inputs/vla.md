# Synthetic evidence pack: vla

- Nature: synthetic VLA fixture; not a real model or robot result.
- Policy: one fictional VLA checkpoint, trained once on 800 teleoperation trajectories from one arm and one fixed camera.
- Action interface: continuous delta pose; chunks of 4 actions at 10 Hz, so a chunk spans 400 ms without replanning.
- Hardware: synthetic device X; inference latency over 100 calls is p50 78 ms and p95 135 ms; control interval is 100 ms.
- Evaluation: final checkpoint; no retries; one rollout is one trial; one synthetic arm.
- Seen suite: 16/20 successes, 1 human takeover, 0 safety stops.
- OOD visual-perturbation suite: 8/20 successes, 5 human takeovers, 2 safety stops.
- Success requires task completion within 60 s; takeover and safety stop both count as failure.
- Statistics: Wilson 95% interval may be reported for success proportions; only one training run, no significance test.
- Unknown: train/evaluation scene overlap, other embodiments, energy, latency under contention, and whether teleoperation coverage includes the OOD perturbations.
