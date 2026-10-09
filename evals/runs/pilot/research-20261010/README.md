# Public-paper research reporting development probe — 2026-10-10

Actual generation exposed a gap that structural checks missed: a paper report
could explain the evidence accurately, then end with a proposed comparison that
would not tell the lab what to decide. Independent review found this in both DPO
reports. The framework now requires controls, a readout and result-dependent
decisions when proposing an experiment. A completed synthesis can instead end
with its warranted implication. In the targeted recheck, the framework report did
the latter and passed; the baseline retained the vague proposal and required
revision. This is adaptive development feedback, not evidence of a general gain.

## Source and routing repairs

The two tasks discuss DPO (arXiv:2305.18290v3, Sections 3–4 and 6–7) and RLiable
(arXiv:2108.13264v4, Sections 3–5 and Figures 2, 5–6). Both use independently
paraphrased, selected facts with versioned links and locators in
[`presentation-cases.json`](../../../presentation-cases.json). They test synthesis
of a supplied packet, not autonomous reading of a complete unseen paper.

An initial source review found that the DPO packet omitted its direct human
comparison and limited distribution-shift result, and that the RLiable packet
overstated the implication of crossing profiles. Those omissions could bias a
cautious report. The initial run remains frozen privately; its reports are not
used as a fair comparison. The packet was corrected and every condition rerun.
The corrected source packet and hand-authored fixtures passed independent review.

Routing also misclassified these discussions when experimental or review words
appeared in the attached facts. Mode and module selection now use the request
before the standard fact-packet sections, including the short-request fallback.
Material can still identify a research profile. Referencing a paper's figure or
table no longer automatically requests that display in the report. This remains
an intent heuristic, not a prompt-isolation guarantee.

## What ran and what review found

The corrected two-case pilot generated baseline and framework reports through
Codex CLI 0.159.2, using the gpt-6.1-sol alias, English prose, a 400-word request
and one independent repeat per condition. Treatment was pinned to
`b1d760e55cfad83d4c4b78ce9350dc014bef7a26`. All four controller records validated
and passed the declared structural checks. A different model, gpt-6-astra,
reviewed each report with its condition label hidden, without assigning preference
scores or human ratings.

Both DPO reports preserved the theory, positive results and evidence limits, but
proposed follow-ups lacked a result-dependent decision: R4 required revision.
Both RLiable reports passed the scientific checks and completed the synthesis
without proposing an unnecessary experiment. The earlier DPO failures remain
recorded; structural success was not reclassified as semantic success.

After the academic-synthesis rule was strengthened, a targeted DPO rerun used the
same neutral request and fact packet in both conditions, with treatment pinned to
`9b0aae00b78b34c9664d79528b07d94e73dd5106`. Both records validated. Independent
condition-masked review passed the framework's completed synthesis; the baseline
still needed revision for its optional experimental proposal. This recheck was
chosen after inspecting a public failure and is not an independent holdout.

## Cost, receipts and claim boundary

[`pilot-summary.json`](pilot-summary.json) and
[`followup-pilot-summary.json`](followup-pilot-summary.json) are sanitized
controller aggregates. In the two-case pilot, observed output-token overhead was
about +208% at the median of the two paired ratios. This is whole-turn host usage,
including tool-command generation, not a measure of report prose length. The
framework also received a study-only checkpoint instruction. These observations
support no efficiency claim and do not isolate ordinary short-answer overhead.

The controller observed a Skill read in each framework unit and none in baseline.
It credited no verified checkpoint audit in either phase. Compound command
execution does not meet the adapter's exact receipt grammar; local audit activity
must not be promoted to controller-verified checkpoint evidence.

Both aggregates remain `insufficient_evidence` with
`effectiveness_claim_eligible: false`. Cases and strong hints were public, sample
sizes were small, the provider revision was unpinned, output tokens had no enforced
provider cap, global instructions were unverified, and workspaces shared one
account. No human rating batch was frozen, no long-context or compaction condition
was tested, and adaptive fixes reused the case. No quality effect size or win rate
is estimated.

Raw prompts, responses, transcripts, host plans, checkpoint artifacts, review
findings and assignment keys remain private outside Git. The public semantic
summary binds reviewed response sets by digest and records the findings without
publishing those artifacts. Further effectiveness work requires the independent
held-out design and human judgments in [BENCHMARK.md](../../../../BENCHMARK.md).
