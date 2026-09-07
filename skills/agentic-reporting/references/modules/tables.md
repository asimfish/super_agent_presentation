# Tables module

Load this module for exact lookup, compact comparison, experimental settings, audit
detail, action tracking, or risk registers. Prose suits a few facts; a chart suits
shape or relationship.

## Table contract

Before drafting, define the table's question, row population, column meanings,
comparison scope, units, time window, missing-value semantics, sort order, and source.
Every column must help answer the question or audit the result.

## Structure

- Give the table a short title or nearby sentence that defines scope.
- Use explicit row and column headers. Keep header hierarchy simple; split a table
  when merged or multi-level headers would blur relationships.
- Put units and metric direction in headers when compact and unambiguous.
- Align numeric values consistently and use consistent precision within a metric.
- Define abbreviations, symbols, bolding, arrows, uncertainty, and footnotes.
- Keep a self-contained caption or note for a table that may be read out of context.
- Provide a nearby takeaway; the table does not write its own conclusion.

## Quantitative comparisons

- Compare or rank rows only under materially comparable task, data, protocol,
  metric, and resource conditions.
- Separate incompatible protocols into different tables or clearly separated groups.
- Report the number of runs or observations and define `±`, intervals, or quantiles.
- Use bold or rank markers only for a stated comparison set. Do not imply significance
  or practical dominance from boldface.
- Preserve relevant baselines, targets, previous-period values, or denominators.
  When rows are compared against a baseline row, add a delta column (absolute,
  plus relative where the scale allows) so readers never compute differences
  themselves; if the table is already wide, state the deltas in the next sentence.
- Use appropriate significant digits; false precision reduces trust.
- Mark numbers cited from other sources apart from numbers reproduced under this
  protocol; they do not share one ranking.
- Prefer horizontal-only rules on print surfaces; avoid vertical rules.

## Missing and special values

Define separate representations for:

- a measured zero;
- missing or unavailable data;
- not reported by a source;
- not run or failed;
- not applicable.

Never sort or calculate with a missing value as zero. Define any dash beside the
table.

## Density and accessibility

- Keep narrative tables scannable; move long-tail rows, raw data, or audit detail
  to an appendix or linked artifact.
- Avoid prose-heavy cells and code blocks inside tables.
- Do not use color, icons, or font weight as the only status signal.
- On narrow surfaces, prefer fewer columns, split tables, or a vertical record list.
- Give each cell one clear header association; explain complex relationships in
  text.

## Avoid

- A wide summary table used in place of an actual explanation.
- Mixed units or denominators in one unlabeled numeric column.
- Global rankings across different tasks, datasets, or evaluation conditions.
- Repeating the same numbers across displays without a distinct purpose.
