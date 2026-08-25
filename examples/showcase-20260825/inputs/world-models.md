# Synthetic evidence pack: world-models

- Nature: untested synthetic world-model idea; no literature or experiment is supplied.
- Proposed role: action-conditioned latent dynamics model used for receding-horizon control.
- Proposed horizons: H in {5, 10, 20, 40} latent steps; replan every 5 real steps.
- Mechanism hypothesis: multi-step consistency plus an error-aware refresh gate reduces compounding rollout error at longer horizons.
- Candidate prediction metrics: horizon-conditioned latent error and decoded observation error.
- Candidate control metrics: episodic return and constraint violations, evaluated separately from open-loop prediction.
- Candidate baselines: one-step latent model; multi-step model without refresh gate; model without action conditioning; reactive policy without world model.
- Unknown: novelty, model size, compute, data distribution, calibration, and whether lower prediction error improves control.
