# Agentic reporting benchmark

## Status and claim boundary

This repository ships a deterministic fixture harness plus a standard-library-only
private study controller. The checked-in smoke fixtures test the evaluator and the
declared reporting invariants; they do **not** show that the framework improves a
real agent. A one-pair real-host pilot validates an execution and activation path
only. An effectiveness claim requires a completed, externally isolated, pinned,
blind baseline-versus-framework study, independent frozen ratings, complete host
telemetry, and a passing machine claim report.

## Questions under evaluation

The benchmark keeps three questions separate:

1. Does a framework report meet an absolute reporting-quality bar?
2. With model, task, tools, decoding, and an actually enforceable output budget held fixed, does the
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
- `presentation_study.py` now implements the `core` mechanics: immutable inputs,
  generation ingest, typed host receipts, blinding, rating freeze, paired case
  bootstrap, and claim gates. No complete core study has been run. A full run still
  needs at least four private held-out cases per scenario, both conditions, and
  three independent repeats.
- The controller accepts the planned `long-soak` contexts near 10%, 50%, and 85%
  occupancy plus a compaction/resume boundary, and records checkpoint telemetry.
  That matrix has not been executed; self-reported occupancy or checkpoint use is
  insufficient.
- `evals/runs/pilot/codex-20260824/` is a one-case, one-model-alias, one-repeat real
  Codex pilot. It observed one treatment Skill read and none in baseline, but has no
  blind ratings, private holdout, external baseline isolation, fixed provider
  revision, audited global-instruction policy, or enforced output-token cap.
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

The private study lifecycle is separate from smoke:

```bash
python3 scripts/presentation_study.py init \
  --plan <private-dir>/plan.json \
  --cases-file <private-dir>/heldout-cases.json \
  --artifact-root <private-dir>/case-assets \
  --output <private-dir>/run
python3 scripts/presentation_study.py import-output \
  --run-dir <private-dir>/run --record <record.json> --response <response.md>
python3 scripts/presentation_study.py validate --run-dir <private-dir>/run
python3 scripts/presentation_study.py blind --run-dir <private-dir>/run
python3 scripts/presentation_study.py rating-template \
  --run-dir <private-dir>/run --rater-id <rater-id> --output <private-rating.json>
python3 scripts/presentation_study.py freeze-ratings \
  --run-dir <private-dir>/run --rating <completed-private-rating.json>
python3 scripts/presentation_study.py aggregate --run-dir <private-dir>/run --json
```

For a supported real host, `host-plan` freezes a typed receipt without execution.
`host-run` launches the exact reviewed executable only when `--execute` is present;
without it the command fails closed. The adapter uses a fixed argument vector and
`shell=False`, then parses bounded JSONL telemetry. The plan locks the complete argv,
transcript format, and host-adapter source SHA-256; execution rebuilds and compares
all three exactly, and the completed receipt is checked against the frozen plan.
It may inherit host credentials,
use the network, incur cost, and alter provider-side state. It enforces a timeout and
local transcript/stderr/response byte caps, but Codex currently does not expose the
plan's `max_output_tokens` as an adapter-enforced provider cap. The receipt records
that limitation instead of claiming equal budgets. Transcript telemetry credits
only successful, exactly tokenized Skill/reportctl command executions; echoed text,
failed commands, shell operators, help/version or unknown-option forms, and
mismatched checkpoint paths receive no credit.
The adapter turns one ordered create → reload → strict-audit sequence into a bounded
candidate, but it cannot mark that evidence verified. For a framework v1.1 host
execution, the controller precreates an owner-only, self-ignored `.agentic-reporting/` directory
and appends a hashed study-only path/mode contract to the delivered host prompt.
The named checkpoint and report paths are promotion invariants, not suggestions.
Frozen local input images are mirrored below the report directory at their exact
workspace-relative paths; traversal-bearing or unmirrored local targets receive no
receipt, so the same Markdown target remains valid in agent audit, controller audit,
stored records, and blind packets.
The full delivered-prompt digest is frozen in the plan and execution receipt; this
contract is not part of ordinary Skill use. The controller then snapshots the checkpoint as each successful event arrives
and snapshots the report at the audit event. It accepts exactly one candidate only
when all three checkpoint byte sequences match, the report bytes equal the final
host response, the framework workspace receipt remains unchanged, and an
independent strict audit over a fresh private pair written from those captured bytes
by the plan-pinned repository `reportctl` succeeds. The controller re-reads that pair
and every referenced mirrored image after audit before promotion. Only
then does `host-run` derive `checkpoint_receipt_verified: true`. Manual imports,
baseline records, ambiguous candidates, unsafe paths, and legacy v1.0 receipts
cannot obtain or retroactively acquire that evidence.

