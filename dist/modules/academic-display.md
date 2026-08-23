# Display module: academic-display

# Academic display module

Load this module when scholarly works themselves are reader-facing objects. It
governs bibliographic identity and claim presentation; use the evidence module for
general source binding.

## Paper identity

For each focal work, provide the smallest useful identity record:

- stable source ID;
- exact title;
- authors or a concise author display when space is limited;
- venue and year, preserving preprint versus published status;
- DOI, official proceedings page, or primary paper URL;
- version or access date when the work may change.

Do not fabricate missing metadata. Distinguish an accepted paper, workshop paper,
preprint, technical report, and unpublished manuscript.

## Single-paper display

Present, in a compact order:

1. one-sentence thesis or neutral contribution summary;
2. research question and motivation;
3. method, assumptions, inputs, supervision, and outputs;
4. evaluation protocol and comparison basis;
5. main evidence with section, table, figure, or page locators when needed;
6. limitations, failure boundaries, and untested claims;
7. relation to the reader's question or project.

Keep a neutral summary separate from critique. The paper's claims are not established
facts merely because they appear in an abstract or conclusion.

Keep `the paper does not report X` distinct from `X was not performed`, and keep an
analyst-identified evidence gap distinct from a limitation the authors explicitly
acknowledge. Use the weaker statement unless the primary paper supports the stronger
one.

## Multi-paper display

- Organize by a meaningful axis such as problem, method, assumption, supervision,
  data, metric, compute, or deployment setting; avoid one disconnected paragraph per
  paper when synthesis is possible.
- Use a comparison table only for shared axes and comparable fields.
- Use a claim-evidence map for claims supported by different source subsets.
- State disagreement and explain whether it may arise from protocol, population,
  metric, resource, or assumption differences.
- Describe the source set as systematic, curated, convenience-based, or incomplete.

## Results and claims

For a reported result, include the method and baseline, task or benchmark, metric and
direction, value or difference, uncertainty or run count, evaluation setting, and
locator when those details determine interpretation. Use `reported by the paper`
when independent verification was not performed.

Use `state of the art`, `significant`, `generalizes`, `robust`, or `real-world`
only when the source evidence and scope justify the term. Do not turn a simulated or
offline evaluation into a deployment claim.

## Figures and quotations

- Use a paper figure only when rights and requested use permit it; otherwise create
  an original explanation or link to the source.
- Attribute quotations and keep them short. Mark paraphrases as paraphrases through
  normal prose rather than quotation formatting.
- Give any displayed paper figure its original locator and a new contextual caption;
  do not alter it in a way that changes the scientific meaning.

## Avoid

- DOI or venue errors introduced from memory.
- Citation counts, rankings, or recency claims without current verification.
- Comparing headline numbers from incompatible protocols.
- Borrowing a paper's related-work wording as if it were independent synthesis.
