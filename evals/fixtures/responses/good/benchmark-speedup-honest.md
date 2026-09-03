The new inference kernel (v2.1) is faster than the tuned baseline (v1.9) at every batch size, with a geometric-mean throughput speedup of 1.83× across the four batch sizes. The best case is up to 3.10× at batch 128 against that 1.83× geometric mean; the worst case is 1.12× at batch 1, where p99 latency regressed. All timings are the median of 20 runs after 5 warm-up runs on one A100 80GB with CUDA 12.4. The baseline was retuned for this hardware and measured 8% faster than its published numbers, so the comparison is against the stronger configuration. The table gives the per-batch results.

| Batch size | Throughput speedup (↑) | p99 latency change (↓) |
|---|---:|---|
| 1 | 1.12× | 4.1 ms → 4.6 ms (regression) |
| 8 | 1.35× | fell |
| 32 | 2.40× | fell |
| 128 | 3.10× | fell |
| Geometric mean | 1.83× | — |

The speedup grows with batch size, so the 3.10× figure describes large-batch offline throughput and not the batch-1 online path, where the kernel trades a 0.5 ms p99 regression for a 12% throughput gain.
