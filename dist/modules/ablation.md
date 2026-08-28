# Display module: ablation

# Ablation module

Load this module when the report designs or presents ablations, component
contribution studies, or decoupling experiments.

## Design

- Compare each variant against the full system, not the baseline; baseline
  comparison belongs to the main results. Change one component per variant and
  hold data, seeds, budget, and evaluation fixed.
- Name the form and match it to the question: leave-one-out asks whether a
  component is necessary and misses redundant pairs; replacement with a simpler
  implementation controls parameter and compute capacity; cumulative addition is
  order-dependent, so state the insertion order and re-check key components with
  a leave-one-out variant.
- Component effects are not additive. For suspected interactions, run the
  factorial cells (full, minus A, minus B, minus both) and report the
  interaction instead of assuming independence. A large gap between summed
  single-component effects and the total gain signals uninvestigated
  interactions.
- State the variant tuning policy: re-tuned per variant, or the same search
  space and budget as the full system. Never pair a tuned full system with
  untuned variants.
- Prefer a negative control (a random or dummy component) when claiming a
  specific mechanism rather than generic capacity.

## Reporting

- The full-system row must match the main results table under the same
  protocol; explain any difference.
- Layouts: a full-system top row with one removal per row and a delta column
  for leave-one-out; a checkmark matrix of combinations for factorial results,
  anchored by baseline and full-system rows and restricted to informative rows.
- Choose seed or trial counts from the expected effect size; a handful of seeds
  cannot support a superiority claim. Comparing many rows against the full
  system is multiple comparison; account for it before claiming per-component
  significance.
- When a winner depends on tuning or compute budget, report performance versus
  budget rather than one selected point.

## Avoid

- Ablating against the baseline while calling it an ablation of the full system.
- Presenting cumulative gains as independent per-component contributions.
- A variant row whose training or evaluation setup silently differs from the
  full system in more than the named component.
