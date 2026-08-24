# ADR-001: Layer reporting instructions across host, skill, and audit

- Status: Accepted
- Date: 2026-08-24

## Context

A full reporting manual in an always-loaded instruction file improves visibility but
uses context on tasks that do not need it. A skill loaded only on demand is cheaper,
yet activation can be missed—especially after long execution. The framework must
balance persistence, efficiency, and portability across agent hosts.

## Candidates

1. Keep the full manual always loaded. This maximizes prompt visibility but spends
   context on every task and encourages one oversized template.
2. Load the Skill only when the agent remembers to do so. This minimizes persistent
   context but leaves long-task finalization dependent on model memory.
3. Persist a micro-contract, externalize a bounded checkpoint, reload one routed
   bundle, and audit the final draft against that same checkpoint. This adds a small
   local artifact and lexical gate while keeping detailed guidance out of task-time
   context.

## Decision

Use three layers:

1. a host-recognized micro-contract that persists across the task and triggers a
   tiny checkpoint at the start of likely long work;
2. an Agent Skill that retrieves one bounded report protocol at the start or
   reporting boundary, then releases it during task execution;
3. a deterministic audit plus manual evidence checks immediately before delivery;
   for checkpointed work, the audit derives its mode and bounded literal anchors from
   the same schema-v2 file.

Long tasks externalize a small report manifest near the start and reload it at the
final boundary. The manifest is not a process log and must not duplicate task
context. Its unkeyed full-intent checksum detects accidental drift but is not an
authentication mechanism. Schema-v1 manifests remain route/bundle-compatible but
cannot drive the final checkpoint gate.

## Consequences

- Normal task work carries only a small fixed instruction cost.
- Installation provides more persistent prompt exposure than handing an agent a
  URL, but does not guarantee compliance.
- Host adapters need maintenance, but reporting semantics stay canonical.
- A missing normalized literal anchor becomes an audit error, but literal presence
  is not proof of semantic coverage, ownership, truth, or scientific validity.
- The bundle character limit remains an independent caller-controlled context
  budget; a valid two-module checkpoint may require a larger explicit limit.
