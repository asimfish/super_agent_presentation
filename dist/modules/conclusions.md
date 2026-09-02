# Display module: conclusions

# Conclusions module

Load this module when the report must interpret evidence, make a recommendation, or
state a scientific, technical, operational, or business conclusion. A conclusion is
an evidence boundary, not a more emphatic summary.

Do not load it when the selected primary mode already provides the needed conclusion
protocol. In particular, `experiment-report` already covers verified results,
interpretation, uncertainty, scope, null findings, trade-offs, and the next
experiment. Compose this module with that mode only for a distinct decision or
recommendation policy that the experiment protocol does not cover.

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

## Statistical claims

- Report exact p-values as graded evidence, not a significant/non-significant
  binary; never read `p > 0.05` as proof of no effect.
- Pair any test with an effect size and interval estimate; a p-value measures
  neither magnitude nor importance.
- Report risks and rates as absolute change with the base rate, not only a
  relative ratio.
- Match causal language to the design: `associated with` for observed
  relations, `predicts` for predictive use, causal verbs only with
  randomization or a stated identification strategy. Do not attach causal
  advice to associational evidence.
- Label findings formed after seeing the results as exploratory; the same data
  cannot generate and confirm a hypothesis.
- When several comparisons feed one conclusion, name the comparison family and
  the correction applied, or why none was needed.

## Explanation and language

- Separate explanation from speculation: a mechanism claimed for a result needs
  its own evidence (an ablation, an intervention, a diagnostic); otherwise write
  `we speculate` and keep the speculation out of the title, summary, and abstract.
- Attribute gains to their source. When a system changes several things at once,
  do not credit the headline component until the other changes are held fixed.
- Describe what the system does against a defined task instead of what it
  `understands`, `believes`, `wants`, or `reasons about`. Suggestive words
  (`human-level`, `superhuman`, `emergent`, `first to`) need the defined
  comparison, population, and metric in the same sentence.
- Equations, notation, and technical terms earn their place by carrying the
  argument; decorative formalism and redefined common words lower precision.

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
