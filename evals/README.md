# Evaluation assets and evidence boundaries

This directory separates deterministic regression assets, development traces,
and sanitized real-host observations. None of these artifacts alone establishes
that the reporting framework improves quality or efficiency.

## Directory responsibilities

- `presentation-cases.json` is the versioned public case catalog. It records case
  facts, requested surfaces, expected routing, and deterministic machine checks;
  it is not a collection of model outputs or human judgments.
- `schema/` contains the JSON Schema contracts for case catalogs, frozen study
  plans, caller generation records, controller-stored generation records, blind
  assignments, rating batches, controller checkpoint-artifact receipts, aggregate
  study reports, and public pilot summaries.
  Only the stored-record schema permits controller-produced machine evaluation.
  Schema validity establishes shape, not the truth of a claim.
- `templates/` contains starting points for study plans. Copy a template into a
  private run, resolve every placeholder and digest, then freeze it before any
  generation. A template is not preregistration evidence by itself.
- `fixtures/` contains known-good and known-bad responses plus small display
  assets used to regression-test the deterministic evaluator. Fixtures are test
  vectors, not empirical samples, training data, or effectiveness evidence.
- `runs/forward/` preserves fresh-context development tests and their review
  trace. These runs help detect routing and presentation regressions, but they
  are same-model development evidence rather than a public blind benchmark.
- `runs/pilot/` may contain only sanitized narrative and aggregate records from
  explicitly executed real-host pilots. A pilot is an integration and activation
  signal: it can show that an adapter ran and a Skill was read, but it cannot
  support an effectiveness or efficiency claim.

## Private-run contract

Create every executable study run in a new private directory outside every Git
worktree and set that directory to owner-only mode (`0700`). Keep the complete
frozen inputs, execution receipts, and adjudication trail there. Do not commit raw
provider prompts, model responses, JSONL transcripts, host plans, checkpoint
snapshots or receipts, assignment
keys, rating files, credentials, or records containing absolute local paths.

Only a deliberately sanitized aggregate may be copied into `runs/pilot/`. Before
copying, remove local paths and identifiers, retain the study limitations and
claim gate, and validate the result against the corresponding schema. Private-run
artifacts remain the audit source; the public summary is intentionally
insufficient for replaying credentials or reconstructing blinded assignments.

The controller permits at most 1,500 generation records and rejects a frozen
expected-record manifest above 2 MiB. The limit leaves room for the minimum
1,008-record public design while preventing a mistaken case/model/context/repeat
Cartesian product from creating an unusable run. Rating freeze binds the complete
blind packet; do not edit it afterward.
For a public profile, every generation unit must have a different controller-locked
workspace identity, while an external receipt must separately cover the fresh
per-unit isolation semantics. Required/forbidden visual coverage, 100% mandatory
image/table checks, nonempty visual denominators, and semantic-slot density are
explicit release gates rather than narrative review items.

Framework v1.1 checkpoint plans freeze exact checkpoint/report paths and any local
input-image mirror records. The controller mirrors those files below the private
draft directory, accepts only literal non-traversing targets from that allowlist,
and verifies the same target through agent audit, controller re-audit, stored
evaluation, and blind copying. Controller receipts and event snapshots remain under
`private/` and are never copied into evaluation packets.

## Interpretation rule

Deterministic checks establish only the declared structural or lexical property.
Forward tests provide development feedback. Real-host pilots provide integration
and activation evidence. General claims about readability, correctness,
consistency, latency, or token efficiency require the preregistered comparison,
independent blind ratings, isolation receipts, repetitions, and claim gates
defined by the study pipeline.
