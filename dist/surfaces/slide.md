# Surface guide: slide

# Academic slide surface

Use the slide surface for a live or self-navigated research presentation. Select a
narrative preset from the actual audience and purpose; do not convert every report
heading into one slide.

## Narrative presets

- **Paper talk:** problem and gap -> thesis -> mechanism -> decisive evidence ->
  exceptions/limitations -> takeaway.
- **Research progress:** objective -> last decision -> new evidence -> what changed
  -> blocker or uncertainty -> next experiment/help needed.
- **Experiment review:** research question -> protocol comparability -> main result
  -> variability/exceptions -> decision and next test.
- **Idea pitch:** current limit -> hypothesis -> mechanism -> closest alternative ->
  decisive experiment -> risks and evaluation gates.

## Slide contract

- Give each evidence slide a sentence assertion as its title and visual or tabular
  evidence that supports that assertion.
- Keep one primary message per slide. Move derivations, dense tables, and backup
  ablations to appendix slides.
- Put metric direction, units, protocol, sample size, and uncertainty on the slide
  where a quantitative claim is made.
- Use direct labels and accessible contrast; do not rely on color or animation
  alone. Preserve alt text or an adjacent text account for material visuals.
- Put a short source locator on evidence slides and full references in the ending or
  notes. Speaker notes may hold delivery cues but not evidence absent from the slide
  or linked artifact.
- Rehearse against the actual time budget; slide count is an output of the story and
  evidence density, not a universal quota.

## Asset selection

Use `template academic-talk-html` for a dependency-free HTML/PPT-style deck or
`template academic-talk-revealjs` when Quarto/reveal.js is available. Retrieve one,
not both, unless the user explicitly requests multiple formats.

Provenance: Assertion-Evidence presentation guidance, Reveal.js, and Quarto
presentation documentation. See the portable `UPSTREAM.md`; the source repository's
detailed adoption ledger is `docs/TEMPLATE-SOURCES.md`.
