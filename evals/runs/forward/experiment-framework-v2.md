# Benchmark accuracy–latency trade-off

**Main result.** Method B has the highest observed mean accuracy, while Method C is only 0.1 percentage points lower and has the lowest latency, 9 ms below B. The measurements therefore show a trade-off rather than a universal winner.

**Research question.** How do Methods A–C compare on accuracy and latency?

**Metrics and protocol.** Accuracy is higher-is-better and is reported as the mean ± standard deviation (SD) across five seeds; latency is lower-is-better. The table reports all supplied measurements for the three methods.

| Method | Accuracy, mean ± SD across 5 seeds (%) ↑ | Latency (ms) ↓ |
|:---|---:|---:|
| A | 72.4 ± 1.1 | 31 |
| B | 74.0 ± 1.0 | 38 |
| C | 73.9 ± 0.9 | 29 |

*Table note: ↑ indicates higher-is-better; ↓ indicates lower-is-better. `±` denotes SD across the five accuracy seeds.*

**Conclusion.** On the observed point estimates, B provides the highest accuracy mean, whereas C gives nearly the same mean accuracy with 9 ms lower latency. C also has a 1.5-percentage-point higher mean accuracy and 2 ms lower latency than A. Thus, B is the point-estimate choice only when the additional 0.1 percentage point over C is preferred despite the latency cost; C offers the stronger observed accuracy–latency balance when latency matters.

**Evidence boundary.** No significance test was run, so the observed 0.1-percentage-point accuracy gap between B and C supports no claim of a statistical difference. These results are descriptive and do not establish causality or a universal winner.
