# Review report

Use this mode to assess code, a change set, design, document, dataset, artifact, or
scholarly work. The review is evidence-driven and review-only unless the user also
authorizes fixes.

## Semantic order

1. **Verdict or findings:** put actionable problems first, ordered by material
   severity or decision impact. If no actionable finding survives review, say so.
2. **Scope:** identify the reviewed target, version or diff, criteria, and exclusions.
3. **Finding detail:** for each finding, give a stable ID, severity, confidence,
   locator, evidence, impact, and the smallest useful correction or question.
4. **Positive evidence:** note strengths when they affect the verdict or should be
   preserved; do not use praise to dilute a material finding.
5. **Coverage and boundary:** record tests or surfaces reviewed, areas not checked,
   rejected candidates, and residual uncertainty.
6. **Decision support:** state whether the evidence supports pass, conditional pass,
   revision, or block when the review context defines such a verdict.

## Finding discipline

- A finding must be specific, consequential, and supported by inspectable evidence.
- Describe severity through concrete impact and realistic reachability, not a label
  alone.
- Calibrate confidence from the evidence available and missing proof.
- Use precise locations such as file and line, section, page, table, figure, record,
  or timestamp.
- Do not combine independent issues merely to shorten the report.
- Do not invent a requirement. Connect criticism to the user's criteria, documented
  contract, accepted standard, or demonstrated harm.
- If an apparent issue is ruled out, include it only when the counterevidence matters
  to coverage or future review.

## Review variants

For scholarly review, keep the neutral summary separate from critique and assess
soundness, evidence, novelty context, clarity, limitations, and reproducibility.
For code or change review, emphasize correctness, regressions, security boundaries,
tests, API effects, and maintainability. For visual or document review, bind findings
to exact pages, figures, screenshots, or sections.

## No-finding reports

Do not claim the target is defect-free. State that no actionable finding was found
within the reviewed scope, then name material coverage or verification gaps.

## Avoid

- Generic comments that could apply to any target.
- Style preferences presented as defects without a governing convention or impact.
- A summary of changes in place of review findings.
- Applying a fix, merge, publication, or external action without authorization.
