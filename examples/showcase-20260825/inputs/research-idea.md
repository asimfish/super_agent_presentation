# Synthetic evidence pack: research-idea

- Nature: untested synthetic idea; no literature, pilot run, or result is supplied.
- Problem statement: a learned controller may issue unsafe actions under visual corruption.
- Proposed mechanism: an action-conditioned latent predictor estimates uncertainty; a gate defers high-uncertainty actions to a conservative controller.
- Candidate baselines: learned controller without gate; uncertainty gate with shuffled uncertainty; conservative controller only.
- Candidate outcome families: task success, unsafe-action count, deferral rate, and control latency.
- Unknown: calibration quality, novelty, compute cost, and whether uncertainty predicts unsafe actions.
