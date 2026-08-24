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
  investigations, experiments, decisions, risks, incidents, postmortems, academic
  synthesis, and reviews.
- Dedicated modules govern figures/images, quantitative tables, conclusions,
  evidence, and academic-paper presentation.
- A standard-library-only CLI can route, scaffold, checkpoint, bundle, and audit a
  report; a long-task final audit can derive mode and bounded literal anchors from
  the same schema-v2 checkpoint, and its behavior is tested.
- Activation evals include at least two positive and two adjacent negative cases.
- Evaluation protocols for baseline comparison and long-context stress are
  recorded; checked-in forward runs are development-only and do not establish
  effectiveness.
- A standard-library-only study controller freezes plans and inputs, ingests
  immutable generation records and artifacts, produces blinded A/B packets,
  freezes owner-only independent ratings, aggregates at the case level, and blocks
  claims when design prerequisites or metric gates are absent.
- A typed Codex host adapter separates side-effect-free planning from an explicit
  `host-run --execute` boundary, pins the executable and installed framework
  receipts, avoids a shell, and records unsupported provider controls honestly.
- The skill passes structural validation, repository tests, security review, and a
  fresh-agent user journey.
- The public GitHub repository is created and pushed under the requested name.

## Milestones

| Milestone | Exit evidence | Status |
|---|---|---|
| M1 Research and architecture | Source notes, trade-off matrix, ADRs | Completed |
| M2 Canonical framework | Skill, protocols, modules, adapters, CLI | Completed |
| M3 Evaluation | Unit tests, declarative activation contract, route/fixture smoke, fresh-agent development record; comparative effectiveness remains unclaimed | Completed for v0.2 structural scope |
| M4 Release | Validation, review, commit, public GitHub URL | Completed |
| M5 Study mechanics and real-host pilot | Schemas, private controller, typed host adapter, blind/rating pipeline, non-claiming one-pair pilot | Completed for v0.3 integration scope |
| M6 Preregistered effectiveness study | External baseline isolation, private heldout matrix, fixed revisions, long-context telemetry, frozen blind ratings, passing claim gates | Not started |

## Decisions

- D1: Use a three-layer bookend architecture: tiny persistent contract, routed
  on-demand skill context, and deterministic final audit against the same checkpoint
  for long work. See ADR-001 and ADR-005.
- D2: Use one primary report spine plus zero to two orthogonal display modules,
  rather than a universal report template. See ADR-002.
- D3: Keep the canonical skill host-neutral; ship host-specific adapters as optional
  installation material.
- D4: Offer a structured report IR and deterministic renderer only as a strict path
  for durable or wrapper-controlled reports. See ADR-003.
- D5: Keep deterministic evaluation separate from typed, opt-in host execution;
  pilots can validate integration but can never become effectiveness claims. See
  ADR-006.

## Risks and controls

| Risk | Consequence | Control |
|---|---|---|
| A long always-on prompt consumes context | Slower, less focused task work | Keep persistent contract under a small fixed budget; defer detail |
| A pure on-demand skill is not invoked | Inconsistent final reports | Repository/user rule requests activation at long-task start and the report boundary |
| Saved reporting intent drifts or is omitted at finalization | Long-task handoff loses a known requirement | Fingerprint schema-v2 intent and audit normalized literal anchors against the same checkpoint; retain manual semantic checks |
| One template is forced onto every task | Bloated or unnatural output | Route to one primary mode; allow concise mode and explicit user override |
| Lint is mistaken for semantic verification | False confidence | Label audit as structural; require manual evidence and claim checks |
| Arbitrary link is treated as enforceable | Silent non-compliance | Document link-only as best effort; recommend installation for persistent prompting |
| External templates introduce license issues | Redistribution risk | Independently synthesize rules; cite ideas; do not copy restrictive assets |
| Same-account baseline can still inherit global instructions or credentials | Contaminated comparison and false causal attribution | Permit it only for pilots; require an external-sandbox receipt and audited shared global policy for public claims |
| Host execution uses credentials, network, and paid model services | Cost, privacy, or provider-side effects | Make planning inert; require literal `--execute`; pin executable identity; bound time and local evidence; keep raw runs private |
| A planned output-token budget is not enforced by the host | Conditions may have unequal effective budgets | Record `output_token_cap_enforced: false`; block strong budget-equivalence claims until the provider exposes an enforceable control |
| Caller labels an unpinned provider model as a revision | Apparent reproducibility without immutable model identity | Require verifiable multiple revisions for public eligibility and disclose unpinned pilot aliases |
| Transcript text is mistaken for checkpoint proof | Echoes or commands could overstate long-context compliance | Credit only successful exact commands; require a separate controller-side receipt for public compaction evidence |
| Repeats reuse one mutable worktree | Cross-run state contaminates nominally independent samples | Require a unique controller-locked workspace per public generation unit plus an external fresh-state receipt |

## Current frontier

The `v0.3.0` study mechanics and one-pair real-host pilot are complete at the
integration-evidence level. The pilot exposed a redundant experiment conclusion
module, now removed from automatic routing with a bundle-size regression. The next
frontier is M6: an externally isolated, preregistered, blind, private-heldout study.
The current Codex path still lacks both an enforced output cap and a verified
checkpoint-artifact receipt, so no general effectiveness or efficiency claim is
currently eligible.
