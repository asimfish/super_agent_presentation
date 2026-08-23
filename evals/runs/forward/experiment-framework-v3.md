# Accuracy–latency benchmark

## Main result

Method B has the highest observed accuracy mean, whereas Method C has the lowest reported latency and an accuracy mean only 0.1 percentage points below B. Accordingly, B and C represent an observed accuracy–latency trade-off; neither is universally preferable from these measurements alone.

## Research question and metrics

Under the supplied benchmark, how do Methods A, B, and C compare on accuracy and latency? The table reports accuracy as mean ± standard deviation across five seeds (higher is better) and latency in milliseconds (lower is better).

| Method | Accuracy, mean ± SD over 5 seeds (%) ↑ | Latency (ms) ↓ |
|:---|---:|---:|
| A | 72.4 ± 1.1 | 31 |
| B | 74.0 ± 1.0 | 38 |
| C | 73.9 ± 0.9 | 29 |

*Scope and notation:* ↑ means higher is better; ↓ means lower is better; ± denotes the standard deviation across five seeds for accuracy. No significance test was run, and no uncertainty or repetition count was supplied for latency.

## Calibrated conclusion

On the reported point estimates, B gains 0.1 percentage points of mean accuracy over C but incurs 9 ms more latency. C also exceeds A's mean accuracy by 1.5 percentage points while reducing latency by 2 ms, so C dominates A on the two reported point estimates. However, the accuracy uncertainties overlap and no significance test was performed; in particular, B and C cannot be declared statistically different. Without a user-specified utility function, latency budget, or minimum accuracy threshold, the evidence does not identify a single best trade-off: B is the conditional choice if only the highest observed accuracy mean matters, while C is the conditional choice if lower latency matters without sacrificing more than 0.1 percentage points of observed mean accuracy.
