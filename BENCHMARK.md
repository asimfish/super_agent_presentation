# Agentic reporting benchmark

## Status and claim boundary

This repository ships an executable, standard-library-only evaluation harness. The
checked-in smoke fixtures test the harness and the declared reporting invariants;
they do **not** show that the framework improves a real agent. An effectiveness
claim requires a completed, pinned, blind baseline-versus-framework generation run,
independent ratings, and the resulting machine report.

## Questions under evaluation

The benchmark keeps three questions separate:

1. Does a framework report meet an absolute reporting-quality bar?
2. With model, task, tools, decoding, and output budget held fixed, does the
   framework improve the report over a no-framework baseline?
3. Does reporting guidance preserve task correctness and remain proportionate in
   token cost, visual use, and ceremony after long work sessions?

Consistency means stable semantic coverage and prioritization, not identical prose
or universal headings. Explicit user formatting remains authoritative.

## Suites

- `harness-smoke` uses checked-in known-good and deliberately mutated responses for
  seven scenarios. It calls no model and proves only that the evaluator catches the
  declared mutations.
- `skills/agentic-reporting/evals/activation.json` is a declarative activation
  contract with eight cases. CI validates four boundary categories and five
  governance rubrics, then checks only the five positive cases' internal routes
  after activation. It does not observe whether a real host invokes the Skill.
- A future `core` run should use at least four held-out cases per scenario, both
  conditions, and three seeds.
- A future `long-soak` run should probe the same final handoff near 10%, 50%, and
  85% context occupancy, plus a compaction/resume boundary, without repeating the
  reporting rules. It should record creation, reload, and final audit against the
  same checkpoint rather than accepting an agent's self-report that these occurred.
- Only a preregistered full run across held-out cases and multiple model revisions
  should support a public effectiveness claim.

The smoke scenarios are concise answer, long engineering handoff, experiment
analysis, image presentation, multi-table presentation, academic-paper synthesis,
and failure/risk reporting.

## Commands

Run from the repository root:

```bash
python3 scripts/presentation_benchmark.py list
python3 scripts/presentation_benchmark.py prompt experiment-null-result
python3 scripts/presentation_benchmark.py check \
  --case experiment-null-result \
  --response evals/fixtures/responses/good/experiment-null-result.md
python3 scripts/presentation_benchmark.py smoke
```

Every command also supports `--json`. `prompt` deliberately emits only the
condition-neutral request, facts, evidence boundary, supplied artifacts, and output
budget. It does not reveal machine checks, semantic slots, or the visual oracle.

The smoke JSON deliberately reports `host_activation_observed: false` and
`activation_effectiveness_claim: false`. The locally checked route proxy must not be
renamed activation accuracy, precision, recall, or pass rate.

## Baseline-versus-framework protocol

1. Freeze the case set and gates before generation.
2. Pin model revision, client, system prompts and their SHA-256 hashes, framework
   commit, tools, decoding controls, output budget, locale, rendering CSS, seed
   policy, and artifact checksums.
3. Run the baseline in an isolated directory that cannot read this framework or the
   hidden evaluator. Run the treatment from the pinned distribution, not from a
   maintainer checkout containing hidden cases.
4. Give both conditions the exact prompt emitted by this harness. Preserve tool
   availability and task assets.
5. Save raw Markdown, generated artifacts, the full transcript, token counts,
   latency, context occupancy, and any compaction event.
6. Randomize pair order and A/B assignment. Keep the key private with owner-only
   permissions, and reject symbolic-link key targets.
7. Render both reports with the same renderer. Raters score each side separately
   before recording a preference. They must not see condition names, machine checks,
   framework terminology, or the assignment key.
8. Use at least two independent qualified raters; three are preferred for release
   evidence. Freeze ratings before deblinding.
9. Aggregate repeated seeds at the case level, then use a paired case bootstrap.
   Do not treat seeds from one prompt as independent cases.

An optional `prompt-only` ablation may distinguish the effect of a short style prompt
from the persistent micro-contract, routed protocol, and final audit. It is not a
replacement for the baseline comparison.

## Human rubric

Score each response from 1 to 5 on:

- task fidelity;
- information architecture;
- readability and scannability;
- completeness and actionability;
- evidence calibration;
- visual/display fitness; and
- concision and proportionality.

