# Research reporting: make an argument the lab can examine

The aim is to help a supervisor or colleague judge what has been learned and
which decision the evidence supports. More metrics, longer methods sections,
and more formal vocabulary do not establish that judgment. The rules below are
this project's design choices for doctoral research communication, not a
universal PhD assessment standard.

## What the reader should be able to reconstruct

| Reader's question | Useful answer | Common failure |
|---|---|---|
| Why did we do this? | A research uncertainty, assumption, or limitation that matters | A list of runs or papers read |
| What did we learn? | An answer bounded to the tested setting, including an unresolved answer | A list of increased and decreased scores |
| Why does that follow? | The decisive comparison, its controls, and the interpretation | Repeating the table or supplying a plausible causal story |
| What else could explain it? | The material alternative still open and the counterevidence | Treating an ablation as proof of mechanism |
| What changes now? | A justified choice or a test whose outcomes lead to different choices | More experiments without a discriminating question |

These are reasoning roles. A short update can cover them in two paragraphs;
a theory report may use a proposition, assumptions, proof sketch, and implications
instead of experiments. Do not fill every cell with invented content. A completed
answer does not require an artificial next experiment.

## Write around the uncertainty

For an experiment, answer the question first, then explain the comparison that
changes the working view. Distinguish three kinds of statements in normal prose:
what was measured, what is inferred, and what is proposed. An observed score gain
can justify investigating a method without proving its explanation.

For research progress, relate the new evidence to the previous hypothesis or
decision when that history is documented. A failed control can be the most useful
weekly result because it rules out a route. Work still running should be reported
as work still running; do not turn activity into knowledge gained.

For a paper discussion, explain the problem's bottleneck, the method's proposed
move, and the experiment that tests it against the closest alternative. Keep the
authors' explanation distinct from demonstrated evidence and your assessment.
For several papers, organize around a disagreement or assumption rather than
giving each paper a disconnected summary. A source gap is not proof of novelty.

For an idea, explain why the proposed change could address the bottleneck, then
name a test that separates it from a plausible alternative. An engineering
combination may be useful without being a new scientific explanation.

## Put numbers where they do work

Keep the decisive result, comparator, uncertainty, and counterexample near the
claim. Explain the relationship once. Move complete sweeps, logs, run accounting,
and detailed methods to a labeled appendix or inspectable artifact. The main
argument must still preserve the comparison basis: population, budget, units,
selection, independent observations, and interval meaning when material.

An editor may move complete supporting tables. It must not discard unique values,
drop failed controls, remove a denominator, or detach a claim's scope. A shorter
report obtained by hiding inconvenient evidence is a failed edit.

The difference between 0.410 and 0.450 matters here because the same method falls
from 0.360 to 0.330 on a shifted corpus. Together they weaken the tested transfer
hypothesis; listing all four numbers alone does not explain that implication.
This is a synthetic teaching example, not an empirical claim about a real method.

## Review reasoning separately from style

The existing CLI paths remain the entry points:

```bash
python3 skills/agentic-reporting/scripts/reportctl.py exemplar experiment-report
python3 skills/agentic-reporting/scripts/reportctl.py review-prompt \
  --file examples/research-reporting/transfer-report.md \
  --facts examples/research-reporting/transfer-facts.md --mode experiment-report
python3 skills/agentic-reporting/scripts/reportctl.py edit-prompt \
  --file examples/research-reporting/transfer-report.md --mode experiment-report
```

`review-prompt` adds R1-R5 scientific judgment checks to research modes and a
conditional check for research status updates. Evaluate each dimension as
supported, needs revision, not applicable, or unverifiable, quoting the passage
and evidence behind the verdict. Do not add the dimensions into a synthetic
quality score. A persuasive invented mechanism fails source fidelity regardless
of how polished the report sounds. A negative result can pass.

`edit-prompt` preserves the scientific argument and can relocate supporting data.
It cannot supply reasoning that the author never wrote. Return a measurement-only
draft to the author for substantive revision before expecting style editing to
solve it.

Structural audit cannot determine whether an explanation is warranted or an
experiment distinguishes hypotheses. Use an independent model or human for the
semantic pass and check original evidence. Without a fact sheet, source fidelity
remains unverified even if internal reasoning passes.

## Evidence and limits of this change

[The paired examples](../examples/research-reporting/README.md) contain synthetic
fact sheets, measurement-only drafts, and hand-authored research arguments for
transfer failure, a compute confound, and an inconclusive comparison. They test
whether the review workflow distinguishes information from interpretation. They
are public teaching fixtures, not held-out model evaluations or evidence of a
measured readability improvement.

This design draws on claims/scope alignment and explicit experimental assumptions
in the [NeurIPS Paper Checklist](https://neurips.cc/public/guides/PaperChecklist),
and the distinction between explanation and speculation in
[Lipton and Steinhardt's primary essay](https://arxiv.org/abs/1807.03341).
The argument-first structure and doctoral audience choices are our synthesis.
Full effectiveness claims still require the controls in
[BENCHMARK.md](../BENCHMARK.md), including independent human judgments and task
fidelity; passing CLI tests does not establish those claims.
