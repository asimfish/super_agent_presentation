# ADR-003: Offer a structured report IR as an optional strict path

- Status: Accepted
- Date: 2026-08-24

## Context

Natural-language protocols can guide a normal chat handoff but cannot strictly
guarantee fields or deterministic layout. Batch agents and formal experiment or
incident reports sometimes need a stable machine boundary. Requiring an IR for every
answer, however, would add needless ceremony and make simple conversation worse.

## Decision

Keep direct native drafting as the default. Offer a versioned JSON report
specification, validator, and deterministic Markdown renderer for durable, batch,
or wrapper-controlled workflows. The IR records status, claims and their kinds,
semantic claim roles, evidence references, metrics, visuals, actions, artifacts, and
boundaries. The validator reads each selected mode's required semantics from the
canonical protocol catalog; typed evidence, metrics, uncertainty, actions, and
limitations may satisfy the matching roles.

The renderer controls presentation only. It never infers missing evidence or
converts an unsupported claim into a verified one.

The published Draft 2020-12 schema is a portable structural and conditional
preflight. `reportctl validate-spec` is the authoritative acceptance gate because
evidence-ID uniqueness, cross-record references, placeholder policy, and the live
protocol catalog cannot all be expressed by the standalone schema. A consumer must
not substitute schema-only validation for the CLI gate before rendering.

## Consequences

- Controlled runtimes can enforce structural completeness before delivery.
- A single presentation source prevents parallel artifact drift.
- Formal reports become easier to test and re-render.
- Semantic truth, scientific validity, and evidence quality still require source
  verification.
- Short answers avoid the overhead entirely.
