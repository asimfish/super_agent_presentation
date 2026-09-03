Result: every component removal lowers success, and the gate accounts for the largest observed drop. Success is higher-is-better (↑), reported as mean success (%) with standard deviation over five seeds and 200 scenes per seed; every variant was tuned with the same 12-trial budget as the full system. The table lists each variant against the full-system reference row.

| Variant | Success (%, ↑) | SD (5 seeds) | Drop vs full (points) |
|---|---:|---:|---:|
| Full system | 84.2 | 1.9 | — |
| Without gate | 76.5 | 2.4 | −7.7 |
| Without noise schedule | 82.9 | 2.1 | −1.3 |
| Without data augmentation | 80.1 | 2.6 | −4.1 |

The gate carries the largest observed contribution (7.7 points), augmentation the second (4.1), and the noise schedule the smallest (1.3), which sits within about one standard deviation of the full system. Removing the gate and the augmentation together was not run, so the contributions cannot be treated as additive or independent; no significance test was run, so these are observed drops under a shared tuning budget, not tested differences.
