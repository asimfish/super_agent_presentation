# Synthetic evidence pack: HTML academic talk

- Nature: synthetic presentation fixture; no real VLA model, robot, or publication is represented.
- Question: under one fixed synthetic VLA checkpoint and visual-OOD suite, how does fixed 4-action chunking compare with an adaptive 1-or-4 action rule?
- Shared protocol: synthetic device X; one arm; 10 Hz; final checkpoint; 20 OOD rollouts per condition; no retry; success within 60 s; takeover or safety stop counts as failure.
- Fixed-4: 8/20 successes; 5/20 human takeovers; inference p95 135 ms over 100 calls.
- Adaptive-1/4: 12/20 successes; 3/20 human takeovers; inference p95 149 ms over 100 calls.
- Mechanism: an invented confidence gate selects one action under low confidence and four otherwise.
- Training boundary: checkpoint comes from one fictional training run over 800 teleoperation trajectories from one arm and fixed camera; train/evaluation scene overlap is unknown.
- Missing: significance test, multiple training seeds, energy, other robots, real deployment, and causal linkage between latency and rollout failure.
