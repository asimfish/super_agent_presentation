# Synthetic facts: compute attribution

Invented teaching facts. The research question is whether memory retrieval itself
lowers perplexity. Same backbone, training data, held-out corpus, and prompt set.
The method adds memory and doubles the inference token budget at the same time.
Three seeds per configuration. Reported values are means; variability and
per-seed results are unavailable. Perplexity is unitless and lower is better.

| Method | Perplexity, mean | Relative inference token budget |
|---|---:|---:|
| Baseline, no memory | 36.0 | 1× |
| With memory | 32.0 | 2× |

No matched-budget memory ablation, no no-memory 2× arm, and no significance test
have been run. The proposed mechanism is retrieval of relevant context, not a
verified causal result. Other selection/leakage/run-accounting details are unknown.
