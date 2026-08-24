# Routed reporting bundle

Primary mode: `academic-synthesis`
Surface: `markdown`; audience: user
Display modules: none
Required semantics: paper_identity, method, evidence, limitations
Must show: none specified
Read: `references/core-contract.md`, `modes/academic-synthesis.md`


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

# Academic synthesis

Use this mode to summarize one paper, synthesize a literature set, explain a research
area, or compare scholarly approaches. Treat library records and secondary summaries
as navigation aids; verify consequential literature claims against primary works.

## Semantic order

1. **Synthesis:** answer the research question or state the paper's central thesis in
   neutral language.
2. **Scope and source set:** define topic, inclusion boundary, recency, venues, and
   source limitations when they affect representativeness.
3. **Conceptual organization:** group work by problem, assumption, method family,
   supervision, data, evaluation setting, or another meaningful axis.
4. **Claim-evidence account:** connect important claims to specific primary sources
   and, where needed, section, figure, table, or page locators.
5. **Agreement and disagreement:** distinguish shared findings from differences
   caused by protocol, assumptions, metrics, data, or deployment conditions.
6. **Limits and gaps:** state missing evidence, contradictory results, and open
   questions.
7. **Relevance:** explain the bounded implication for the user's work when requested.

## Source discipline

- Give each source a stable identifier and resolvable bibliographic link when
  available.
- Separate what a paper states from what the synthesis infers across papers.
- Do not present a paraphrase as a quotation. Keep any necessary quotation short and
  attributable.
- Verify venue, year, authorship, title, and reported result before relying on them.
- Do not create a citation to fill a narrative gap.
- Preserve the source's epistemic operator. `Not reported`, `not found in the
  inspected sections`, `not evaluated`, and `shown to be absent` are different
  claims. Never turn non-reporting into proof that an experiment or analysis did not
  occur.
- Call something an author-reported limitation only when the paper characterizes it
  that way. Otherwise describe it as a boundary of the supplied or inspected
  evidence.
- Compare papers only on explicit axes. Different tasks, datasets, access assumptions,
  or metrics do not form one leaderboard.

## Single-paper brief

For one paper, cover bibliographic identity, research question, thesis, method and
assumptions, evaluation protocol, main evidence, limitations, and relationship to the
reader's question. A summary is not an endorsement or a review.

## Multi-paper synthesis

Prefer a concept-first narrative over one paragraph per paper. Use an evidence map
when several claims depend on different source subsets. State whether the source set
is systematic, curated, convenience-based, or incomplete.

## Avoid

- `The literature shows` without naming the relevant source set.
- Treating an abstract, search snippet, or related-work sentence as verification of a
  detailed result.
- Claiming consensus from repeated wording or several papers sharing a benchmark.
- Overstating generalization, causality, significance, or deployment readiness.