For a more objective readability measure, ask readers to identify the current
status, strongest evidence, and next action or limitation, and record both accuracy
and elapsed time. Formula-based readability scores are diagnostic only.

Critical errors cannot be averaged away: fabricated evidence or tests; numeric,
unit, negation, or modality drift; false completion or stale status; unsupported
causality, significance, or ranking; ranking incomparable protocols; secret
leakage; materially misleading visuals; and ignoring an explicit user format.

## Machine checks and their limits

The harness checks only declared observable invariants: required and forbidden
phrases, word and heading budgets, Markdown table counts, image presence and local
resolution, alt text, citation allowlists, and unresolved placeholders. Case-level
checks preserve supplied numbers, uncertainty boundaries, comparison boundaries,
and status.

Image-forbidden checks fail closed on every unescaped `![` marker and every raw
HTML opening tag, including literals. This broader rule closes inline CSS,
custom-element, SVG, object, and iframe visual sinks without attempting to execute
an HTML renderer. Mermaid fence openings also count as rendered visual markers for
this check. Escape the Markdown marker or entity-encode the opening `<` in examples.
Required image credit remains limited to the documented canonical Markdown form.
It stops after the first raw contiguous triple-backtick/triple-tilde run or
paragraph-sensitive type-7 HTML tag marker to avoid optimistic credit when this
bounded scanner and a full CommonMark parser could disagree. Put required images
before those forms; URI autolinks do not trigger the type-7 marker.

Passing these checks does not establish factual truth, scientific validity,
appropriate causal interpretation, accessibility, or professional readability.
Those properties require source verification and human review.

## Provisional release gates

These thresholds must be frozen before inspecting a real run:

- zero critical errors;
- at least 98% declared machine-invariant pass rate and 100% resolvable local
  resources/tables;
- framework task fidelity non-inferior to baseline by a 0.20 margin on a 5-point
  scale;
- all human dimensions at least 4.0, with readability, completeness, and evidence
  calibration at least 4.2;
- paired primary-composite gain at least 0.30 with a case-bootstrap 95% interval
  above zero;
- pairwise win rate at least 65% and loss rate at most 15%;
- semantic-slot adherence at least 95%;
- required/forbidden visual-selection precision and recall at least 90%;
- median output-token overhead at most 15%, p90 at most 30%, and no reduction in
  useful facts or semantic slots per 1,000 output tokens;
- contract pass rate at 85% context occupancy at least 90%, no more than five
  percentage points below the fresh-session rate; and
- at least 85% of paired rater scores within one point. Low agreement blocks an
  effectiveness claim even when mean scores look favorable.

The framework's always-on instruction budget and routed bundle budget should be
reported separately from output tokens. Latency and model-call counts are reported
as costs, not hidden inside a quality composite.

## Contamination and overfitting controls

- Keep public development cases separate from private holdouts; never distribute
  hidden prompts or checks in the installable framework.
- Store facts and allowed/forbidden claims, not reference prose.
- Parameterize facts and phrasing, rotate part of the holdout, and retain a frozen
  anchor set for longitudinal comparison.
- Hold out task domains as well as wording, and repeat across model families.
- Change framework guidance only for a cross-case behavior supported by evidence,
  not to satisfy one hidden regex.
- Version schemas, artifacts, licenses, checksums, model inputs, and the framework
  commit.
- Treat regex and structural scores as diagnostics; never optimize them as a proxy
  for human usefulness.

## Adversarial coverage

The broader suite should include a yes/no task that punishes over-formatting, an
explicit JSON-format override, prompt injection embedded in logs, a late failure
after earlier success, rollback without root-cause resolution, unnecessary and
misleading charts, inaccessible color-only graphics, zero/missing/N/A confusion,
incomparable protocols, absent uncertainty, conflicting facts, secrets in logs,
partial multi-task success, unsupported SOTA language, stale file links, a
checkpoint/explicit-mode conflict, a tampered full-intent fingerprint, must-show text
that appears only in headings/quotes/lists/tables/links/references/images/code/raw
HTML, entity source text that differs from its rendered character, decoded controls
or non-rendering characters, odd/even backslash entity escapes, an anchor split
across blank-line paragraphs versus a soft line break, rejected anchor delimiter
forms, an anchor after an unmasked raw HTML tag, a checkpoint-backed report above 1
MiB, and audit output that must not echo a missing sensitive anchor. These are
structural and security regressions, not evidence that real-agent reporting
improves.
