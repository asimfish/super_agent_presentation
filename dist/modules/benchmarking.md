# Display module: benchmarking

# Benchmarking module

Load this module when the report compares throughput, latency, speedup,
scalability, or resource efficiency across systems, configurations, or hardware.

## Protocol

- Evaluate the cost case, not only the benefit case; an optimization report
  without its overhead scenarios is selective benchmarking.
- Run and report the whole suite. A subset needs a stated reason, and per-item
  results accompany any aggregate score.
- The baseline is a tuned, current system. Disclose competitor configuration;
  when your measurement of a competitor disagrees with its published numbers,
  say so.
- Keep calibration and evaluation workloads disjoint.
- Declare warmup handling; report cold-start and steady-state separately when
  both matter. Report repetitions and variance; institutionalized medians
  (best of n is never reported) beat single runs.

## Aggregation and units

- Normalized ratios aggregate with the geometric mean; rates over a fixed total
  workload with the harmonic mean; the arithmetic mean is for raw times only.
- Never report `up to N×` alone; give the central tendency and the worst case,
  and state when the best case occurs.
- Keep the baseline in the denominator and never confuse percent with
  percentage points.
- Every ratio is accompanied by absolute numbers.
- For online-service latency, report a tail percentile (p99 or stricter) next
  to the mean; fan-out turns rare single-machine stragglers into the common
  user experience.

## Disclosure

- State platform (CPU/GPU model and count, memory, interconnect), software
  stack (OS, compiler, framework, runtime versions), and benchmark-suite
  version; scores across suite versions are not comparable.
- State numeric precision and the quantization method when applicable.
- Report throughput-latency as a curve or as points under a declared latency
  bound, not as a single unconstrained throughput number; batch sizes are
  matched or each system's optimum is disclosed.
- Report compute cost (device-hours, energy, or price) when efficiency is part
  of the claim, including failed and search runs where relevant.

## Avoid

- Microbenchmarks presented as overall performance.
- Best-case datasets or load ranges that stop where degradation begins.
- Throughput deltas presented as overhead without the accompanying load data.
- Comparing only against your own previous version.
