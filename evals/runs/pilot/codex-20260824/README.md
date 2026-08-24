# Codex development pilot — 2026-08-24

This directory contains only the controller-generated aggregate summary from a
minimal real-host integration pilot. Raw prompts, responses, JSONL transcripts,
host plans, local paths, credentials, assignment keys, and rating files remain in a
private run directory outside Git.

## What ran

- one public benchmark case: `experiment-null-result`;
- one model alias: `gpt-5.6-luna` through Codex CLI `0.149.0`;
- one fresh-context repeat for each condition;
- a baseline workspace without the project adapter and a framework workspace with
  the Skill and `AGENTS.md` adapter installed;
- treatment pinned to repository commit
  `b4c014d4b87c0d4556908b492dcf35cccb8631d4` (release `v0.2.0`);
- executable pinned by SHA-256, while the provider model revision remained
  unpinned.

The framework trace showed one Skill read. The baseline trace showed none. The
baseline response passed 9/10 declared machine checks; the framework response
passed 10/10. The framework response used 980 output tokens and 29.763 seconds,
versus 358 tokens and 13.597 seconds for the baseline. The paired output-token
overhead was approximately `+173.7%`.

## Interpretation boundary

These two calls are an integration and activation signal, not an effectiveness or
efficiency study. The case was public, the sample size was one, there were no blind
human ratings, the baseline used a same-account workspace rather than an externally
isolated sandbox, and the global instruction policy was not audited. Context
occupancy and compaction were not observed. The plan's output-token value was not a
provider-enforced cap. Model revision and service behavior were not immutable.

Accordingly, `pilot-summary.json` is permanently gated to
`insufficient_evidence` and `effectiveness_claim_eligible: false`. The observed
cost also motivated the v0.3 change that removes the redundant generic
`conclusions` module from the automatic `experiment-report` route. That follow-up
is verified deterministically by routing and bundle-size tests; it was not rerun as
a second model-effectiveness comparison.
