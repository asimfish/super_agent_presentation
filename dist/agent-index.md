# Agent reporting index

Choose exactly one primary route and read no other route. Add at most one matching research profile, prefer one display module (at most two), and read a surface guide only when needed. Exact assets stay outside this bounded route context. Explicit user format wins.

## Primary routes

- [`concise-answer`](routes/concise-answer.md) — A direct, proportional answer for a bounded question or small handoff.
- [`implementation-handoff`](routes/implementation-handoff.md) — A completed, partial, or blocked engineering handoff with verification and changed artifacts.
- [`status-update`](routes/status-update.md) — A time-bounded progress report that separates completed work, active work, blockers, and next priorities.
- [`investigation-report`](routes/investigation-report.md) — A findings-first account of a diagnosis, analysis, or research investigation.
- [`experiment-report`](routes/experiment-report.md) — A reproducible experimental report with protocol, quantitative results, uncertainty, and bounded conclusions.
- [`decision-brief`](routes/decision-brief.md) — A decision-ready brief that states the recommendation, alternatives, trade-offs, confidence, and revisit conditions.
- [`academic-synthesis`](routes/academic-synthesis.md) — A source-grounded synthesis of one or more scholarly works, with claims, evidence, disagreements, and limits kept distinct.
- [`research-idea`](routes/research-idea.md) — A testable research proposal that separates verified motivation from hypothesis, novelty, decisive evaluation, and kill criteria.
- [`review-report`](routes/review-report.md) — An evidence-driven review of code, a document, a design, or a scholarly work, ordered by actionable significance.
- [`incident-update`](routes/incident-update.md) — A timestamped live-incident update centered on impact, current state, mitigation, and the next communication point.
- [`postmortem`](routes/postmortem.md) — A blameless record of incident impact, timeline, causes, response, and owned preventive actions.
- [`risk-report`](routes/risk-report.md) — A prioritized risk assessment with explicit rationale, controls, ownership, triggers, and residual exposure.

## Optional display modules

- [`visuals`](modules/visuals.md) — Select, caption, describe, and validate figures, charts, screenshots, diagrams, or qualitative image sets.
- [`tables`](modules/tables.md) — Present exact values, comparisons, settings, registers, or audit details in compact and accessible tables.
- [`conclusions`](modules/conclusions.md) — Calibrate conclusions, separate observation from inference, and state scope, confidence, trade-offs, and action.
- [`evidence`](modules/evidence.md) — Bind consequential claims to inspectable sources or artifacts and preserve uncertainty and provenance.
- [`academic-display`](modules/academic-display.md) — Display scholarly identity, thesis, method, claim-evidence links, limitations, and relationships without fabricating literature claims.

## Optional research profiles

Select at most one profile when the task is a domain research idea, experiment, investigation, review, status, or academic synthesis.

- [`reinforcement-learning`](profiles/reinforcement-learning.md) — RL protocol, run accounting, tuning parity, interval estimates, learning curves, and aggregate evaluation.
- [`embodied-ai`](profiles/embodied-ai.md) — Embodiment, sensors/actions, sim-versus-real protocols, success definitions, interventions, generalization, and failure taxonomy.
- [`world-models`](profiles/world-models.md) — World-model roles, data/model cards, open-loop prediction, closed-loop control, scaling, transfer, and exploitation boundaries.
- [`vla`](profiles/vla.md) — VLA data mixtures, morphology and action interfaces, adaptation regimes, rollout accounting, generalization, latency, and safety.

## Surface guides

- [`slide`](surfaces/slide.md) — Assertion-evidence academic talks for paper, progress, experiment, and idea presentations.

## Exact assets

Open exactly one compatible asset only after selecting it; assets are not part of the bounded route bundle.

- [`experiment-report-detailed`](../skills/agentic-reporting/assets/templates/experiment-report-detailed.md) — Detailed general experiment report with claim map, protocol, metrics, uncertainty, results, and reproducibility pointers.
- [`research-idea`](../skills/agentic-reporting/assets/templates/research-idea.md) — Paper/research idea brief with closest-work comparison, decisive experiment, falsifier, risks, and evaluation gates.
- [`rl-experiment-report`](../skills/agentic-reporting/assets/templates/rl-experiment-report.md) — RL experiment report with environment protocol card, run/tuning accounting, aggregate statistics, and failure tasks.
- [`embodied-experiment-report`](../skills/agentic-reporting/assets/templates/embodied-experiment-report.md) — Embodied experiment report for sim/real protocols, success rules, generalization axes, interventions, and failure taxonomy.
- [`world-model-experiment-report`](../skills/agentic-reporting/assets/templates/world-model-experiment-report.md) — World-model report separating prediction, control, scaling, transfer, and failure evidence.
- [`vla-experiment-report`](../skills/agentic-reporting/assets/templates/vla-experiment-report.md) — VLA report covering dataset mixtures, action interfaces, rollout protocols, generalization, deployment, and safety.
- [`academic-talk-html`](../skills/agentic-reporting/assets/presentations/academic-talk.html) — Dependency-free, responsive, printable HTML/PPT-style academic talk with accessible assertion-evidence layouts.
- [`academic-talk-revealjs`](../skills/agentic-reporting/assets/presentations/academic-talk-revealjs.qmd) — Quarto Reveal.js academic-talk source with citations, notes, self-contained HTML output, and appendix structure.
- [`sbar-handoff`](../skills/agentic-reporting/assets/templates/sbar-handoff.md) — SBAR-structured operational handoff or escalation: situation, background, assessment, and a time-bound recommendation with contingency.
- [`executive-onepager`](../skills/agentic-reporting/assets/templates/executive-onepager.md) — Pyramid-structured executive one-pager: governing-thought title, two to four evidence-backed reasons, costs and revisit triggers, decision requested.

Before delivery, manually verify facts, latest state, evidence, numbers, uncertainty, and the user's requested format. A repository link is not an installation or instruction-elevation mechanism.
