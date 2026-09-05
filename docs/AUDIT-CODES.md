# Audit codes

Every finding that `reportctl audit` can emit, what triggers it, and how to clear
it. The audit is mechanical: it checks structure, syntax, and a small set of
high-precision claim patterns. It never verifies that a number, citation, or
statement is true; that residue is listed at the end as `manual_checks_required`
in every receipt.

A drift test (`test_audit_codes_reference_tracks_every_finding_code`) keeps this
file and `skills/agentic-reporting/scripts/reportctl.py` in lockstep: a code that
exists in one and not the other fails the suite, and so does a code listed under
the wrong severity.

## Reading the tables

- **Severity.** An `error` fails the audit (`exit 1`) unconditionally. A `warning`
  fails it only under `--strict`, which the framework's final-audit step uses.
- **Scope.** Most checks run in every mode. The research-mode checks run only
  when `--mode` is `experiment-report`, `academic-synthesis`, or `research-idea`.
  The checkpoint-bound checks run only when `--checkpoint` is supplied.
- **Exemptions.** Fenced code blocks are excluded from every prose check. Inline
  code spans are excluded from the phrase-level claim checks, so quoting a
  forbidden phrase in backticks keeps it legal. `<details>` and `<summary>` tags
  are never placeholders.
- **Bounds.** Claim checks emit at most one finding per line per code. The whole
  audit stops at 500 findings (`audit-finding-limit`) and refuses reports above
  100,000 lines or 1,000 images.
- **Output.** Text mode prints `SEVERITY code:line — message`; `--json` returns
  `errors`, `warnings`, `findings[{code, severity, message, line?}]`, and
  `manual_checks_required`.

## Errors that block delivery (any mode)

