# Synthetic facts: transfer

This is an invented teaching dataset, not a real experiment or literature claim.
The question is whether contrastive training improves transferable retrieval
representations. The working hypothesis predicts gains on both the in-domain and
shifted corpora under this protocol.

The baseline and contrastive variant share encoder size, training-step budget,
training data, retrieval depth, and evaluation populations. They differ in the
training objective. Five seeds per configuration; values are means with SD across
seeds. NDCG@10 is unitless and higher is better. No significance test or per-seed
values are supplied. Selection, leakage checks, and failed-run accounting are
not supplied; broader reproducibility and generalization are unverified.

| Method | In-domain NDCG@10, mean ± SD | Shifted NDCG@10, mean ± SD |
|---|---:|---:|
| Baseline | 0.410 ± 0.008 | 0.360 ± 0.012 |
| Contrastive | 0.450 ± 0.010 | 0.330 ± 0.011 |

No mechanism experiment or intervention on positive-pair domain composition has
been performed. A test changing pair composition is a possible new proposal,
not an observation in this fact sheet.
