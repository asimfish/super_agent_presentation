# Response to reviewers: showcase paper 4127, gated diffusion policies

All facts below are synthetic showcase data; they demonstrate the template, not a
real submission.

## To the editor / area chair

We thank the reviewers for their careful reading; every finding below is
answered point by point. The theme of this revision is
tightening the evidence behind the safety claim: we added a five-seed variance
study (new Table 3), replaced the bar chart of means with interval plots
(revised Figure 2), and rewrote the causal wording in Section 5.2. Reviewers 1
and 2 disagree on whether the gating ablation is necessary; we ran it and report
it either way (new Section 4.4).

## Global responses

Both reviewers asked how many runs support the headline numbers. All headline
results now aggregate five seeds; Table 3 reports mean, standard deviation, and
a 95% bootstrap interval per task. Single-run numbers survive only in the
appendix and are labeled as such.

## Reviewer 1

### Comment 1.1

> The 12% improvement in Table 2 has no uncertainty estimate. One seed is not
> enough for a claim of this size in this benchmark.

Agree, and revised. Table 2 is superseded by Table 3, which reports five seeds
per cell. The improvement is 9.8% with a 95% interval of 4.1 to 15.2 percentage
points, so the direction of the claim holds while the original point estimate
was optimistic. Section 4.2 now states the revised number.

### Comment 1.2

> Section 5.2 says the gate "causes" the recovery behavior, but the study is
> observational on logged rollouts.

Agree, and revised. Section 5.2 now says the gate activation is associated with
recovery onset within two steps, and the causal reading is explicitly deferred.
The one interventional result we do have, the gate-off ablation in Section 4.4,
is now cited there as the only causal evidence.

## Reviewer 2

### Comment 2.1

> Why is there no ablation of the gating threshold? The method section presents
> it as the central contribution.

Agree, and added. New Section 4.4 sweeps the threshold over five values on both
simulation suites. Success is flat within 1.3 percentage points across the
middle three values and degrades at the extremes, which supports the default
and bounds its sensitivity. Runtime cost of the sweep is reported in the same
section.

### Comment 2.2

> The related-work section should cite the earlier energy-based gating line of
> work; the omission makes the novelty claim look stronger than it is.

Partially agree. Section 2 now cites and contrasts that line: it gates at the
trajectory level while our gate acts per action chunk, and neither of its two
public implementations handles the multimodal case in our Section 3 setting.
The novelty sentence in the introduction was narrowed accordingly.

## Summary of changes

- Table 3 and Section 4.2: five-seed aggregates with bootstrap intervals.
- Figure 2: interval plot replaces the bar chart of means.
- Section 4.4: new gating-threshold ablation with runtime cost.
- Section 5.2: associational wording; causal claim scoped to the ablation.
- Section 2 and introduction: added the energy-based gating citations and
  narrowed the novelty sentence.
- Line numbers above refer to revision 2 of the manuscript.
