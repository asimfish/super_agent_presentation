# Routed reporting bundle

Primary mode: `research-idea`
Research profile: `none`
Surface: `markdown`; audience: user
Display modules: none
Recommended exact templates: research-idea
Required semantics: question, method, evidence, boundary, next_action
Must show: none specified
Read: `references/core-contract.md`, `modes/research-idea.md`


## Universal contract

# Core reporting contract

Apply this contract with exactly one primary mode and no more than two display
modules. Treat headings in a mode or template as semantic roles, not mandatory
English labels. Write in the user's language and follow an explicit user-supplied
format when it conflicts with the framework.

## Reporting primitives

Build the report from the smallest useful subset of these primitives:

- **Outcome:** what changed, was learned, is currently true, or remains unresolved.
- **Evidence:** observations, measurements, sources, artifacts, or checks supporting
  the outcome.
- **Interpretation:** what the evidence permits the agent to infer.
- **Boundary:** uncertainty, limitations, exceptions, failed checks, and blockers.
- **Action:** the next decision, owner, verification step, or useful follow-up.

Do not force all five into visible sections. Preserve their meaning even when a
short answer needs only one sentence.

## Reader contract

1. Lead with the answer, status, finding, or decision. Do not make the reader
   reconstruct it from a chronology of work.
2. Give each visible section one job. Use specific headings when a heading is
   useful; omit ceremony for bounded answers.
3. Pair each consequential claim with nearby evidence or an unambiguous evidence
   reference. Put detailed logs and large supporting data outside the main reading
   path.
4. State the comparison basis, scope, and time boundary before relying on them.
5. End with an action only when action is useful. Do not add generic offers or
   recommendations unsupported by the work.

## Truth and status boundaries

- Distinguish `verified`, `observed`, `inferred`, `suspected`, `recommended`, and
  `unknown` when the distinction changes interpretation.
- Use `complete` only when the requested outcome and its material verification are
  complete. A successful rollback, partial build, passing unit suite, or drafted
  file does not erase a later failure or unmet acceptance criterion.
- Use `blocked` when progress requires a missing authority, dependency, credential,
  external state change, or user decision. Name the blocker and the smallest
  unblock action.
- Use `partial` or `incomplete` when useful work exists but required work remains.
- Treat `zero`, `missing`, `not measured`, `not run`, and `not applicable` as
  different values.
- Never invent a source, citation, number, test result, file, comparison, cause,
  owner, deadline, or completion claim.

## Quantitative claims

When material, provide the metric definition, direction, unit, denominator or
population, time window, comparison baseline, number of independent observations,
and uncertainty definition. Do not imply statistical, causal, practical, or
state-of-the-art superiority from a larger displayed number alone.

## Surface and proportionality

- Use chat for direct and compact handoffs; use a durable artifact when the user
  requests one or the report must stand alone.
- Prefer a single-column reading path for reports. Use a dashboard grid only for a
  monitoring task that benefits from parallel scanning.
- Use tables for exact lookup and audit detail, visuals for shape or relationships,
  and prose for a small number of facts.
- Put commands, raw logs, full data, and extended methods in a linked artifact or a
  clearly labeled collapsed section when the surface supports it.
- Do not add a figure, table, diagram, alert, or executive-summary section merely
  to make a short answer look formal.

## Accessibility and safe presentation

- Give meaningful images concise alternative text; give complex visuals an
  adjacent textual account of the essential data, relationships, or trend.
- Emit auditable Markdown images at column zero as independent, single-line,
  top-level paragraphs bounded by blank lines or document boundaries; use
  percent-encoded targets when a path contains spaces or parentheses.
- Put auditable report images before raw triple-backtick/triple-tilde examples or
  paragraph-sensitive raw HTML tags. The conservative required-credit subset stops
  at the first such marker; link later logs/snippets instead. URI autolinks do not
  count as HTML tag markers.
- In literal examples, escape a Markdown image's leading bang (`\![...]`) and
  entity-encode a raw image tag (`&lt;img ...>`); the structural gate treats raw
  markers conservatively regardless of code or comment context.
- Do not use color, emoji, position, or typography as the only carrier of status or
  meaning.
- Keep table headers explicit and visual labels, units, legends, and scales
  readable in the delivered surface.
- Link to inspectable artifacts when safe. Do not expose secrets, personal data,
  private logs, or sensitive exploit details in a reader-facing report.

## Final boundary check

For long work, final-audit its v2 checkpoint, not `--mode`. Put each rendered-text
anchor in one blank-line-bounded, column-zero prose paragraph. Soft breaks join;
blank lines and Markdown do not. Raw HTML errors and ends later credit. Entities
decode unless `&` has odd backslash parity. Literal presence is not truth.

Before handoff, manually verify current state, claims, evidence, exceptions, links,
and format. The audit checks form, not truth, citations, causality, or visual fitness.


## Primary mode protocol

# Research idea brief

Use this mode to present, challenge, or decide whether to pursue a paper idea,
research hypothesis, or proposed empirical contribution. It is an argument for a
testable program, not an abstract for work that has already succeeded.

## Semantic order

1. **Thesis:** state the proposed change and intended outcome in one jargon-light
   sentence.
2. **Problem and current limit:** identify who or what is affected, how the problem
   is handled now, and the specific unresolved limitation.
3. **Hypothesis and mechanism:** state why the proposed intervention should change
   the measured outcome. Separate prior evidence from conjecture.
4. **Novelty delta:** compare against the closest approaches on an explicit axis;
   do not claim novelty from unfamiliar wording.
5. **Decisive evaluation:** define the smallest experiment that could support or
   falsify the hypothesis, including baselines, metrics, controls, and failure
   criteria.
6. **Risk and feasibility:** expose scientific, data, compute, implementation, and
   evaluation risks together with mitigations or kill criteria.
7. **Decision:** state the next evidence-producing step, resource envelope, and
   mid-point/final checks.

## Idea evidence contract

- Label observations from papers, preliminary runs, or existing artifacts as
  evidence and locate them.
- Label the proposed mechanism, expected result, and impact as hypotheses until
  tested.
- Name the closest alternatives before claiming a gap or novelty.
- Define what negative or null evidence would make the idea change or stop.
- Avoid fabricated expected gains, target venues, timelines, or implementation
  ease.

## Useful displays

- A one-row claim-to-test table: claim, intervention, control, metric, falsifier.
- A comparison matrix with explicit axes rather than a generic related-work list.
- A compact risk register when feasibility drives the decision.
- One mechanism diagram only when it makes the causal or computational proposal
  easier to inspect.

## Avoid

- Writing a future experiment as if it were a verified contribution.
- Defining the gap as “no one has combined A and B.”
- Treating an implementation plan as scientific evidence.
- Listing many experiments without identifying the decisive one.

Provenance: the question sequence is independently synthesized from the DARPA
Heilmeier Catechism and ML conference reproducibility/checklist criteria. See
`docs/TEMPLATE-SOURCES.md` in the repository for source links and boundaries.
