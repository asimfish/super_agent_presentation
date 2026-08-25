# Synthetic evidence pack: investigation-report

- Nature: synthetic showcase fixture; not production telemetry.
- Symptom: p99 inference latency rose from 480 ms to 920 ms in a controlled replay.
- Held constant: request corpus, concurrency 8, model build, and host.
- Observation A: queue wait rose from 35 ms to 310 ms; CPU stayed within 2 percentage points.
- Probe B: batch flush timer 250 ms reproduced 910 ms p99.
- Counterfactual C: timer 25 ms reduced p99 to 515 ms without changing the other held controls.
- Probe D: disabling response compression changed p99 by less than 5 ms.
- Not tested: a second host, real traffic, or long-duration memory behavior.
