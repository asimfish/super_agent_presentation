# Synthetic evidence pack: embodied-ai

- Nature: synthetic embodied-AI fixture; not a real robot study.
- Task: tabletop pick-and-place; success requires the object remain inside a 5 cm target zone for 3 s within 90 s.
- Embodiment: `SyntheticArm-A`, 7-DoF arm, parallel gripper, overhead RGB-D camera, joint state; delta-pose action.
- Simulation: `SyntheticSim 1.0`, 20 Hz control, 40 independent trials, 30 successes, zero safety stops.
- Real protocol: fictional lab rig, 10 Hz control, 10 independent trials, 7 successes, 2 operator safety stops; each safety stop counts as failure.
- Resets: fixed scripted reset; no retries; initial poses sampled from the fixture's bounded set.
- On-device latency over 50 real control decisions: median 62 ms, p95 91 ms; no per-trial latency linkage.
- Statistics: Wilson 95% intervals may be reported for success proportions; no independent training seeds or significance test.
- Unknown: energy, hardware-failure rate, broader objects/scenes, and training/evaluation overlap.
