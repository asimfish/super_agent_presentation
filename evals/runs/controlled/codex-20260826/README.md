# Codex held-out controlled study — 2026-08-26 (v2 re-run)

This directory contains only the controller-generated aggregate summary
(`study-summary.json`) from the second private controlled study. It re-runs the
exact `codex-20260825` design against the fixed contract, so the two runs are
directly comparable. Case texts, prompts, responses, transcripts, host plans,
rating files, and assignment keys remain in a private run directory outside Git.

## What changed between the runs

The treatment is pinned to commit `f989e026e45b0bc6064df2eb87994491e0bfc82d`,
which includes the two contract fixes motivated by the first run (the final
response must contain the report itself, and ceremony is proportional to task
size) plus the absorbed reporting standards (BLUF, SBAR, Minto, plain-language,
scanning research, SRE postmortems, IBCS) and the readability audit warnings.
Everything else — the 28 frozen held-out cases, Codex CLI `0.149.1` with a
SHA-pinned executable, one unpinned `gpt-5.6-sol` revision, 2 conditions × 3
fresh-context seeds = 168 executions, 84 blind pairs, two independent
non-OpenAI model raters (Claude and Kimi families), ratings frozen before
unblinding, paired bootstrap with 10,000 resamples — matches the first run.

## Blind-rating outcome

The primary preregistered quality gate passes for the first time: the primary
composite difference is `+0.315` with a bootstrap 95% CI of `[0.110, 0.579]`,
clearing the `+0.3` threshold with the CI excluding zero (first run: `+0.214`,
gate failed). The framework again rated higher on 6 of 7 dimensions, and
concision — the losing dimension in the first run — is now at parity (4.64 vs
4.65). Pair preference moved from 56 wins / 68 ties / 44 losses to 76 wins /
45 ties / 47 losses (win rate 33.3% → 45.2%), still below the 65% win-rate
gate, with the loss rate at 28.0% against a 15% cap.

Of the 46 critical-error records, 45 sit on the baseline side and 1 on the
framework side. Both raters independently flagged the same baseline responses
on figure and handoff tasks for delivering a pointer to a saved report file —
leaking a local absolute path — instead of the report itself. A scan of all
blind sides confirms zero framework responses contain an absolute local path
in either study, while 11 baseline responses do in this run. The single
framework record is a one-rater `fabricated_evidence` flag on one pair (an
inferred "prior client-rendering path" not present in the supplied facts); the
second rater scored the same response clean.

The efficiency gates still fail and are structural to the design: the
framework produces full reports where the baseline often answers in a line, so
median output-token overhead stays at `7.9x` (p90 `26.7x`) against a
`1.15x`/`1.3x` budget, and semantic density per 1,000 output tokens remains
19.9 versus 1.9. Machine invariants pass at 96.1% against a 98% gate (30 of
396 `required_regex` checks missed on phrasing). The long-soak stratum is
absent from this design by construction.

Accordingly, `study-summary.json` remains gated to `insufficient_evidence` and
`effectiveness_claim_eligible: false`.

## Correction to the first run's narrative

The `codex-20260825` README originally attributed its 22 pointer-style
critical errors to framework responses. Deblinding shows all 22 sat on
baseline sides in that run as well; the framework side had zero critical
errors in the first run. The first run's README has been corrected. The
contract fixes remain justified as defense-in-depth (old-contract probes did
produce file-pointer finals), and this run validates them under blind rating.

## Telemetry note for the next run

Under the proportional-ceremony contract, 79 of 84 framework units correctly
skipped the final script audit, but `final_audit_passed` telemetry records a
skip as not-passed (fresh pass rate 5.95%). The telemetry needs a
skipped-by-contract state before the audit-contract prerequisite can be
evaluated meaningfully.

## Interpretation boundary

Cases were synthetic and privately authored; raters were models, not humans;
the baseline used a same-account workspace without an external isolation
receipt; the global instruction policy was `unverified`; the provider revision
was unpinned; rater timing was approximated from output-file timestamps. This
run informs the internal claim gates only and cannot support the public
effectiveness claim.
