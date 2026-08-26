# Routed reporting bundle

Primary mode: `review-report`
Research profile: `none`
Surface: `markdown`; audience: user
Display modules: none
Recommended exact templates: none
Required semantics: findings, evidence, boundary, next_action
Must show: none specified
Read: `references/core-contract.md`, `modes/review-report.md`


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

# Review report

Use this mode to assess code, a change set, design, document, dataset, artifact, or
scholarly work. The review is evidence-driven and review-only unless the user also
authorizes fixes.

## Semantic order

1. **Verdict or findings:** put actionable problems first, ordered by material
   severity or decision impact. If no actionable finding survives review, say so.
2. **Scope:** identify the reviewed target, version or diff, criteria, and exclusions.
3. **Finding detail:** for each finding, give a stable ID, severity, confidence,
   locator, evidence, impact, and the smallest useful correction or question.
4. **Positive evidence:** note strengths when they affect the verdict or should be
   preserved; do not use praise to dilute a material finding.
5. **Coverage and boundary:** record tests or surfaces reviewed, areas not checked,
   rejected candidates, and residual uncertainty.
6. **Decision support:** state whether the evidence supports pass, conditional pass,
   revision, or block when the review context defines such a verdict.

## Finding discipline

- A finding must be specific, consequential, and supported by inspectable evidence.
- Describe severity through concrete impact and realistic reachability, not a label
  alone.
- Calibrate confidence from the evidence available and missing proof.
- Use precise locations such as file and line, section, page, table, figure, record,
  or timestamp.
- Do not combine independent issues merely to shorten the report.
- Do not invent a requirement. Connect criticism to the user's criteria, documented
  contract, accepted standard, or demonstrated harm.
- If an apparent issue is ruled out, include it only when the counterevidence matters
  to coverage or future review.

## Review variants

For scholarly review, keep the neutral summary separate from critique and assess
soundness, evidence, novelty context, clarity, limitations, and reproducibility.
For code or change review, emphasize correctness, regressions, security boundaries,
tests, API effects, and maintainability. For visual or document review, bind findings
to exact pages, figures, screenshots, or sections.

## No-finding reports

Do not claim the target is defect-free. State that no actionable finding was found
within the reviewed scope, then name material coverage or verification gaps.

## Avoid

- Generic comments that could apply to any target.
- Style preferences presented as defects without a governing convention or impact.
- A summary of changes in place of review findings.
- Applying a fix, merge, publication, or external action without authorization.
