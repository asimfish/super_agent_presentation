# ADR-006: Separate deterministic study evidence from host execution

- Status: Accepted
- Date: 2026-08-24
- Update: ADR-007 partially supersedes the checkpoint-receipt limitation below;
  adapters still cannot assert verification, while v1.1 `host-run` can derive it
  from controller-owned event snapshots and an independent audit.

## Context

The structural harness can detect declared report mutations, but it cannot show that
a real agent host activates the Skill or that framework reports outperform an
isolated baseline. A credible comparison needs frozen inputs, paired generation,
blind assignment, independently frozen ratings, and case-level statistics. It must
also avoid committing hidden cases, transcripts, assignment keys, credentials, or
unredacted rater data. Model calls are costly and host CLIs may mutate user state,
so ordinary validation and CI must never invoke them implicitly.

## Driving factors

- Keep the public evaluator standard-library-only, deterministic, and reviewable.
- Preserve a strict claim boundary between harness checks, pilots, and full studies.
- Support more than one host without accepting arbitrary shell command templates.
- Keep hidden holdouts and blind-assignment material outside the repository.
- Bound untrusted JSON, Markdown, transcript, subprocess, and filesystem inputs.
- Make external model execution an explicit, least-privilege operation.

## Candidates

### A. Add generation and ratings directly to `presentation_benchmark.py`

- Pros: one command and direct reuse of existing case checks.
- Cons: mixes deterministic CI with network/cost side effects, expands an already
  large parser, and makes it easier to mistake a smoke result for study evidence.

### B. Add a separate study controller with typed host adapters

- Pros: keeps the existing harness pure; gives plans, records, blind packages,
  ratings, and reports explicit schemas; lets host execution remain opt-in behind a
  narrow adapter interface; and permits private study directories.
- Cons: adds one CLI and a small amount of shared-loader plumbing.

### C. Adopt a hosted experiment or generic evaluation platform

- Pros: mature dashboards, queues, and managed model integrations.
- Cons: introduces runtime dependencies, cost, external data retention, credential
  handling, and a platform-specific evidence format that the repository cannot
  independently reproduce.

## Decision

Choose B. `scripts/presentation_study.py` owns the study lifecycle and imports the
existing benchmark only through a fixed local module path. JSON is canonical for
plans, generation records, assignment receipts, ratings, and machine reports;
responses remain Markdown and host event streams remain immutable evidence files.
Caller generation input and controller-enriched storage use separate, self-contained
schemas. Only the stored form may contain `machine_evaluation`; its schema name and
the full record are digest-locked by the controller.

The controller separates two boundaries:

1. Deterministic commands validate, prepare, ingest, blind, freeze ratings, and
   aggregate. They never call a model.
2. Host commands implement a typed adapter protocol and registry. Planning is the
   default. Execution requires an explicit flag, an exact executable path and
   SHA-256 identity, a frozen complete argv, transcript format, host-adapter source
   SHA-256, pinned workspace/Skill/active-instruction receipts, bounded
   runtime and local evidence sizes, and argument-vector process launch without a
   shell. The receipt records which requested controls the adapter can actually
   enforce. The current Codex path cannot enforce the plan's output-token value or a
   cost ceiling; those remain declared constraints and must not be described as
   equivalent provider-side budgets.

`host_adapter` telemetry is controller-owned: `host-run` binds the frozen host plan
and completed execution receipt to the full stored generation record. A normal
`import-output` call may ingest manual evidence but cannot self-label it as adapter
telemetry or an adapter-enforced cap. Every imported record, response, transcript,
and optional host binding receives a controller-owned digest lock; later drift makes
the generation matrix invalid. Public eligibility rejects any `manual` model.
At execution, the adapter rebuild must match the frozen argv, transcript format,
capability bit, and source digest exactly. The completed execution receipt repeats
those identities, and later binding validation compares them to the locked plan.
The Codex parser credits only successful, exactly tokenized reads and reportctl
commands. It ignores echoed substrings, failed commands, shell operators, and
mismatched checkpoint paths. Command observation is weaker than an artifact
receipt, so the current adapter cannot set `checkpoint_receipt_verified: true`.

Study runs must use a previously nonexistent private directory outside a Git
worktree; the controller creates it with POSIX mode `0700`. Plans, prompts,
responses, transcripts, host receipts, assignment keys, and ratings remain private
and must not be committed. The blind package contains condition-neutral prompts and
randomized A/B reports without controller condition metadata; the assignment key
remains in the private run with owner-only
permissions. Rating files are copied and hashed before deblinding, and the rating
lock binds both the private assignment key and the complete blind-packet tree.
Aggregation rejects any later change to those inputs. These unkeyed hashes detect
drift but do not authenticate a dishonest operator.
Response bytes are intentionally preserved, so writing style or explicit framework
self-identification can reveal treatment to a rater. The controller does not claim
content-level blinding.

The controller fixes one release threshold profile, bounds JSON depth/value count
and numeric-token length before analysis, caps the Cartesian generation matrix at
1,500 records, and rejects an expected-record manifest that would exceed its own
2 MiB read ceiling. The cap still permits the minimum 1,008-record public design
(28 held-out cases, two revisions, three context strata, three repeats, and two
conditions).

A `same-account-workspace` baseline is sufficient only for integration pilots.
Public claim eligibility requires an `external-sandbox` isolation receipt and a
`shared-and-audited` global-instruction policy. A caller-provided model revision
string is descriptive metadata, not proof of immutable provider behavior. Public
claim eligibility additionally requires external revision receipts, a genuinely
enforced output-token cap, observed context strata, complete compaction telemetry,
and successful create/reload/audit checkpoint telemetry for framework runs in
compaction-required strata. Short tasks remain eligible for the proportional
mode-only final audit defined by the Skill.
Accordingly, `final_audit_passed` is separate from
`checkpoint_audit_passed`: the long-soak comparison uses the common strict final
audit, while checkpoint create/reload/audit/receipt fields constrain only
compaction-required framework records.
The public profile also requires a distinct controller-locked workspace for every
generation unit; the external isolation receipt must attest the fresh per-unit
starting state. A plan label alone is not verification of independent repeats.

Release metrics fail closed on empty visual denominators and require both required
and forbidden visual-oracle coverage. Required local-image and declared table-count
checks have a separate 100% gate, so the aggregate 98% invariant threshold cannot
hide a broken display. Output efficiency includes a frozen non-inferiority gate for
human-rated required semantic slots per 1,000 output tokens.

## Impact

- `harness-smoke` remains fast, offline, and unable to claim effectiveness.
- A pilot report always states `effectiveness_claim_eligible: false`, even if every
  provisional metric passes.
- Full-study eligibility requires frozen minimum design properties and all declared
  gates; semantic truth and operator independence remain external evidence.
- A typed host plan is inert. Only `host-run --execute` may launch the reviewed
  executable; that process can use inherited credentials, network access, paid
  services, and provider-side state.
- Host additions implement the adapter contract rather than adding raw command
  strings to study plans.
- Private artifacts are not release assets. Only a redacted aggregate and its input
  digests may be published after review.
