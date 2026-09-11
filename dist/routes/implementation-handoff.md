# Routed reporting bundle

Primary mode: `implementation-handoff`
Research profile: `none`
Surface: `markdown`; audience: user
Display modules: none
Recommended exact templates: release-card
Required semantics: outcome, changes, verification, boundary, next_action
Must show: none specified
Read: `references/core-contract.md`, `modes/implementation-handoff.md`


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
2. Write for the reader's next decision, not for completeness. Omit what this
   reader already knows: do not define a metric an expert audience uses daily,
   do not list every absent detail when one sentence names the gap that matters.
   What a report leaves out shows judgment as much as what it keeps.
3. Give each visible section one job. Past about 2,000 characters, mark every
   semantic-role boundary with a heading or a bold lead-in sentence on any
   surface, chat included; omit that ceremony for bounded answers.
4. Pair each consequential claim with nearby evidence or an unambiguous evidence
   reference. Put detailed logs and large supporting data outside the main reading
   path.
5. State the comparison basis, scope, and time boundary before relying on them.
   State each boundary once, in its place; do not re-hedge every sentence.
6. State what is known and stop. Do not narrate the inferences you decline to
   make: "Recall was not reported" is complete; "Recall was not reported, so it
   cannot be read as zero or as untested" is commentary the reader did not need.
7. When the mode calls for a recommendation or decision, give one and name the
   condition that would flip it. Do not hand the reader a tree of if-then
   branches in place of a position.
8. End with an action only when action is useful. Do not add generic offers or
   recommendations unsupported by the work.

## Truth and status boundaries

These are working rules for the author, not sentences for the report.

- Distinguish verified, observed, inferred, suspected, recommended, and unknown
  when the distinction changes interpretation.
- Use complete only when the requested outcome and its material verification are
  complete. A rollback, partial build, passing unit suite, or drafted file does
  not erase a later failure or unmet acceptance criterion.
- Use blocked when progress requires a missing authority, dependency, credential,
  external state change, or user decision. Name the blocker and the smallest
  unblock action.
- Use partial or incomplete when useful work exists but required work remains.
- Zero, missing, not measured, not run, and not applicable are different values.
- Never invent a source, citation, number, test result, file, comparison, cause,
  owner, deadline, or completion claim.

## Quantitative claims

The reader must be able to recover, for each material number, the metric's
direction, unit, denominator or population, time window, comparison baseline,
number of independent observations, and what any interval means. Supply these
only where the reader could not otherwise recover them: an arrow in a table
header or one note beside the first table usually covers all of them. Do not
imply statistical, causal, practical, or state-of-the-art superiority from a
larger displayed number alone.

## Surface and proportionality

- Use chat for direct and compact handoffs; use a durable artifact when the user
  requests one or the report must stand alone.
- This protocol's own Markdown is not a model for the report's formatting. Write
  numbers, metric names, and status words in plain prose; reserve code spans for
  code, commands, paths, and identifiers.
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

- Give meaningful images concise alt text and complex visuals an adjacent textual
  account of the essential data or trend.
- Emit report images as standalone Markdown image paragraphs at column zero (blank
  lines around, one per line, percent-encode spaces and parentheses in targets),
  placed before any raw fenced-code example or raw HTML tag: the audit credits
  images only up to the first such marker; URI autolinks are not markers. In
  literal examples escape the image bang (`\![...]`) and entity-encode raw tags
  (`&lt;img ...>`).
- Never let color, emoji, position, or typography be the only carrier of meaning.
- Keep table headers explicit and visual labels, units, legends, and scales
  readable on the delivered surface.
- Link inspectable artifacts when safe; never expose secrets, personal data,
  private logs, or exploit details in a reader-facing report.

## Final boundary check

For long work, final-audit its v2 checkpoint, not `--mode`. Put each rendered-text
anchor in one blank-line-bounded, column-zero prose paragraph. Soft breaks join;
blank lines and Markdown do not. Raw HTML errors and ends later credit. Entities
decode unless `&` has odd backslash parity. Literal presence is not truth.

Before handoff, verify current state, claims, evidence, exceptions, links, and
format yourself; the audit checks form, not truth, citations, causality, or visuals.


## Primary mode protocol

# Implementation handoff

Use this mode after changing code, configuration, data, documentation, or another
project artifact. Report the real terminal state: complete, partial, or blocked.

## Semantic order

1. **Outcome:** state what now works or what prevented completion.
2. **Scope:** summarize user-visible behavior and the material artifacts changed.
3. **Verification:** list the checks run and their observed results.
4. **Boundary:** expose failed, skipped, unavailable, or out-of-scope checks and
   remaining risks.
5. **Handoff:** link the relevant files, commit, pull request, or generated artifact;
   name the next action only when work remains.

Rename or merge sections when the report remains easy to scan. For a tiny successful
edit, a short outcome sentence plus one verification bullet may be enough.

## Verification rules

- Identify the check, relevant scope, and result. Include a command only when it
  improves reproducibility or diagnosis.
- Distinguish unit, integration, static, security, build, and user-journey checks.
- Report the latest material failure even when earlier checks passed.
- Do not write all tests passed when only a subset ran. Do not infer runtime
  behavior from compilation or static inspection alone.
- If no check was run, state why and what remains unverified.

## Artifact rules

- Link to the smallest useful set of files or durable artifacts.
- Describe behavior rather than dumping a file list with no meaning.
- Keep raw diffs, complete logs, and generated output outside the main narrative.
- Preserve unrelated user changes; do not imply ownership of work not performed in
  this run.

## Completion language

Use complete only when the requested change exists and the material acceptance
path passed. Use partial when a useful change exists but required work remains.
Use blocked when a dependency, authority, credential, environment, or user choice
prevents progress, and state the smallest unblock action.

## Avoid

- A chronological diary of commands.
- Claims such as ready to ship without release-relevant evidence.
- Hiding a late integration failure below a success headline.
- Suggesting unrelated cleanup as if it were required to complete the task.
