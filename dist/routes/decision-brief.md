# Routed reporting bundle

Primary mode: `decision-brief`
Surface: `markdown`; audience: user
Display modules: none
Required semantics: decision, evidence, options, boundary, next_action
Must show: none specified
Read: `references/core-contract.md`, `modes/decision-brief.md`


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

Before handoff, manually confirm that the top line matches the actual terminal
state, evidence supports each consequential claim, exceptions are visible, links
resolve, and the report does not overstate what structural lint can prove. The
audit can check form; it cannot verify scientific truth, citation correctness,
causality, or visual appropriateness.


## Primary mode protocol

# Decision brief

Use this mode when the reader must choose, approve, defer, or revisit a consequential
option. Make the decision easy to locate without hiding uncertainty or trade-offs.

## Semantic order

1. **Recommendation or decision:** state the proposed or accepted choice and status.
2. **Context:** define the problem, scope, constraints, and decision deadline.
3. **Decision drivers:** list the criteria that materially distinguish options.
4. **Options considered:** compare credible alternatives on the same criteria,
   including the option to defer when relevant.
5. **Rationale:** connect evidence and drivers to the choice.
6. **Consequences:** state benefits, costs, trade-offs, dependencies, and risks.
7. **Confidence and revisit conditions:** name uncertainty and evidence that would
   trigger reconsideration.
8. **Action:** identify the decision owner, implementation owner, or next approval
   step only when known.

## Decision discipline

- Distinguish an accepted decision from an agent recommendation.
- Use a status such as proposed, accepted, deferred, rejected, or superseded when a
  durable record is needed.
- Explain why the non-selected options were not chosen; do not construct obviously
  weak alternatives to make the preferred option look inevitable.
- Keep factual evidence, value judgment, and preference separate.
- State confidence qualitatively with rationale unless a calibrated quantitative
  probability exists.
- Preserve consequences that weaken the preferred option.
- For a durable decision record, do not silently rewrite an accepted historical
  decision; link a later superseding decision.

## Comparison display

Use a table only when options share stable decision criteria. Avoid a weighted total
unless weights and scoring anchors were agreed in advance. A simple pros-and-cons
list is often clearer than pseudo-precise scoring.

## Avoid

- Burying the recommendation after background.
- Presenting a recommendation as authorization to act.
- Claiming consensus, owner, deadline, or approval that was not established.
- Omitting a material cost, reversibility concern, or dependency.
- Ending with a generic recommendation that is not connected to the evaluated
  options.
