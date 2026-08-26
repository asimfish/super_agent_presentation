# Catalog: modes, modules, profiles, surfaces, and templates

Authoritative inventory of everything `reportctl` can route to. This file is
generated from `reportctl list --json` and `reportctl template --list --json`;
regenerate it when those outputs change rather than editing numbers by hand.

An agent never loads this whole catalog at report time: routing selects exactly
one primary mode, at most one research profile, preferably one display module
(at most two), one surface guide only when needed, and retrieves at most one
exact template asset separately.

## Primary modes (12)

| Mode | Summary | Bounded route | Finished example |
|---|---|---|---|
| `concise-answer` | A direct, proportional answer for a bounded question or small handoff. | [route](../dist/routes/concise-answer.md) | [example](../examples/showcase-20260825/modes/concise-answer.md) |
| `implementation-handoff` | A completed, partial, or blocked engineering handoff with verification and changed artifacts. | [route](../dist/routes/implementation-handoff.md) | [example](../examples/showcase-20260825/modes/implementation-handoff.md) |
| `status-update` | A time-bounded progress report that separates completed work, active work, blockers, and next priorities. | [route](../dist/routes/status-update.md) | [example](../examples/showcase-20260825/modes/status-update.md) |
| `investigation-report` | A findings-first account of a diagnosis, analysis, or research investigation. | [route](../dist/routes/investigation-report.md) | [example](../examples/showcase-20260825/modes/investigation-report.md) |
| `experiment-report` | A reproducible experimental report with protocol, quantitative results, uncertainty, and bounded conclusions. | [route](../dist/routes/experiment-report.md) | [example](../examples/showcase-20260825/modes/experiment-report.md) |
| `decision-brief` | A decision-ready brief that states the recommendation, alternatives, trade-offs, confidence, and revisit conditions. | [route](../dist/routes/decision-brief.md) | [example](../examples/showcase-20260825/modes/decision-brief.md) |
| `academic-synthesis` | A source-grounded synthesis of one or more scholarly works, with claims, evidence, disagreements, and limits kept distinct. | [route](../dist/routes/academic-synthesis.md) | [example](../examples/showcase-20260825/modes/academic-synthesis.md) |
| `research-idea` | A testable research proposal that separates verified motivation from hypothesis, novelty, decisive evaluation, and kill criteria. | [route](../dist/routes/research-idea.md) | [example](../examples/showcase-20260825/modes/research-idea.md) |
| `review-report` | An evidence-driven review of code, a document, a design, or a scholarly work, ordered by actionable significance. | [route](../dist/routes/review-report.md) | [example](../examples/showcase-20260825/modes/review-report.md) |
| `incident-update` | A timestamped live-incident update centered on impact, current state, mitigation, and the next communication point. | [route](../dist/routes/incident-update.md) | [example](../examples/showcase-20260825/modes/incident-update.md) |
| `postmortem` | A blameless record of incident impact, timeline, causes, response, and owned preventive actions. | [route](../dist/routes/postmortem.md) | [example](../examples/showcase-20260825/modes/postmortem.md) |
| `risk-report` | A prioritized risk assessment with explicit rationale, controls, ownership, triggers, and residual exposure. | [route](../dist/routes/risk-report.md) | [example](../examples/showcase-20260825/modes/risk-report.md) |

## Display modules (5)

| Module | Summary |
|---|---|
| `visuals` | Select, caption, describe, and validate figures, charts, screenshots, diagrams, or qualitative image sets. |
| `tables` | Present exact values, comparisons, settings, registers, or audit details in compact and accessible tables. |
| `conclusions` | Calibrate conclusions, separate observation from inference, and state scope, confidence, trade-offs, and action. |
| `evidence` | Bind consequential claims to inspectable sources or artifacts and preserve uncertainty and provenance. |
| `academic-display` | Display scholarly identity, thesis, method, claim-evidence links, limitations, and relationships without fabricating literature claims. |

## Research profiles (4)

| Profile | Summary | Finished example |
|---|---|---|
| `reinforcement-learning` | RL protocol, run accounting, tuning parity, interval estimates, learning curves, and aggregate evaluation. | [example](../examples/showcase-20260825/profiles/reinforcement-learning.md) |
| `embodied-ai` | Embodiment, sensors/actions, sim-versus-real protocols, success definitions, interventions, generalization, and failure taxonomy. | [example](../examples/showcase-20260825/profiles/embodied-ai.md) |
| `world-models` | World-model roles, data/model cards, open-loop prediction, closed-loop control, scaling, transfer, and exploitation boundaries. | [example](../examples/showcase-20260825/profiles/world-models.md) |
| `vla` | VLA data mixtures, morphology and action interfaces, adaptation regimes, rollout accounting, generalization, latency, and safety. | [example](../examples/showcase-20260825/profiles/vla.md) |

## Surfaces (5)

`chat`, `markdown`, `issue-pr`, `document`, `slide`

Surface guides are loaded only when the delivery surface needs one (for
example the slide guide for academic talks).

## Exact template assets (10)

Templates never enter a bounded route bundle; retrieve exactly one with
`reportctl template <id> --output <path>` after routing.

| Template | Summary | Compatible modes | Surfaces |
|---|---|---|---|
| `experiment-report-detailed` | Detailed general experiment report with claim map, protocol, metrics, uncertainty, results, and reproducibility pointers. | `experiment-report` | chat, markdown, document |
| `research-idea` | Paper/research idea brief with closest-work comparison, decisive experiment, falsifier, risks, and evaluation gates. | `research-idea` | chat, markdown, document |
| `rl-experiment-report` | RL experiment report with environment protocol card, run/tuning accounting, aggregate statistics, and failure tasks. | `experiment-report` | chat, markdown, document |
| `embodied-experiment-report` | Embodied experiment report for sim/real protocols, success rules, generalization axes, interventions, and failure taxonomy. | `experiment-report` | chat, markdown, document |
| `world-model-experiment-report` | World-model report separating prediction, control, scaling, transfer, and failure evidence. | `experiment-report` | chat, markdown, document |
| `vla-experiment-report` | VLA report covering dataset mixtures, action interfaces, rollout protocols, generalization, deployment, and safety. | `experiment-report` | chat, markdown, document |
| `academic-talk-html` | Dependency-free, responsive, printable HTML/PPT-style academic talk with accessible assertion-evidence layouts. | `academic-synthesis`, `experiment-report`, `research-idea`, `status-update` | slide |
| `academic-talk-revealjs` | Quarto Reveal.js academic-talk source with citations, notes, self-contained HTML output, and appendix structure. | `academic-synthesis`, `experiment-report`, `research-idea`, `status-update` | slide |
| `sbar-handoff` | SBAR-structured operational handoff or escalation: situation, background, assessment, and a time-bound recommendation with contingency. | `incident-update`, `status-update` | chat, markdown, issue-pr |
| `executive-onepager` | Pyramid-structured executive one-pager: governing-thought title, two to four evidence-backed reasons, costs and revisit triggers, decision requested. | `decision-brief`, `status-update` | markdown, document |

Template provenance and adaptation boundaries are documented in
[TEMPLATE-SOURCES.md](TEMPLATE-SOURCES.md); communication-standard provenance is
in [REPORTING-STANDARDS.md](REPORTING-STANDARDS.md). Audit-clean finished
examples for `sbar-handoff` and `executive-onepager` live in
[examples/templates-20260826/](../examples/templates-20260826/README.md).