| Code | Trigger | Clear it by |
|---|---|---|
| `empty-report` | The file is empty or whitespace only. | Writing the report before auditing it. |
| `report-line-limit` | More than 100,000 lines; the audit stops immediately. | Splitting the artifact or moving bulk data to an attachment. |
| `unresolved-placeholder` | `TODO`, `TBD`, or `XXX` as a word; any HTML comment; an upper-case angle tag such as `<OWNER>` or `<RESULT_1>`; a fill-in tag beginning with insert, replace, your, owner, date, path, value, result, status, or summary such as `<insert-date>`. | Filling or deleting every placeholder. Template instruction comments must be removed before delivery. |
| `malformed-table` | Rows of one Markdown table have different column counts. | Making every row, including the separator, the same width; escaping literal pipes as `\|`. |
| `invalid-table-separator` | A separator cell is not three or more hyphens with optional alignment colons (`---`, `:---`, `---:`, `:---:`). | Rewriting the separator row. |
| `noncanonical-image-syntax` | An image that is not a blank-line-bounded, column-zero inline `![alt](target)` paragraph: reference-style images, raw `<img>` tags, images inside lists, containers, or mixed prose, or an unescaped literal image marker in running text. | Giving every image its own paragraph; writing examples as `\![...]` or entity-encoding the opening `<`. |
| `missing-image-alt` | An informative image has no visible alternative text. | Writing alt text that states what the figure shows. |
| `invalid-image-alt` | Alt text contains a control or bidirectional-format character. | Removing the character. |
| `invalid-image-target` | The target contains whitespace, `\`, `(`, `)`, `<`, `>`, or a control or bidirectional-format character; an `http(s)` URL that fails the strict URL rules; or a local path with a scheme or authority, an unresolvable path, or a file that is not a regular image with a renderable suffix (`.avif .gif .jpeg .jpg .png .svg .webp`). | Pointing at a plain relative path to a real image file, or a well-formed `https` URL. |
| `missing-image-file` | A local image path, resolved relative to the report file, does not exist. | Fixing the path or adding the file; a render produced elsewhere must be copied next to the report. |
| `image-scan-limit` | More than 1,000 Markdown images; remaining images are not audited. | Reducing the image count or splitting the artifact. |
| `audit-finding-limit` | 500 findings reached; the rest of the report was not audited. | Fixing the reported findings and re-running. |

## Errors bound to a checkpoint (`--checkpoint`)

| Code | Trigger | Clear it by |
|---|---|---|
| `missing-must-show` | A checkpoint must-show item does not appear, after NFC, whitespace, and case normalization, inside a plain prose paragraph. Paragraphs containing tables, lists, headings, code, images, links, quotes, or HTML do not count as visible prose. | Stating the item in a plain sentence of the main narrative, not only in a table cell, heading, or list. |
| `unsafe-visible-prose` | The prose contains a control or non-rendering (Unicode category C) character. | Removing the character. |
| `checkpoint-prose-paragraph-limit` | A prose paragraph is longer than 4,096 characters, so it cannot be normalized for must-show matching. | Splitting the paragraph. |
| `excessive-combining-sequence` | More than 64 consecutive combining marks. | Removing the sequence. |

## Warnings: structure and scanning (any mode)

| Code | Trigger | Clear it by |
|---|---|---|
| `outcome-not-first` | The first two paragraphs (700 characters) carry no outcome or status vocabulary (`result`, `status`, `completed`, `blocked`, mode-specific openers such as `recommend` for decision briefs or `finding` for reviews, and their CJK equivalents). Not applied to `concise-answer`. | Leading with the result or current state, then the support. |
| `process-diary-opening` | The opening reads as a narrated process (`first I`, `then I`, `首先我`). | Deleting the narration; keep the result, evidence, and boundary. |
| `over-sectioned` | Fewer than 1,200 characters but more than five headings. | Dropping headings to two or three, or none. |
| `generic-heading` | A heading is a content-free label (`Introduction`, `Misc`, `Other`, `Notes`, `General`, `Information`, `简介`, `其他`, `备注`, `说明`). | Rewriting the heading to carry the section's message. |
| `heading-level-skip` | A heading level jumps by more than one (`##` to `####`). | Keeping levels consecutive. |
| `dense-paragraph` | A paragraph exceeds 1,200 characters. | Splitting it, only if that helps scanning. |
| `long-sentence` | A sentence exceeds 45 words or 120 CJK characters. | Splitting it unless precision requires the length. |
| `deep-list-nesting` | A list item sits three or more levels deep. | Flattening or restructuring the list. |
| `cjk-halfwidth-punctuation` | Halfwidth `,.;:!?` directly between two CJK characters. | Using fullwidth marks (`，。：；！？`) in CJK prose; code stays verbatim. |
| `ai-tone-boilerplate` | One of the highest-precision boilerplate phrases (`值得注意的是`, `综上所述`, `worth noting`, `delve`, `game-changer`, `in today's ...`). One finding per line. | Deleting the phrase or stating the concrete point; the `natural-tone` module carries the full pass. |

## Warnings: displays (any mode)

