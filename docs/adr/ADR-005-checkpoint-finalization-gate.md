# ADR-005: Gate long-task finalization with the same checkpoint

- Status: Accepted
- Date: 2026-08-24

## Context

A prompt can remind an agent to preserve reporting intent, but it cannot guarantee
that the agent will remember or follow the reminder after a long run, compaction, or
handoff. Reloading a route at the end also does not establish that it is the route
saved at task start. The gate must remain small, deterministic, compatible with
existing short-task commands, and honest about what a lexical audit can prove.

## Candidates

1. Trust the final prompt or model memory. This has no executable failure signal and
   is vulnerable to long-context drift.
2. Persist only the selected mode. This is small, but loses the task, audience,
   surface, module, and required-display intent that explains the route.
3. Fingerprint the full reporting intent in a schema-v2 checkpoint, derive the final
   audit mode from that same file, and gate a few bounded literal anchors. This adds
   a local artifact and a conservative lexical proxy while keeping task execution
   independent of the reporting bundle.
4. Require a semantic judge or full Markdown renderer. This could check a broader
   interpretation, but introduces model or parser dependence and still cannot prove
   facts, authorship, or scientific validity.

## Decision

Choose candidate 3. Schema v2 fingerprints `task`, `mode`, `surface`, `audience`,
`modules`, and `must_show` as one intent. `audit --checkpoint` derives the mode;
supplying the same explicit mode is allowed, while a conflict is an input error.
Every `must_show` value must occur as a normalized literal substring in the
documented blank-line-bounded, column-zero, plain top-level Markdown prose subset.
Headings, quotes, lists, tables, links/references, images, code, and raw HTML make a
paragraph ineligible. After the first unmasked raw HTML tag, later paragraphs also
receive no credit because the proxy does not model cross-paragraph DOM or CSS state.
Raw HTML is itself a structural audit error. Each anchor must match within one safe
paragraph: soft line breaks collapse, but blank-line boundaries do not. Before
normalization, the proxy decodes one round of the shared scanner's supported,
semicolon-terminated CommonMark entity subset only at an `&` not escaped by an
odd-length backslash run; a decoded control or Unicode non-rendering character is an
error. V2 anchors use exact rendered plain text and reject Markdown delimiter forms.
A missing anchor is an audit failure. Agents should place each anchor before raw
HTML in a standalone ordinary conclusion sentence rather than a heading, table cell,
or display label.

Each anchor is limited to 120 characters. Its escaped checkpoint receipt, including
the `; ` separators between anchors, is limited to 240 characters in total. These
limits keep the persisted contract and diagnostics bounded. The checksum is unkeyed:
it detects accidental drift, not a malicious writer who can recompute it. Literal
presence is an omission proxy, not proof of meaning, ownership, truth, audience or
surface fit, or module use.

Schema-v1 checkpoints remain accepted by `route` and `bundle` for compatibility but
cannot drive checkpoint-backed final audit. They must be recreated or upgraded to a
valid v2 file first. The legacy `audit --mode` path remains available for short work
without a checkpoint.

Checkpoint files belong in private scratch outside version control. Task, audience,
and anchor text are stored verbatim and `route` or `bundle` can replay them to
stdout, so callers must not store secrets or unnecessary private data. Restrictive
POSIX creation does not protect permissive parent directories, logs, backups, a
later commit, or a same-account process that replaces the file between checks.

## Enforcement boundary

Repository instructions, adapters, and the Skill can keep both bookends salient but
cannot force an arbitrary agent to invoke them. A wrapper or CI workflow can enforce
the mechanical portion by blocking delivery unless checkpoint creation succeeds and
the final `audit --checkpoint` exits 0. Exit 1 denotes candidate-content failure,
including a missing anchor; exit 2 denotes an invalid invocation, checkpoint,
unsupported v1 gate, or conflicting intent. Manual evidence and claim verification
remain mandatory after an audit passes.

The bundle's default 16,000-character limit is a separate retrieval budget, not a
checkpoint-validity promise. Some valid checkpoints selecting two large modules
require an explicitly higher `--max-chars` value. Checkpoint-backed audit separately
caps report input at 1 MiB because it runs the prose proxy; mode-only audit keeps the
4 MiB cap. Before NFC or matching, eligible prose paragraphs above 4,096 characters
or runs above 64 Unicode mark characters fail and are skipped. JSON numeric source
tokens above 128 characters fail before integer or float conversion. These inner
limits bound work that the outer byte caps alone do not control.

## Consequences

- Long-task intent can be reloaded and mechanically compared at finalization without
  retaining the full protocol during task work.
- V2 is intentionally stricter than v1; compatibility is preserved only before the
  final gate.
- Callers gain stable exit codes suitable for wrappers and CI, but prompts alone
  remain best effort.
- The gate reduces omission and drift risk; it does not establish report quality or
  factual correctness.
