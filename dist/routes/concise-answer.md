# Routed reporting bundle

Primary mode: `concise-answer`
Research profile: `none`
Surface: `markdown`; audience: user
Display modules: none
Recommended exact templates: none
Required semantics: outcome, boundary
Must show: none specified
Read: `references/core-contract.md`, `modes/concise-answer.md`


## Universal contract

# Core reporting contract

Apply this contract with one primary mode and at most two display modules.
Headings in a mode or template are semantic roles, not mandatory English labels.
Write in the user's language; an explicit user-supplied format wins.

## Reporting primitives

Build the report from the smallest useful subset of these primitives:

- **Outcome:** what changed, was learned, is currently true, or remains unresolved.
- **Evidence:** observations, measurements, sources, artifacts, or checks supporting
  the outcome.
- **Interpretation:** what the evidence permits the agent to infer.
- **Boundary:** uncertainty, limitations, exceptions, failed checks, and blockers.
- **Action:** the next decision, owner, verification step, or useful follow-up.

Do not force all five into visible sections; keep their meaning even in a
one-sentence answer.

## Reader contract

1. Lead with the answer, status, finding, or decision. Do not make the reader
   reconstruct it from a chronology of work.
2. Give each visible section one job. Past about 2,000 characters, mark every
   semantic-role boundary with a heading or a bold lead-in sentence on any
   surface, chat included; omit that ceremony for bounded answers.
3. Pair each consequential claim with nearby evidence or an unambiguous evidence
   reference. Put detailed logs and large supporting data outside the main reading
   path.
4. State the comparison basis, scope, and time boundary before relying on them.
   State each boundary once, in its place; do not re-hedge every sentence.
5. End with an action only when action is useful. Do not add generic offers or
   recommendations unsupported by the work.

## Truth and status boundaries

- Distinguish `verified`, `observed`, `inferred`, `suspected`, `recommended`, and
  `unknown` when the distinction changes interpretation.
- Use `complete` only when the requested outcome and its material verification are
  complete. A rollback, partial build, passing unit suite, or drafted file does
  not erase a later failure or unmet acceptance criterion.
- Use `blocked` when progress requires a missing authority, dependency, credential,
  external state change, or user decision. Name the blocker and the smallest
  unblock action.
- Use `partial` or `incomplete` when useful work exists but required work remains.
- `zero`, `missing`, `not measured`, `not run`, and `not applicable` are different
  values.
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
- Prefer a single-column reading path; use a dashboard grid only for monitoring
  that benefits from parallel scanning.
- Use tables for exact lookup and audit detail, visuals for shape or relationship,
  prose for a few facts.
- Put commands, raw logs, full data, and extended methods in a linked artifact or a
  labeled collapsed section.
- Do not add a figure, table, diagram, alert, or summary section merely to make a
  short answer look formal.
- Short single-session answers skip checkpoints, draft files, and audits.
- Deliver the report itself, never a file path, pointer, or scratch path.

## Accessibility and safe presentation

- Give meaningful images concise alternative text and complex visuals an adjacent
  textual account of the essential data or trend.
- Emit auditable Markdown images at column zero as independent, single-line,
  top-level paragraphs bounded by blank lines or document boundaries; use
  percent-encoded targets when a path contains spaces or parentheses.
- Put auditable report images before raw triple-backtick/triple-tilde examples or
  paragraph-sensitive raw HTML tags; required credit stops at the first such
  marker, so link later logs instead. URI autolinks are not HTML markers.
- In literal examples, escape a Markdown image's leading bang (`\![...]`) and
  entity-encode a raw image tag (`&lt;img ...>`); the gate treats raw markers
  conservatively even inside code or comments.
- Do not use color, emoji, position, or typography as the only carrier of status or
  meaning.
- Keep table headers explicit and visual labels, units, legends, and scales
  readable in the delivered surface.
- Link to inspectable artifacts when safe. Never expose secrets, personal data,
  private logs, or exploit details in a reader-facing report.

## Final boundary check

For long work, final-audit its v2 checkpoint, not `--mode`. Put each rendered-text
anchor in one blank-line-bounded, column-zero prose paragraph. Soft breaks join;
blank lines and Markdown do not. Raw HTML errors and ends later credit. Entities
decode unless `&` has odd backslash parity. Literal presence is not truth.

Before handoff, verify current state, claims, evidence, exceptions, links, and
format yourself; the audit checks form, not truth, citations, causality, or visuals.


## Primary mode protocol

# Concise answer

Use this mode for a bounded question, a small factual handoff, or a direct status
answer that does not need a durable report. Proportionality is the defining rule.

## Required shape

1. State the answer or terminal status in the first sentence.
2. Add the one material qualifier, number, or evidence point needed to interpret it.
3. Add a next action only if the reader must act or the task remains incomplete.

Use no heading when one or two short paragraphs are clearer. A compact list is
appropriate only when the user asked for several distinct items.

## Content rules

- Preserve exact requested formats such as yes/no, a corrected sentence, or one
  value with its unit.
- Name a remaining gap when a positive answer could otherwise imply completion.
- State `unknown`, `not checked`, `partial`, or `blocked` instead of filling a gap
  with confidence language.
- Cite or link the source when the answer depends on an external fact or artifact
  and traceability matters.
- Prefer exact numbers over vague quantifiers when the numbers are verified.

## Avoid

- An executive summary, status table, diagram, or decorative image for a trivial
  answer.
- Repeating the question or narrating the work before answering.
- Generic next-step offers when no next step is needed.
- Turning a partial success into an unqualified `yes` or `complete`.

## Final check

Confirm that removing any sentence would either remove the answer, a material
boundary, or a useful action. If not, remove it.
