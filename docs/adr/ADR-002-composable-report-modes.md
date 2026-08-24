# ADR-002: Compose one report mode with bounded display modules

- Status: Accepted
- Date: 2026-08-24

## Context

An experiment result, code handoff, literature synthesis, and one-line factual answer
do not share a useful full template. Nevertheless, they share outcome, evidence,
boundary, and action primitives. Figures and tables are evidence representations,
not report types.

## Decision

Select exactly one primary report mode. Prefer one display module and add a second
only for a distinct need that the mode and first module do not already cover. A mode
may declare a generic module capability as embedded so automatic routing does not
retrieve duplicate instructions. Explicit user formatting wins. Default to the
shortest mode that preserves evidence and decision usefulness.

## Consequences

- Reports remain recognizable without becoming uniform or bloated.
- Routers and evals can test a finite set of behaviors.
- Cross-cutting display guidance stays consistent across report types.
- Mixed requests require selecting one primary narrative spine instead of merging
  multiple full templates.
