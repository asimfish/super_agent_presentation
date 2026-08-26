# Routed reporting bundle

Primary mode: `postmortem`
Research profile: `none`
Surface: `markdown`; audience: user
Display modules: none
Recommended exact templates: none
Required semantics: impact, timeline, cause, next_action
Must show: none specified
Read: `references/core-contract.md`, `modes/postmortem.md`


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
- Short single-session answers skip checkpoints, draft files, and audits.
- Deliver the report itself, never a file path, pointer, or scratch path.

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

# Postmortem

Use this mode after an incident to create a blameless, durable record of impact,
causes, response, learning, and owned prevention work. Do not use it as a substitute
for a live incident update.

## Semantic order

1. **Metadata:** incident date, report status, owner, audience, and relevant service
   or system boundary.
2. **Executive summary:** state impact, duration, trigger, root or contributing
   causes, and recovery at a decision-useful level.
3. **Impact:** quantify affected population, operations, data, SLOs, duration, or
   cost where evidence permits; label estimates and gaps.
4. **Timeline:** record decision-relevant detection, escalation, mitigation,
   recovery, and verification events with timestamps and timezones.
5. **Cause analysis:** distinguish trigger, proximate mechanism, root control gaps,
   contributing conditions, and factors that limited impact.
6. **Response analysis:** explain detection, recovery, communication, what worked,
   what did not, and where luck affected the outcome.
7. **Actions:** specify preventive and mitigative work with owner, priority, tracker,
   due state, and a verifiable completion condition.
8. **Lessons and residual risk:** state reusable learning and what remains exposed.

## Blameless analysis

- Describe what the system, process, interface, automation, or information allowed to
  happen. Do not reduce the cause to an individual's mistake.
- Assume responders acted with the information and constraints available at the
  time; analyze how those conditions can be improved.
- Include counterevidence and competing causes when the root-cause account remains
  uncertain.
- Separate observed events from hindsight interpretation.

## Action quality

Avoid vague actions such as `improve`, `be careful`, or `train everyone` without an
observable end state. Prefer controls that prevent recurrence, bound blast radius,
shorten detection, accelerate mitigation, or improve verification. Give every
accepted action a single accountable owner or role and a tracking mechanism.

## Avoid

- Writing a postmortem before evidence is stable while presenting it as final.
- Omitting impact because an exact number is unavailable; provide a bounded estimate
  or name the measurement gap.
- A detailed timeline with no causal analysis.
- Action items that only address people while leaving the enabling system unchanged.
- Declaring recurrence impossible or risk eliminated.
