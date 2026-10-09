# Routed reporting bundle

Primary mode: `experiment-report`
Research profile: `none`
Surface: `markdown`; audience: user
Display modules: none
Recommended exact templates: experiment-report-detailed
Required semantics: question, method, metrics, uncertainty, boundary
Must show: none specified
Read: `references/core-contract.md`, `modes/experiment-report.md`
Exemplar: run `reportctl exemplar experiment-report` before drafting


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

# Experiment report

Use this mode for benchmarks, ablations, controlled evaluations, model comparisons,
or empirical studies. Organize around research questions, not run order.

## Scientific argument

Lead with the answer to a research question, not a list of improved metrics.
Name the uncertainty, assumption, or limitation it addresses. A useful result can
narrow a hypothesis or rule out a route without improving a score.

For each main finding, connect the discriminating comparison to an interpretation
and scope. Say what changed in the working view and what remains unresolved.
Separate a measured effect from a proposed mechanism; an ablation can isolate a
component's contribution without establishing why it works. Name the strongest
plausible competing explanation when material; do not invent one to fill a slot.

Give the reader the comparison and practical consequence, not a recital of cells.
Keep counterexamples and decisive controls in the main reading path. Move full
sweeps, logs, and reproducibility detail to an appendix; omission must not hide
contradictory evidence or weaken the comparison basis.

End with a position, including "unresolved". If needed, propose a discriminating test:
what changes, what stays fixed, and how different outcomes change the decision.
"More seeds" addresses uncertainty; it does not by itself identify a mechanism.

## Semantic order

Finding/question -> decisive comparison -> interpretation/counterevidence ->
bounded conclusion -> next test if needed. Methods needed to read evidence go
beside it; full detail can follow. These are roles, not mandatory headings.

## Metric and uncertainty contract

For material metrics, make direction, unit, population/denominator, aggregation,
independent run count, and variability source/interval (SD, SEM, CI, quantiles)
recoverable. Define unfamiliar metrics only. Explain interval computation when
it affects interpretation. Statistical significance needs a stated analysis;
practical importance needs a research or decision criterion.

## Comparability and selection

- Rank only comparable protocols; disclose material data, supervision,
  pretraining, compute/hardware, tuning, test-time, and privileged-access differences.
- State hyperparameter, checkpoint, prompt, seed, and run selection. Account for
  exclusion counts/reasons and failed runs; never compare a best with a baseline mean.
- Distinguish zero, missing, not reported, failed, and not applicable.
- Disclose split construction, train-only preprocessing, duplicate/temporal
  checks, and pretrained contamination checks. "Not checked" is a valid status;
  an unresolved leak prevents an unqualified performance claim.

## Analysis discipline

- Separate descriptive, diagnostic, predictive, causal, and deployment claims.
- Untested uncertainty does not establish a winner or equivalence.
- Opposing metrics require a trade-off; a single ranking needs a stated utility,
  budget, or threshold. Name the closest relevant baseline before attributing gains.

## Avoid

- Metric recitation, unexplained boldface, or a leaderboard of incompatible tasks.
- A causal story inferred from a score increase; significance used as importance.
- state of the art without a verified benchmark and comparison set.
- Conclusions broader than the tested data, runs, or deployment conditions.
