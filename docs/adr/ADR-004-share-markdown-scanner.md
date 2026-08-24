# ADR-004: Share one bounded Markdown image scanner

- Status: Accepted
- Date: 2026-08-24

## Context

The report audit and development benchmark both classify Markdown image candidates,
CommonMark literal regions, entity references, and source order. Separate copies had
the same intended security boundary but could drift after a fix, producing different
credit for the same input. The installed Skill must remain standard-library-only and
self-contained.

## Candidates

1. Keep independent scanners in each consumer. This avoids an import boundary, but
   duplicates security-sensitive state machines and requires parity fixes twice.
2. Put the bounded scanner in the installable Skill and expose a narrow, typed module
   API. Consumers retain their own policy while sharing source parsing.
3. Adopt a third-party full Markdown parser. This could increase syntax coverage,
   but adds a dependency, changes the install contract, and still would not make a
   downstream renderer or sanitizer identical.

## Decision

Choose candidate 2. `skills/agentic-reporting/scripts/markdown_image_scanner.py` is
the canonical source scanner. It exposes source-ordered image records, conservative
block masking, CommonMark entity decoding, escape checks, and visible-alt checks.
`reportctl` loads it lazily by fixed packaged path and keeps its compatibility-facing
wrappers; the benchmark imports the same engine and applies benchmark-specific
requirements separately.

## Consequences

- Parser and security fixes reach both consumers through one implementation.
- The installer must copy the scanner with the rest of the Skill; isolated installed
  execution is a release test.
- Route, checkpoint, and bundle commands do not load the scanner.
- Consumer policy, finding text, and fixture or report semantics remain separate.
- The scanner is a bounded conservative subset, not a claim of full CommonMark or
  renderer equivalence.
