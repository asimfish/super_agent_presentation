# Codex held-out controlled study — 2026-08-25

This directory contains only the controller-generated aggregate summary
(`study-summary.json`) from a private controlled study. The 28 held-out case
texts, raw prompts, responses, JSONL transcripts, host plans, rating files,
assignment keys, and local paths remain in a private run directory outside Git so
the cases stay reusable for future runs.

## What ran

- 28 private held-out synthetic cases: 7 scenarios (short answer, implementation
  handoff, incident update, experiment report, investigation, academic synthesis,
  research idea) crossed with 4 domain suites, all passing strict `init`
  validation;
- one model alias, `gpt-5.6-sol`, through Codex CLI `0.149.0`, executable pinned by
  SHA-256, provider revision unpinned;
- 2 conditions (baseline workspace without the adapter; framework workspace with
  the Skill and `AGENTS.md` adapter installed) × 3 independent fresh-context
  repeats (seeds 7/11/13) = 168 real host executions, each with a frozen host plan
  and execution receipt;
- treatment pinned to repository commit
  `9ee0d15e3babc0cb69402cf408df5e2d96a258f6` (post-`v0.4.1`);
- blind rating of all 84 randomized A/B pairs by two independent non-OpenAI model
  raters (Claude and Kimi model families), 7 dimensions plus comprehension probes,
  critical errors, and semantic slots; ratings frozen before unblinding;
- paired bootstrap aggregation with 10,000 resamples against the preregistered
  thresholds.

## Blind-rating outcome

The framework condition rated higher on 6 of 7 quality dimensions (largest gaps:
visual display fitness 5.00 vs 4.62, information architecture 4.93 vs 4.57); the
primary composite difference was `+0.214` with a bootstrap 95% CI of
`[0.015, 0.478]`, so the quality gain is real but below the preregistered `+0.3`
primary-gain threshold. Visual selection precision and recall were both 1.0, and
rater agreement-within-one was 1.0.

The claim gates still failed decisively. Median output-token overhead was `8.1x`
(p90 `27.8x`) against a `1.15x`/`1.3x` budget; concision was the only losing
dimension; semantic density per 1,000 output tokens collapsed from 20.3 to 1.9;
and 22 critical-error records concentrated in one failure mode: some framework
responses delivered a pointer to a saved report file (exposing a local absolute
path) instead of the report itself.

Accordingly, `study-summary.json` is gated to `insufficient_evidence` and
`effectiveness_claim_eligible: false`.

## Interpretation boundary

Cases were synthetic and privately authored; raters were models, not humans; the
baseline used a same-account workspace without an external isolation receipt; the
global instruction policy was `unverified`; the provider revision was unpinned; the
long-soak stratum did not run. One global-instruction language contamination on
the first probe pair was quarantined and re-run under a neutral override applied
identically to both conditions.

## Follow-up driven by this study

The two decisive failure surfaces led to targeted contract changes, verified by
the deterministic test suite rather than re-claimed as effectiveness evidence:

1. every adapter and the Skill now require the final response to contain the
   report itself — a saved-file path or pointer is not a deliverable, and local,
   scratch, and checkpoint paths must not be exposed to the reader;
2. ceremony is now proportional — short single-session answers skip checkpoints,
   draft files, and script audits, reserving the file-backed bookend for long,
   multi-session, multi-agent, or durable-artifact work.

Two single post-fix integration probes reused frozen study prompts against the
updated contract: the short-answer unit answered directly with no checkpoint or
audit ceremony (394 output tokens versus 1,225-1,452 under the old contract and
40-41 for baseline), and the image-embedding unit delivered the report inline with
a workspace-relative figure path instead of a pointer. These are activation
signals with n=1 each, not effectiveness evidence. Re-running this study design
against the updated contract remains the verification path for any future
effectiveness claim.
