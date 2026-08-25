# Synthetic evidence pack: experiment-report

- Nature: synthetic showcase fixture; not a real benchmark.
- Task: one fixed 1,000-example classification split; accuracy is higher-is-better, denominator 1,000.
- Latency: milliseconds per example at batch 1; lower-is-better.
- Four independent training runs per method; report mean and sample SD across runs.
- Dense final-checkpoint runs: accuracy 84.0, 84.2, 83.8, 84.0%; latency 40, 41, 39, 40 ms.
- Pruned final-checkpoint runs: accuracy 83.5, 83.7, 83.4, 83.6%; latency 29, 30, 28, 29 ms.
- Same synthetic host and training budget; no significance test, confidence interval, energy measure, or external baseline.