The checkpoint and artifact receipt remain private execution evidence; they are not
copied into the blind packet, aggregate, or release artifact. The receipt establishes
controller observations at the three event boundaries plus a final independent
audit. It does not prove the exact bytes used internally by each child command,
continuous immutability against a same-UID process, semantic checkpoint recall, or
operator honesty. It adds no instructions, calls, or token cost to ordinary agent
reporting outside this explicit study path.

`pilot-summary` is available only for `study_kind=pilot` and always emits
`status: insufficient_evidence` with `effectiveness_claim_eligible: false`.

## Baseline-versus-framework protocol

1. Freeze the case set and gates before generation.
2. Pin a verifiable model revision, client executable and SHA-256, system/global
   instructions and their receipts, framework commit, installed Skill/adapter
   manifests, tools, decoding controls, enforceable output budget, locale,
   renderer, repeat semantics, and artifact checksums. A caller-supplied revision
   label is not proof that a provider model is immutable.
3. Run each generation unit in its own controller-recorded workspace. Run the
   baseline in an externally isolated sandbox that cannot read this
   framework or the hidden evaluator, and retain its isolation receipt. A separate
   same-account workspace is useful for a pilot but is not sufficient for a public
   claim. The external receipt must cover the fresh per-unit starting state, not
   merely repeat the plan's `independent-repeat` label. Run treatment from the
   pinned distribution, not a maintainer checkout.
4. Give both conditions the exact prompt emitted by this harness. Preserve tool
   availability and task assets.
5. Save raw Markdown, generated artifacts, the full transcript, token counts,
   latency, context occupancy, and any compaction event.
6. Randomize pair order and A/B assignment. Keep the key private with owner-only
   permissions, and reject symbolic-link key targets.
7. Render both reports with the same renderer. Raters score each side separately
   before recording a preference. The controller omits condition labels, machine
   checks, and the assignment key. It copies response content verbatim, so style or
   explicit self-identification may reveal treatment; measure and disclose that
   residual blinding limitation rather than claiming perfect masking.
8. Use at least two independent qualified raters; three are preferred for release
   evidence. Freeze ratings before deblinding.
9. Aggregate repeated seeds at the case level, then use a paired case bootstrap.
   Do not treat seeds from one prompt as independent cases.

## Claim eligibility before metric gates

The controller returns `insufficient_evidence` before considering a favorable score
unless the frozen design includes all of the following:

- a private held-out case file distinct from the public development suite and an
  external preregistration receipt;
- all seven public scenario families with at least four cases each;
- both required and forbidden visual-oracle coverage, plus at least one required
  local-image check and declared table-count checks;
- at least three declared independent repeats backed by distinct controller-locked
  workspaces and an external per-unit isolation receipt, multiple verifiable model revisions, and
  fresh/50%/85% context conditions including required compaction coverage;
- an `external-sandbox` baseline-isolation receipt and
  `shared-and-audited` global-instruction policy;
- complete generation pairs, host telemetry, framework activation evidence,
  controller-bound executable-host records, unpolluted baseline receipts, revision
  receipts, enforced output-token caps,
  observed context strata, complete compaction observations, successful strict
  final-audit telemetry for every framework response, and successful
  framework checkpoint create/reload/audit telemetry plus a controller-verified
  checkpoint receipt in compaction-required strata;
- at least two qualified independent raters with valid owner-only frozen batches.

Passing these prerequisites does not itself establish effectiveness; every
provisional metric gate below must also pass. Unkeyed SHA-256 receipts detect drift,
not a dishonest operator or compromised environment.

No checked-in run currently satisfies this design. In particular, the planned
fresh/50%/85% context-occupancy and compaction matrix has not been executed, Codex
does not provide the controller an enforceable provider output-token or monetary
cap, and a model revision label does not by itself pin provider routing or weights.
Controller-verified checkpoint receipts retire only one evidence gap; they do not
make the published pilot eligible for an effectiveness claim.

The release controller accepts at most 1,500 generation records and also rejects a
serialized expected-record manifest above 2 MiB. This accommodates the minimum
1,008-record public design while failing closed on accidental Cartesian explosions.

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
- at least 98% declared machine-invariant pass rate and 100% pass rate for every
  required local-image and declared table-count check;
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
  human-rated required semantic slots per 1,000 output tokens relative to baseline;
- strict final-audit pass rate at 85% context occupancy at least 90%, no more than
  five percentage points below the fresh-session rate. Fresh short tasks may use
  mode-only audit; compaction strata additionally require the checkpoint contract;
  and
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
