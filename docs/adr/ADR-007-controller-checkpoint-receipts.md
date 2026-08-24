# ADR-007: Capture checkpoint evidence at the controller boundary

- Status: Accepted
- Date: 2026-08-24

## Context

The Codex adapter currently recognizes successful checkpoint creation, bundle
reload, and strict audit commands in the JSONL transcript. Those events show that
commands ran, but they do not bind the persisted checkpoint bytes to the draft that
was audited or to the final response stored by the host controller. Consequently,
`checkpoint_receipt_verified` is always false and a compaction-required framework
record cannot satisfy the public-study checkpoint prerequisite.

OpenAI's documented non-interactive interface exposes JSONL events and a separate
`--output-last-message` file, but no artifact-attestation flag. The controller must
therefore establish the file binding locally without treating transcript text as a
filesystem receipt:
https://learn.chatgpt.com/docs/non-interactive-mode

## Driving factors

- Do not add model calls, network access, or paid execution to deterministic
  validation and CI.
- Keep host adapters responsible for typed event interpretation and the controller
  responsible for filesystem access, process execution, and durable evidence.
- Bind one ordered create -> reload -> strict-audit trace to one checkpoint, one
  audited draft, and the exact final response bytes.
- Read agent-controlled paths only under the frozen workspace and reject traversal,
  symlinks, nonregular files, hard links, oversized inputs, and ambiguous matches.
- Reuse the pinned standard-library `reportctl` audit instead of duplicating its
  checkpoint and Markdown semantics in the study controller.
- Preserve old locked execution receipts for validation while making new receipts
  explicit and fail-closed.

## Candidates

### A. Trust the transcript and hash the named checkpoint after execution

- Pros: smallest implementation and no additional subprocess.
- Cons: does not prove that the named draft equals the final response, does not
  independently validate the checkpoint, loses command ordering when represented
  as booleans, and lets path aliases or post-run substitution overstate evidence.

### B. Ask `reportctl` to write an agent-owned audit sidecar

- Pros: can record checkpoint and draft hashes at the audit command boundary.
- Cons: the agent can write, replace, or fabricate the unkeyed sidecar in the same
  workspace; trusting it would move the unsupported claim rather than retire it.
  Making it authenticated would require a secret or privileged IPC channel exposed
  across the host sandbox boundary.

### C. Snapshot at controller-observed event boundaries and independently re-run the pinned audit

- Pros: keeps file authority in the controller; directly compares the audited
  draft bytes with the host's final response; archives the checkpoint in the
  private execution evidence; reuses the exact pinned audit implementation; and
  adds no instructions, files, or token cost to ordinary non-study reporting.
- Cons: the controller observes an event only after the host emits it, so a process
  with the same UID can still race the event-to-read interval. POSIX
  descriptor-relative no-follow reads are required for claim-eligible receipts.

## Decision

Choose C.

The host adapter returns bounded individual checkpoint events rather than a
controller-verification boolean. As each complete successful JSONL event arrives,
the controller recognizes only allowlisted checkpoint creation, bundle reload, or
strict checkpoint audit commands and immediately snapshots the named artifact.
Echoes, failed commands, unknown options, path mismatches, and compound shell
commands receive no credit.

For a framework execution, the controller resolves event paths beneath the exact
frozen workspace and reads each file through descriptor-relative, no-follow POSIX
operations. It rejects nonportable or escaping paths, symlinks, nonregular files,
multiply linked files, ownership changes, group/other permissions, oversized
content, and read-time metadata drift. A receipt requires exactly one ordered
create -> reload -> audit chain, identical checkpoint bytes at all three events,
and audit-event draft bytes identical to the final host response. Missing,
additional, unsafe, or ambiguous event chains produce no verified receipt.

Because the general Skill correctly permits private scratch outside a repository,
the study controller does not require an agent to infer this narrower evidence
boundary. For v1.1 framework runs it precreates `.agentic-reporting/` as `0700`
with an owner-only nested ignore rule and
appends a hashed study-only micro-contract to the delivered host prompt naming the
checkpoint and draft paths plus their `0600` mode. The full delivered-prompt digest
is frozen in the host plan and execution receipt. Baseline runs and ordinary Skill
use receive no such instruction.

Those paths are mandatory promotion invariants. For a case with supplied local
figures, the plan also freezes their relative paths and digests. The controller
mirrors them below `.agentic-reporting/` at those same paths, and the micro-contract
requires Markdown to use the literal artifact path without `../`. The controller
rejects any local target outside that allowlist and securely rechecks referenced
mirrors before and after final audit. Consequently the target has the same meaning
relative to the private draft, the stored response, and each blind side.

The controller keeps the event bytes in memory until promotion, writes a new private
checkpoint/report pair beside the draft from those exact bytes, runs the repository's
fixed `reportctl.py audit --strict --json` without a shell, re-reads the pair, and
compares the auditor-returned exact report byte count/SHA-256 and parsed checkpoint
intent fingerprint. It accepts only a schema-v2 checkpoint with zero errors, zero warnings, and no
missing anchors. The entrypoint, Markdown scanner, and protocol catalog form a
versioned auditor closure whose SHA-256 is frozen in the host plan; it must match
the installed framework copy before host execution, and the framework workspace
activation receipt must still match after execution. The accepted checkpoint is
copied with owner-only permissions into the controller-owned execution directory.

A versioned execution receipt binds the study and unit identity, condition, host
plan, transcript, final response, checkpoint bytes and size, normalized workspace
locators, checkpoint intent fingerprint, auditor digest, and independent audit
result. The generation record's existing `checkpoint_receipt_verified` field is
derived only by `host-run`; manual imports cannot set it true. Stored-record
validation rechecks every archived digest and the execution binding. Legacy v1.0
host and execution receipts remain readable for validation but can never acquire a
verified checkpoint receipt retroactively; new plans and executions use v1.1.

## Evidence boundary

The receipt proves that the controller archived the bytes visible immediately
after each host-emitted successful event, that those three checkpoint snapshots
were identical, that the audit-event draft exactly matched the final stored
response, and that a pair rebuilt from those captured bytes passed the pinned strict
audit after host completion.

It does not eliminate the same-UID race between event emission and the controller
read, prove which bytes the command itself consumed before exit, prove that the
model semantically remembered the checkpoint rather than reconstructing the
answer, or establish that an operator controlling all unkeyed locks is honest. A
privileged watcher, signed helper, or host-native attestation would be required for
the stronger temporal claim. The public effectiveness study still remains blocked by its other
prerequisites, including external isolation, fixed provider revisions, private
held-out cases, qualified blind ratings, and an actually enforced output-token cap.

## Impact

- Ordinary routing, checkpointing, bundling, and auditing remain unchanged.
- Short tasks and runs without one unambiguous workspace-local candidate continue
  normally with `checkpoint_receipt_verified: false`.
- Invalid evidence cannot make a run claim-eligible; unsafe candidate paths are
  never opened outside the frozen workspace.
- The deterministic verification path can be exercised with a fake host in CI and
  never invokes a model.

This decision partially supersedes ADR-006's statement that the current adapter
cannot produce a verified receipt. The adapter still cannot assert one; v1.1
`host-run` may now derive it from controller-owned snapshots and re-audit evidence.
