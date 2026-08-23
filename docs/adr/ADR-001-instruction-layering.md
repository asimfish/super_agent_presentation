# ADR-001: Layer reporting instructions across host, skill, and audit

- Status: Accepted
- Date: 2026-08-24

## Context

A full reporting manual in an always-loaded instruction file improves visibility but
uses context on tasks that do not need it. A skill loaded only on demand is cheaper,
yet activation can be missed—especially after long execution. The framework must
balance persistence, efficiency, and portability across agent hosts.

## Decision

Use three layers:

1. a host-recognized micro-contract that persists across the task and triggers a
   tiny checkpoint at the start of likely long work;
2. an Agent Skill that retrieves one bounded report protocol at the start or
   reporting boundary, then releases it during task execution;
3. a deterministic audit plus manual evidence checks immediately before delivery.

Long tasks externalize a small report manifest near the start and reload it at the
final boundary. The manifest is not a process log and must not duplicate task
context.

## Consequences

- Normal task work carries only a small fixed instruction cost.
- Installation provides more persistent prompt exposure than handing an agent a
  URL, but does not guarantee compliance.
- Host adapters need maintenance, but reporting semantics stay canonical.
- The audit can catch structural omissions, not truth or scientific validity.
