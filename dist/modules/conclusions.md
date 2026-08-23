# Display module: conclusions

# Conclusions module

Load this module when the report must interpret evidence, make a recommendation, or
state a scientific, technical, operational, or business conclusion. A conclusion is
an evidence boundary, not a more emphatic summary.

## Conclusion chain

Use this order, visibly or implicitly:

1. **Evidence:** state the verified observation or result.
2. **Interpretation:** explain the relationship the evidence supports.
3. **Conclusion:** answer the report's question at the supported scope.
4. **Boundary:** state uncertainty, exceptions, assumptions, and what the evidence
   does not establish.
5. **Action:** give a recommendation, next test, decision, or monitoring point only
   when warranted.

## Claim calibration

- Label material statements as observation, verified fact, inference, hypothesis,
  recommendation, or unknown when readers could confuse them.
- Match the conclusion to the evaluated population, datasets, systems, time period,
  protocols, comparison set, and deployment setting.
- Separate descriptive, diagnostic, predictive, causal, and normative claims.
- A correlation, temporal sequence, chart pattern, or ablation alone does not prove a
  complete causal account.
- A larger mean does not prove statistical significance; statistical significance
  does not prove practical value.
- A null or inconclusive result is a reportable outcome. State power and evidence
  limitations instead of converting it into confirmation.
- Present trade-offs, exceptions, failure boundaries, and contradictory results that
  materially change the answer.

## Comparative language

Use `better`, `outperforms`, `best`, `superior`, and `state of the art` only with an
explicit metric, direction, benchmark or task, protocol, comparison set, and verified
result. Prefer `highest observed mean` when uncertainty or significance remains
untested. Avoid universal winners when the evidence shows an accuracy, cost, latency,
robustness, or deployment trade-off.

When metrics trade off, do not call one method the `stronger balance`, `best
trade-off`, or preferred Pareto point without a stated utility function, constraint,
or decision threshold. Report the non-dominated choices and make any conditional
recommendation explicit.

## Confidence

State confidence only when it helps a decision. Ground it in evidence quality,
coverage, consistency, directness, and unresolved alternatives. Do not use a numeric
probability unless the scale is calibrated or derived.

## Recommendations

Connect each recommendation to the conclusion and state preconditions, downside,
owner, or verification condition when material. Distinguish a recommendation from
authorization or an accepted decision.

## Avoid

- Repeating every result in the conclusion.
- Introducing new evidence after the conclusion.
- Hiding caveats in an appendix when they reverse the headline.
- `Clearly`, `obviously`, or certainty language in place of evidence.
