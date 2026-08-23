# Super Agent Presentation — project contract

## Outcome

An installable, agent-native reporting system intended to make task handoffs more
consistent, readable, evidence-aware, and proportional to the task. It must support
long work sessions without keeping a large reporting manual in active context.

## Acceptance criteria

- A repository-level contract provides a persistent activation reminder in
  supported agent hosts, while a link-only bootstrap remains available with an
  explicit best-effort warning.
- One lean Agent Skill routes a task to exactly one primary report mode and only the
  display modules it needs.
- Modes cover concise answers, implementation handoffs, status updates,
  investigations, experiments, decisions, academic synthesis, and reviews.
- Dedicated modules govern figures/images, quantitative tables, conclusions,
  evidence, and academic-paper presentation.
- A standard-library-only CLI can route, scaffold, checkpoint, bundle, and audit a
  report; its behavior is tested.
- Activation evals include at least two positive and two adjacent negative cases.
- Evaluation protocols for baseline comparison and long-context stress are
  recorded; checked-in forward runs are development-only and do not establish
  effectiveness.
- The skill passes structural validation, repository tests, security review, and a
  fresh-agent user journey.
- The public GitHub repository is created and pushed under the requested name.

## Milestones

| Milestone | Exit evidence | Status |
|---|---|---|
| M1 Research and architecture | Source notes, trade-off matrix, ADRs | Completed |
| M2 Canonical framework | Skill, protocols, modules, adapters, CLI | Completed |
| M3 Evaluation | Unit tests, declarative activation contract, route/fixture smoke, fresh-agent development record; comparative effectiveness remains unclaimed | Completed for v0.1 structural scope |
| M4 Release | Validation, review, commit, public GitHub URL | Pending |

## Decisions

- D1: Use a three-layer bookend architecture: tiny persistent contract, routed
  on-demand skill context, deterministic final audit. See ADR-001.
- D2: Use one primary report spine plus zero to two orthogonal display modules,
  rather than a universal report template. See ADR-002.
- D3: Keep the canonical skill host-neutral; ship host-specific adapters as optional
  installation material.
- D4: Offer a structured report IR and deterministic renderer only as a strict path
  for durable or wrapper-controlled reports. See ADR-003.

## Risks and controls

| Risk | Consequence | Control |
|---|---|---|
| A long always-on prompt consumes context | Slower, less focused task work | Keep persistent contract under a small fixed budget; defer detail |
| A pure on-demand skill is not invoked | Inconsistent final reports | Repository/user rule requests activation at long-task start and the report boundary |
| One template is forced onto every task | Bloated or unnatural output | Route to one primary mode; allow concise mode and explicit user override |
| Lint is mistaken for semantic verification | False confidence | Label audit as structural; require manual evidence and claim checks |
| Arbitrary link is treated as enforceable | Silent non-compliance | Document link-only as best effort; recommend installation for persistent prompting |
| External templates introduce license issues | Redistribution risk | Independently synthesize rules; cite ideas; do not copy restrictive assets |

## Current frontier

Close final review findings, verify a clean installation journey, publish the
reviewed commit, and reproduce the release gates from the public SHA. A future blind
baseline-versus-framework study remains separate from the v0.1 structural release.
