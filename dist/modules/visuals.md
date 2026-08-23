# Display module: visuals

# Visuals module

Load this module only when a figure, chart, image, screenshot, diagram, or qualitative
set makes an important relationship easier to understand than prose or a table.
Every visual must support a named report claim or observation.

## Visual contract

Before rendering, define:

- the analytical or communicative question;
- the one-sentence takeaway the evidence supports;
- data or image source, scope, grain, filters, time window, and comparison basis;
- selected visual family and why it fits the relationship;
- units, denominator, uncertainty, scale, ordering, and reference lines when relevant;
- caption, alternative text, and textual fallback;
- delivery surface and fallback if the visual cannot render.

Keep this contract in working notes unless methodology changes interpretation.

## Selection defaults

| Relationship | Prefer | Do not default to |
|---|---|---|
| Category comparison | Sorted bar or dot plot | Pie or decorative cards |
| Continuous change over time | Line plot with sufficient observations | A line through a few unrelated periods |
| A few discrete periods | Grouped bar, slope, or exact table | Underpowered trend line |
| Distribution | Histogram, box plot, or interval plot | Mean-only bar |
| Two numeric variables | Scatter at one consistent grain | Bubble plot with an irrelevant third encoding |
| Part-to-whole | Stacked or 100% stacked bar | Many-slice pie |
| Additive change | Waterfall | Non-additive waterfall |
| Process or dependency | Small flow, sequence, or tree diagram | Diagram for a one-step fact |
| Exact lookup | Table | Chart that obscures values |

Treat observation-count heuristics as defaults, not scientific laws. If evidence is
too sparse for the selected form, collect a more appropriate grain once or switch to
a more honest display.

## Charts

- Match title, axes, legend, marks, and caption to the supported claim.
- Standard magnitude bars start at zero. If a delta-focused display uses a narrowed
  scale, make the scale break or focused range unmistakable and show exact values.
- Keep comparable charts on consistent scales unless a difference is disclosed.
- Define uncertainty bands or error bars, including statistic, sample count, source
  of variability, and computation.
- Put the reader-facing interpretation immediately before or after the figure.
- Do not use color alone; add direct labels, line styles, markers, ordering, texture,
  or another redundant cue.

## Images and screenshots

- Give every image a stable figure ID, purpose, caption, concise alternative text,
  and source or artifact link.
- For machine-verifiable Markdown, place the image at column zero on one independent
  top-level line, with a blank line or document boundary on both sides. Keep its alt
  text and target on that line. Use a nonempty local path or an absolute HTTP(S)
  URL; pure fragments, query-only targets, and data URIs are outside the auditable
  subset. Percent-encode spaces and parentheses in targets instead of relying on
  backslash escapes. Do not place a report image inside a list, block quote, HTML
  block, or code span/fence. Place report images before any raw contiguous
  triple-backtick/triple-tilde run or paragraph-sensitive raw HTML tag marker. To
  avoid divergence from a full CommonMark parser, the audit grants no required-image
  credit after the first such marker, even when a renderer might show a later image;
  link later fenced logs/snippets instead. CommonMark block tags and completed raw
  blocks remain block-scanned, and URI autolinks do not count as type-7 tag markers.
  The strict renderer emits none of the pre-image ambiguous forms. The audit's
  fail-closed broad gate treats every unescaped `![` and every raw HTML opening tag
  as a potential visual source even inside literals; this also rejects harmless raw
  tags because inline CSS and custom elements can render images. Write examples as
  `\![...]` or entity-encode the opening `<` when no visual is intended.
- State cropping, resizing, annotation, stitching, enhancement, thresholding, or
  other material processing. Preserve access to the unmodified original when safe.
- Use consistent crop, scale, and ordering for side-by-side comparisons.
- Bind annotations to the exact region they explain without hiding evidence.
- For qualitative results, state the selection rule and show important failures or
  exceptions as well as representative successes. Do not cherry-pick silently.
- A screenshot proves only visible state at the captured time; name behavior or
  accessibility properties that still require runtime testing.

## Accessibility and fallback

Alternative text identifies the visual and its purpose. A complex graph or diagram
also needs adjacent prose or a structured data table covering the essential values,
relationships, and trend. For Mermaid, include `accTitle` and `accDescr` when the
renderer supports them. Ensure text and graphical objects remain readable at the
delivered size and in grayscale or equivalent non-color encoding.

## Avoid

- Decorative visuals, redundant legends, gradients, 3D effects, and chartjunk.
- A figure with no adjacent interpretation.
- Inferring a hidden cause from a visual pattern alone.
- Flattening an interactive report into an image as the only deliverable.
- Claiming a visual rendered without inspecting the delivered surface.
