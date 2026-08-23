# Routed reporting bundle

Primary mode: `experiment-report`
Surface: `markdown`; audience: user
Display modules: none
Required semantics: question, method, metrics, uncertainty, boundary
Must show: none specified
Read: `references/core-contract.md`, `modes/experiment-report.md`


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

# Experiment report

Use this mode for benchmarks, ablations, controlled evaluations, model comparisons,
or empirical studies. Organize the report around research questions rather than the
order in which experiments were run.

## Semantic order

1. **Main result:** state the supported result and its most important trade-off or
   qualification.
2. **Research question:** define the proposition each experiment tests.
3. **Protocol:** identify methods, baselines, data, splits, selection procedure,
   metrics, compute, and material controls.
4. **Results:** present exact evidence with the tables or visuals required to read
   it.
5. **Analysis:** explain patterns, exceptions, practical magnitude, and competing
   interpretations.
6. **Boundary:** report uncertainty, null results, failed runs, limitations, and the
   domain in which the evidence applies.
7. **Conclusion and next experiment:** state only what the protocol supports.

## Metric and uncertainty contract

For every decision-relevant metric, state:

- definition, unit, and higher-is-better or lower-is-better direction;
- evaluation population, denominator, and aggregation level;
- number of independent runs, seeds, trials, samples, or tasks;
- variability source and whether the interval is SD, SEM, CI, quantiles, or another
  statistic;
- interval computation and assumptions when they affect interpretation.

Do not call a difference statistically significant without a defined analysis that
supports that statement. Do not equate statistical significance with practical
importance.

## Comparability and selection

- Rank or highlight methods only inside a shared evaluation protocol.
- Expose material differences in data, supervision, pretraining, compute, hardware,
  tuning budget, test-time resources, and access to privileged information.
- State how hyperparameters, checkpoints, prompts, seeds, and reported runs were
  selected. Do not compare a selected best run with a baseline mean without making
  the mismatch explicit.
- Keep zero, missing, not reported, failed, and not applicable distinct.

## Analysis discipline

- Report verified values before explaining them.
- Discuss results that contradict the main narrative, not only the best row.
- Treat nearly equal observed means with overlapping or untested uncertainty as a
  trade-off or unresolved comparison, not a universal winner.
- With opposing metrics, report the Pareto trade-off. Do not collapse it into an
  overall balance ranking unless the decision supplies a utility function, budget,
  constraint, or minimum acceptable threshold.
- Separate descriptive, diagnostic, predictive, causal, and deployment claims.
- State compute and resource requirements when they affect reproducibility or the
  comparison.

## Avoid

- A global leaderboard built from different tasks or protocols.
- Boldface as a substitute for analysis.
- `state of the art` without a named benchmark, metric, comparison set, and verified
  result.
- A conclusion broader than the tested datasets, seeds, environments, or deployment
  conditions.