| Code | Trigger | Clear it by |
|---|---|---|
| `table-without-context` | None of the three lines before a table mentions `table`, `comparison`, `results`, `metrics`, or `actions` (`表`, `比较`, `结果`, `指标`, `行动`). | Introducing the table with a sentence that says what it compares. |
| `wide-table` | More than 10 columns. | Splitting the table or moving detail to an appendix. |
| `image-without-context` | Within 350 characters around an image there is no `figure`, `fig.`, `caption`, `takeaway` (`图`, `说明`, `观察`). | Adding a caption or the one-sentence takeaway next to the image. |
| `mermaid-accessibility` | A ```` ```mermaid ```` block lacks `accTitle` or `accDescr`. | Adding both accessibility fields. |

## Warnings: claims (any mode)

| Code | Trigger | Clear it by |
|---|---|---|
| `missing-semantic` | A semantic role the mode requires (`required_semantics` in `references/protocols.json`, term lists in `SEMANTIC_TERMS`) has no matching vocabulary anywhere in the report, for example `question`, `method`, `uncertainty`, or `boundary` for an experiment report. | Stating the role explicitly in a sentence; the audit looks for the role's vocabulary, not for a heading. |
| `strong-claim-boundary` | `state of the art`, `SOTA`, `proves`, `guarantees`, `statistically significant` (`最先进`, `显著优于`, `证明了`, `保证`) with no number, citation link, or bracketed reference within 250 characters. | Attaching the comparison, number, or citation, or weakening the verb. |

## Warnings: research-mode claim discipline

Only in `experiment-report`, `academic-synthesis`, and `research-idea`.

| Code | Trigger | Clear it by |
|---|---|---|
| `success-rate-without-denominator` | A success rate printed as a bare percentage in a sentence, or in a table whose header names no trial, `k/n`, or interval column. | Reporting `k/n` with the trial count and a Wilson or Clopper-Pearson interval (embodied-AI and VLA profiles). |
| `significance-without-statistic` | `significant` used as a comparative verdict (`significantly better`, `显著优于`) with no test, p-value, interval, or effect size in the same sentence. | Putting the test, exact p-value or interval, and effect size in that sentence, or using a plain magnitude word. |
| `anthropomorphic-claim` | A model, policy, agent, or system that `understands`, `thinks`, `wants`, `intends`, or `is aware` (`模型理解了`). | Describing the measured behavior against the defined task (Lipton & Steinhardt). |

## Warnings: research-mode number presentation

Same three modes.

| Code | Trigger | Clear it by |
|---|---|---|
| `unlabeled-uncertainty` | `±` (or `+/-`) appears but nothing in the report says what it denotes (SD, SEM, CI, IQR, tolerance, `标准差`, `置信区间`). One finding at the first use. | Labeling the interval once in the header, caption, or first use, with the run count (Cumming et al. 2007). |
| `threshold-p-value` | `p < 0.05`, `p < 0.01`, `p < 0.1`, `p > 0.05`, or `n.s.`; `p < 0.001` stays legal as the conventional floor. A sentence that declares a threshold (`alpha`, `threshold`, `pre-registered`, `阈值`, `预注册`) is exempt. | Reporting the exact value (`p = 0.031`); never reading `p > 0.05` as no effect (ASA 2016). |
| `p-value-without-effect-size` | A p-value in a sentence with no magnitude: no effect size, difference, points, ratio, interval, or from-to pair. Null-result sentences are handled by the next code instead. | Pairing the p-value with the effect size or absolute difference and its interval. |
| `null-result-without-interval` | `not significant`, `no significant difference`, `不显著` together with a statistic but no interval, equivalence bound, or power statement in the sentence. | Giving the interval or equivalence bound so readers see which effects were ruled out (Greenland et al. 2016). |
| `significance-euphemism` | `approached significance`, `trend toward significance`, `marginally significant`, `borderline significant`, `边缘显著`, `接近显著`, `趋于显著`. | Reporting the exact p-value and effect size and letting the reader grade it. |
| `up-to-without-central-tendency` | `up to N×`, `up to N times`, `最高可达 N 倍` while the report contains no geometric mean, median, mean, average, or worst case anywhere. | Adding the geometric mean or median and the worst case, and saying when the best case occurs (Heiser). |
| `best-of-n-runs` | `best of 5 runs`, `the best run is reported`, `报告最好的一次`. `Best-of-n sampling` as a method name is not matched. | Reporting the median or mean with dispersion over all runs, or stating why best-of-n is the deployment-relevant statistic. |

## What the audit cannot check

Every receipt lists the same six manual checks because no structural audit can
perform them: latest-state accuracy, claim and number fidelity, evidence and
citation validity, uncertainty and comparison boundaries, visual interpretability
in the final surface, and explicit user-format compliance. A clean audit means
the report is well-formed and free of the mechanical defects above; it does not
mean the report is correct.

## Adding a code

Add the check to `reportctl.py`, add a row to the matching table here, register
the source norm in [REPORTING-STANDARDS.md](REPORTING-STANDARDS.md) when the rule
comes from one, and add a positive and a negative unit test. Prefer a check that
fires on a narrow lexical pattern and stays silent on every committed example
(`examples/`, `evals/fixtures/`) over one that needs judgment; judgment guidance
belongs in a mode or module file.
