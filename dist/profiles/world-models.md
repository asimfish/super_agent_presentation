# Research profile: world-models

# World-model research profile

Load this profile when a learned dynamics/world model is a contribution, controller,
simulator, representation, or evaluation target. State the role before presenting
results.

## Model and data card

Identify observation encoder/representation, transition dynamics, action
conditioning, reward/continuation heads, decoder when present, imagination or
planning horizon, controller/planner, training data policy, online/offline mixture,
environment-step budget, replay ratio, model size, and compute. Clarify which
components receive gradients from which objectives.

## Evaluation layers

Keep these evidence layers separate:

1. **Open-loop prediction:** conditioning context, rollout horizon, teacher forcing,
   stochastic samples, perceptual/dynamics metrics, and error growth.
2. **Closed-loop control or planning:** real-environment interaction budget, task
   return/success, replanning frequency, and policy/planner resources.
3. **Representation or transfer:** frozen/fine-tuned components, downstream data,
   adaptation budget, and target distribution.

Open-loop visual quality does not by itself prove control utility. Closed-loop task
success does not isolate which world-model component caused the gain.

## Result displays

- Separate prediction, control, scaling, and transfer tables.
- For scaling, show model/data/compute axes and matched-budget comparisons.
- Show horizon-conditioned error or consistency curves when long-rollout behavior
  matters.
- Include ablations that target the proposed mechanism and report model exploitation,
  compounding error, or off-distribution failure when observed.

Provenance IDs: WM-1 DreamerV3 evaluation and compute disclosure; WM-2 TD-MPC2
multi-domain/multi-task evaluation; WM-3 original World Models framing. See
the portable `UPSTREAM.md`; the source repository's detailed adoption ledger is
`docs/TEMPLATE-SOURCES.md`.
