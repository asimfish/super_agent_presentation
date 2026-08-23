# Investigation report

Use this mode for diagnosis, root-cause analysis, behavior probes, data inquiries, or
other work whose primary output is a supported finding rather than an implemented
change.

## Semantic order

1. **Finding:** put the strongest verified answer first. If there is no conclusive
   answer, state the leading evidence and unresolved question.
2. **Scope and question:** define the behavior, population, time window, or system
   boundary investigated.
3. **Evidence:** summarize the decisive observations, reproductions, measurements,
   or source records.
4. **Analysis:** explain how the evidence supports the finding; distinguish cause,
   contributing factor, correlation, and coincidence.
5. **Alternatives:** record material hypotheses ruled out, still plausible, or not
   tested when they affect confidence.
6. **Boundary and next step:** state evidence gaps, confidence, and the smallest next
   test or action.

## Investigation discipline

- Preserve the observed symptom separately from its explanation.
- Do not call a hypothesis the root cause until a causal path is supported and a
  relevant validation, counterfactual, or fix check has been performed when
  feasible.
- Record failed attempts only when they narrow the search, reveal a boundary, or
  prevent repetition. Do not reproduce the entire command history.
- State what was held constant in a comparison or probe.
- When a result is negative, name the scope in which no issue or effect was found;
  do not generalize absence beyond inspected coverage.
- If investigation was read-only, do not imply that the issue was fixed.

## Evidence presentation

Use a compact case matrix when several probes differ by one controlled variable.
Use a timeline only when sequence changes interpretation. Link raw logs or scripts
rather than pasting them into the main report.

## Avoid

- A finding based only on the most recent error line when an earlier broken control
  is known.
- Generic `likely` language without explaining supporting and missing evidence.
- Treating a screenshot, chart, or passing smoke test as proof of an unseen cause.
- Recommending a fix as though it has already been implemented or validated.
