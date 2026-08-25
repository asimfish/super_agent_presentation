# Synthetic evidence pack: risk-report

- Nature: synthetic risk fixture; not a real deployment assessment.
- Objective/horizon: evaluate a hypothetical model rollout over its first 30 days.
- Scale: likelihood is Low/Medium/High; impact is Low/Medium/High; ratings are ordinal, not probabilities.
- R1: training/evaluation overlap is unknown; event is inflated evaluation; consequence is an unsupported rollout decision. Likelihood Medium, impact High, confidence Low. Owner: Evaluation role. Trigger: overlap audit finds any shared record.
- R2: input drift may lower accuracy after launch. Likelihood Medium, impact Medium, confidence Medium. Owner: Monitoring role. Trigger: weekly accuracy proxy drops by 3 percentage points.
- R3: rollback artifact may be unavailable. Likelihood Low, impact High, confidence Medium. Owner: Release role. Trigger: rollback rehearsal fails.
- Existing controls: held-out manifest for R1; drift dashboard for R2; artifact checksum for R3.
- Not measured: real traffic frequency, financial impact, or calibrated probabilities.
