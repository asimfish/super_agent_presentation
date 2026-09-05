# Changelog

## Unreleased

- Added `docs/AUDIT-CODES.md`, the first complete reference for every finding
  `reportctl audit` can emit: all 42 codes grouped by severity and scope
  (delivery-blocking errors, checkpoint-bound errors, structure and scanning,
  displays, claims, research-mode claim discipline, research-mode number
  presentation), each with its exact trigger and how to clear it, plus the
  exemption rules, bounds, and the six manual checks no audit performs. Before
  this, 18 codes, including every error that blocks a delivery
  (`unresolved-placeholder`, `missing-image-file`, `malformed-table`,
  `missing-must-show`), were documented nowhere. A drift test pins the file to
  the source in both directions, severity included; linked from README and
  README_CN.
- Added seven deterministic number-presentation audit warnings in the research
  modes, turning the machine-checkable items of the absorbed statistical and
  benchmarking norms into enforceable findings: `unlabeled-uncertainty` (a `±`
  the report never labels as SD, SEM, or CI; Cumming et al. 2007),
  `threshold-p-value` (`p < 0.05`, `p > 0.05`, `n.s.`, with threshold
  declarations such as a pre-registered alpha exempt), `p-value-without-effect-size`
  (a p-value with no magnitude in the same sentence), `null-result-without-interval`
  (`not significant (p = 0.31)` with no interval or equivalence bound; Greenland et
  al. 2016), `significance-euphemism` (`approached significance`, `边缘显著`, and
  relatives), `up-to-without-central-tendency` (`up to N×` with no geometric mean,
  median, or worst case anywhere in the report), and `best-of-n-runs` (`best of 5
  runs`, `报告最好的一次`). EN and CN, inline code spans exempt, one finding per line
  and code, a null-result sentence yields only the more specific finding, and the
  checks stay silent on all 107 committed examples and fixtures. Registered in
  `docs/REPORTING-STANDARDS.md`; named in SKILL.md drafting step 5; three unit tests.
- Fixed a routing gap: a pure performance study (`throughput`, `speedup`, `tail
  latency`, `scalability`, `qps`, `吞吐`, `加速比`, `尾延迟`, `压测`) with no
  experiment wording fell through to `concise-answer` while still loading the
  `benchmarking` module. These measurement terms are now weak experiment-report
  mode signals; `latency` alone stays out so incidents and status updates keep
  their routes. All seven existing eval cases route unchanged. Three routing tests
  cover benchmarking, ablation, and the plain-latency negative.
- Fixed the evaluation harness's stale module whitelist (`ablation`,
  `benchmarking`, `natural-tone` were rejected as unknown) and the matching gap
  in `evals/schema/presentation-cases.schema.json`; a new drift test pins the
  harness mode/module/profile sets and the schema enums to `reportctl`'s.
- Added two harness-smoke eval cases with good and mutated fixtures, the first to
  exercise the new modules: `ablation-component-contribution`
  (`experiment-report+ablation+tables`: full-system reference row, per-component
  drops, tuning parity, untested-combination boundary, no additivity or
  significance claim) and `benchmark-speedup-honest`
  (`experiment-report+benchmarking+tables`: geometric mean and worst case beside
  the best case, `up to 3.1x` forbidden without a qualifier in the same line, p99
  regression, platform, warm-up and repetition protocol, retuned baseline). Smoke
  suite: 9 cases, 18 fixture evaluations.
- Absorbed the scientific-claim discipline that reviewers in RL, robotics, and VLA
  most often enforce and that a keyword audit showed the protocols never named:
  binomial success-rate intervals (Wilson / Clopper-Pearson; Brown, Cai &
  DasGupta 2001; Vincent et al., RA-L 2024), matched back-to-back real-robot
  comparisons with interleaved order (RoboArena, CoRL 2025), stratified bootstrap
  intervals and named variance sources for few-run RL aggregates (Agarwal et al.
  2021; Bouthillier et al., MLSys 2021), a leakage-and-contamination declaration
  (Kapoor & Narayanan, Patterns 2023; Sainz et al. 2023; Jacovi et al. 2023),
  explanation-versus-speculation, gain attribution, and anthropomorphic-language
  discipline (Lipton & Steinhardt 2019), and human/model-judge reporting with
  agreement statistics and position-bias controls (Artstein & Poesio 2008; Zheng
  et al., NeurIPS 2023). Encoded in the embodied-AI, VLA, and RL profiles, the
  experiment-report mode, and the conclusions, evidence, and benchmarking modules
  (the benchmarking module now carries the leakage and judge detail and routes on
  leakage/contamination/rater/judge signals; the mode and evidence files carry the
  one-line obligation so the default bundles keep their budgets); every source
  is registered in `docs/REPORTING-STANDARDS.md` and `docs/TEMPLATE-SOURCES.md`
  (new IDs RL-4, EMB-3, EMB-4, STAT-1, GEN-4 to GEN-7) with URLs verified against
  the publisher or CrossRef.
- Added three deterministic audit warnings that apply only in the research modes
  (`experiment-report`, `academic-synthesis`, `research-idea`):
  `success-rate-without-denominator` (a success rate printed as a bare
  percentage in a sentence, or in a table with no trial/`k/n`/interval column),
  `significance-without-statistic` (`significant` used as a comparative verdict
  with no test, p-value, interval, or effect size in the same sentence; EN and
  CN), and `anthropomorphic-claim` (a model, policy, or agent that `understands`,
  `thinks`, `wants`, `intends`, or `is aware`; EN and CN). Inline code spans are
  exempt, one finding is emitted per line, and the checks stay silent on every
  committed showcase report and outside the research modes. SKILL.md drafting
  step 5 names the pass; covered by four unit tests.
- Every budget-tested bundle stays within its guard after the additions: the
  default experiment bundle at 11,971 of 12,000 characters, the maximum-anchor
  academic bundle under 16,000, and every experiment + profile + tables route
  under 16,000 (largest: embodied-AI at 15,690); existing prose in the
  experiment mode and evidence module was tightened byte-for-byte to make room.
  Rebuilt `dist/` and refroze the study-plan skill manifest hash.

## 0.7.0 — 2026-09-02

- Bumped `reportctl --version`, `CITATION.cff`, and the skill card to 0.7.0
  (the skill card had lagged at 0.5.0), and refroze the study-plan skill
  manifest hash for the changed skill tree.
- Updated the Evidence status sections of both READMEs to report the two
  blind controlled studies (`evals/runs/controlled/`) instead of only the
  one-case pilot: the second run passes the preregistered primary quality gate
  (`+0.315`, 95% CI `[0.110, 0.579]`) while the efficiency gates still fail
  (`7.9x` median output-token overhead), so the claim status stays
  `insufficient_evidence` and no effectiveness claim is made.
- Everything below this line was merged to `main` between v0.6.0 and this
  release.
- Restructured both READMEs following the open-source conventions of the ARIS
  project (wanshuiyin/auto-claude-code-research-in-sleep): a numbered Contents
  section with stable anchors, a dated "What's New" changelog with PR links and
  a collapsible release history, an AI-agent entry pointer to `AGENT_START.md`,
  platform callouts, a Star History chart, and an Acknowledgements section
  crediting the absorbed standards, the licensed `shuorenhua` adaptation, and
  the ARIS README example itself. Fixed a stale display-module count (7 → 8) in
  the English catalog summary line. No protocol, routing, audit, or dist
  changes.
- Added a de-AI tone capability distilled from the MIT-licensed `shuorenhua`
  skill (MrGeDiao/shuorenhua) and registered the mapping in
  `docs/REPORTING-STANDARDS.md`. New on-demand `natural-tone` display module
  (module count 7 → 8): a fidelity contract that lets tone edits change wording
  but never facts (protected spans; relations, scope, negation, modality, and
  abstraction level preserved; two-direction reread), a structural-first
  processing order, a CN/EN signal-to-action table, and misfire protection for
  technical vocabulary (闭环/抓手/收敛/根因/对齐 in their domain senses, statistical
  显著, quoted material, academic passive voice). SKILL.md drafting step 5 now
  requires a de-AI pass before the final audit; the core contract stays
  unchanged so every bundle remains within its character budget. New
  `ai-tone-boilerplate` audit warning flags the highest-precision boilerplate
  only (CN sycophantic openers, performative closers, value inflation, hype
  comparatives; EN throat-clearing, `delve`, `game-changer`, `a testament to`),
  grouped one finding per line with all matched phrases listed, and inline code
  spans are exempt via same-length masking so quoted examples stay legal.
  Routing signals (去AI味/说人话/AI腔/humanize/natural tone) select the module;
  covered by positive/negative audit unit tests and a routing test.
- Added audit-clean finished examples with receipts for the two survey-absorbed
  templates in `examples/templates-20260828/`: `rebuttal-response` audited under
  `review-report` and `release-card` under `implementation-handoff`, both at
  zero errors and zero warnings. Linked them from the examples index and the
  catalog.
- Absorbed scientific reporting norms from a two-round literature survey and
  registered every mapping in `docs/REPORTING-STANDARDS.md`: statistical-claim
  discipline (ASA p-value statement, effect sizes with intervals, causal-language
  ladder, exploratory labeling, comparison families) in the conclusions module;
  uncertainty-visualization rules (within-the-bar bias, prediction versus
  confidence intervals, dual-axis ban) and scientific-figure rules (error-bar
  semantics, raw points for small n, colorblind-safe palettes, learning-curve
  discipline, caption order) in the visuals module; two new on-demand modules,
  `ablation` (form selection, interaction checks, variant tuning policy) and
  `benchmarking` (full-suite protocol, geometric/harmonic means, speedup and
  tail-latency discipline, platform disclosure); exclusion accounting in the
  experiment-report mode and search transparency in the academic-synthesis mode
  (CONSORT/PRISMA core); conclusions-slide ending and question-appendix guidance
  in the slide surface; and two new templates, `rebuttal-response`
  (point-by-point review response) and `release-card` (model-card/datasheet
  release summary). External-number marking and horizontal-rule typography were
  added to the tables module. All bundles remain within their character budgets;
  the module count is now 7 and the template count 12.
- Added the `cjk-halfwidth-punctuation` readability warning to `reportctl
  audit`: halfwidth `,.;:!?` sitting directly between two CJK characters is
  flagged once per line, because mixed-width punctuation is the single most
  visible typography defect in Chinese reports (Latin-adjacent halfwidth
  punctuation stays legal). Covered by a positive/negative unit test.
- Tightened the slide surface contract from showcase feedback ("quality and
  readability still mediocre"): quantitative results with three or more data
  points or a trend/tradeoff shape must be charted (inline SVG for the HTML
  template) with the full-precision table demoted to an appendix; the takeaway
  must be encoded inside the visual (shaded recommended region, highlighted
  chosen point, baseline reference line, labeled better-direction); scenario
  caveats are stated once on the title/closing slide instead of being repeated
  on every slide.
- Executed and published the second private controlled study
  (`evals/runs/controlled/codex-20260826/`): the exact 20260825 design re-run
  against the fixed contract (168 Codex executions, 84 blind pairs, two
  independent model raters, frozen before unblinding). The primary
  preregistered quality gate passes for the first time (`+0.315`, CI
  `[0.110, 0.579]`, threshold `+0.3`); win rate rose 33.3% → 45.2%; concision
  reached parity. Framework-side critical errors: 1 (single-rater flag);
  all 45 remaining critical errors were baseline pointer-style responses
  leaking local paths. Efficiency gates (token overhead `7.9x` median,
  semantic density) still fail structurally, so the claim status correctly
  remains `insufficient_evidence`.
- Corrected the `codex-20260825` study README: deblinding shows its 22
  pointer-style critical errors all sat on baseline sides, not framework
  responses as originally written. Flagged a telemetry gap for the next run:
  `final_audit_passed` records a contract-legitimate audit skip as not-passed
  (79/84 framework units now skip the final audit under proportional
  ceremony).
- Extended the `long-sentence` audit warning to CJK prose (sentences over 120
  CJK characters, split on 。！？), so Chinese run-on sentences are caught even
  though they contain no word-separating spaces. Added audit-clean finished
  examples with receipts for the two standards-based templates in
  `examples/templates-20260826/` and refreshed the catalog to the 10-template
  inventory (now 12 with the survey templates above).
- Absorbed a set of established reporting standards into the framework and
  registered the mapping in `docs/REPORTING-STANDARDS.md`: BLUF (AR 25-50),
  SBAR (IHI/AHRQ/WHO), the Minto pyramid principle, US federal plain-language
  guidelines (with ISO 24495-1), NN/g scanning research, WCAG 2.2 heading
  structure, Google SRE postmortem culture, and IBCS SUCCESS (aligned with
  ISO 24896:2026). Concretely: two new on-demand templates (`sbar-handoff`,
  `executive-onepager`), pyramid discipline in the decision-brief mode,
  assertion-title guidance in the visuals module, went-well/wrong/lucky and
  typed-action prompts in the postmortem template, and four new deterministic
  audit warnings (`generic-heading`, `heading-level-skip`, `long-sentence`,
  `deep-list-nesting`) that stay silent on all known-good fixtures and
  showcase reports. Bundles remain within their character budgets.
- Executed and published the first private controlled study
  (`evals/runs/controlled/codex-20260825/`): 28 held-out cases, 168 real Codex
  executions, 84 blind-rated pairs by two independent model raters, paired
  bootstrap against preregistered gates. Blind quality gains were real (6/7
  dimensions, composite `+0.214`, CI excluding 0) but the effectiveness claim was
  correctly rejected: `8.1x` median output-token overhead, pointer-style final
  responses leaking local paths, and collapsed semantic density.
- Fixed the two decisive failure surfaces in every host adapter, the repository
  micro-contract, `SKILL.md`, and the core contract: the final response must now
  contain the report itself (never a saved-file path, pointer, or scratch path),
  and ceremony is proportional — short single-session answers skip checkpoints,
  draft files, and script audits, reserving the file-backed bookend for long,
  multi-session, multi-agent, or durable-artifact work. Micro-contracts remain
  within the 150-word bound and bundles within their character budgets.
- Registered `evals/runs/controlled/` in the evals policy as a sanitized-aggregate
  destination alongside `runs/pilot/`.
- Upgraded the GitHub Pages demo to an evidence-first landing page: an
  interactive strict-audit repair trajectory quoted from
  `examples/showcase-20260825/first-failures.md` (1/12 → 12/12), an excerpt
  gallery covering all 16 committed showcase reports, a numbers wall where
  every figure links to its receipt, an honest mechanism-comparison table,
  and a materials section. The showcase deck PDF is now published on Pages.
- The Pages upgrade itself made no changes to protocols, routing, template
  content, tests, or dist output.

## 0.6.0 — 2026-08-25

- Added `reportctl --version`, with a regression test that binds the CLI
  version to the version declared in `CITATION.cff`.
- Added `scripts/check_test_env.py`, a stdlib-only preflight that warns when
  the working clone sits inside a cloud-sync scope (iCloud Drive, synced
  Desktop/Documents) and fails when file content has been evicted (dataless
  files or `.icloud` placeholders). Added after evicted iCloud content was
  observed making the subprocess-heavy study tests hang and fail
  non-deterministically; documented in CONTRIBUTING and both READMEs.
- Published a GitHub Pages demo (landing page plus the live showcase deck),
  assembled from committed artifacts only by `.github/workflows/pages.yml`;
  both READMEs gained a live-demo badge and collapsible page previews.
- Added citation metadata (`CITATION.cff` and README citation sections),
  issue templates, and a PR checklist mirroring the CONTRIBUTING gates.
- No changes to protocols, routing, template content, or dist output.

## 0.5.0 — 2026-08-25

- Fixed the `academic-talk-html` template clipping the leading glyph of long CJK
  headings when Chrome printed at 16:9 (print-only `padding-inline-start` on
  `h1`/`h2`), and locked the behavior with filled-deck real-render regression
  tests covering long CJK and mixed-script title fixtures.
- Added `examples/showcase-20260825/`: one finished, receipt-backed sample for
  each of the 12 core modes and 4 research profiles, plus a 7-page academic HTML
  deck with Chrome-printed PDF, per-page renders, strict-audit and semantic-oracle
  receipts, and an honest first-failure log. All facts are synthetic fixtures;
  rendering was verified on macOS Chrome 151 only.
- Split the README into an English `README.md` and a Chinese `README_CN.md`,
  both with visual previews of the rendered showcase deck.
- Added `docs/CATALOG.md`, a generated inventory of modes, modules, profiles,
  surfaces, and template assets cross-linked to bounded routes and finished
  examples, and `examples/README.md` documenting provenance and boundaries.
- Added `CONTRIBUTING.md` covering the test, dist-reproducibility, regression,
  and evidence-gate requirements for changes.
- No protocol, routing, or template-content changes beyond the print fix; bundles
  and dist output are unchanged from 0.4.0.

## 0.4.0 — 2026-08-24

- Added a source-backed `research-idea` mode that separates verified motivation
  from hypothesis, novelty delta, decisive evaluation, falsifiers, risks, and
  mid-point/final evidence gates.
- Added bounded reinforcement-learning, embodied-AI, world-model, and VLA research
  profiles. Profiles add domain protocol cards, comparable result displays,
  run/trial accounting, generalization axes, and failure boundaries without
  duplicating every primary mode.
- Added eight exact assets: detailed general and domain experiment reports, a paper
  idea brief, a dependency-free accessible HTML/PPT-style academic deck, and a
  Quarto Reveal.js source. Assets remain outside normal bundles and are retrieved
  one at a time with the new `reportctl template` registry.
- Added a slide-surface guide for paper talks, research progress, experiment
  reviews, and idea pitches using assertion-evidence structure and visible protocol
  metadata.
- Extended route/list/bundle/build-dist with deterministic profile selection,
  compatible template recommendations, bounded profile/surface files, and
  schema-v2 checkpoint compatibility through profile re-derivation from the frozen
  task.
- Added ADR-008 and a primary-source template ledger covering NeurIPS/ICLR/CVPR,
  DARPA, RL evaluation, Habitat, CALVIN, Open X-Embodiment, OpenVLA, DreamerV3,
  TD-MPC2, Quarto/Reveal.js, and open-source Agent presentation workflows. No
  third-party template asset was copied.

## 0.3.2 — 2026-08-24

- Added controller-verified checkpoint artifact receipts for qualifying framework
  host executions. The v1.1 control path snapshots checkpoint bytes at successful
  create, reload, and strict-audit event boundaries; snapshots the audited report;
  requires checkpoint stability and exact report/final-response equality; and
  independently re-runs the plan-pinned repository `reportctl` strict audit before
  deriving `checkpoint_receipt_verified`.
- Added a study-only delivered-prompt contract and controller-prepared `0700`
  workspace scratch so a real framework agent does not have to guess the receipt's
  relative paths or `0600` file requirement. Its digest is frozen in v1.1 receipts;
  it does not change the ordinary Skill contract.
- Enforced the named checkpoint/report paths, exact `0700` scratch-parent and `0600`
  file modes, and a non-writable workspace root. Final re-audit now consumes a fresh
  private pair written from the captured in-memory bytes and re-reads those bytes
  before issuing the receipt; the pinned auditor also returns the exact report
  byte-count/SHA-256 and parsed checkpoint intent fingerprint for comparison.
- Mirrored frozen local figures beneath the draft directory at their original
  workspace-relative paths and bound every local Markdown target to that allowlist.
  The same target is now covered end to end across agent audit, controller re-audit,
  stored evaluation, and blind packets; traversal, mutation, and symlink cases fail
  closed.
- Kept verification authority out of adapter telemetry and manual imports. Unsafe,
  ambiguous, baseline, or unverifiable candidates remain false; legacy v1.0 host
  plans and execution receipts stay validation-readable but cannot gain or backfill
  verified checkpoint evidence.
- Bound the receipt to private controller evidence and excluded checkpoint snapshots
  from blind packets, aggregates, and release artifacts. The receipt proves narrow
  event-boundary observations and a final controller audit, not continuous
  same-UID immutability, semantic recall, provider identity, or public
  effectiveness. Ordinary agent routing and reporting incur no new instructions,
  model calls, or token overhead.

## 0.3.1 — 2026-08-24

- Replaced full-tree `Path.rglob` materialization in installed-Skill receipts with
  iterative `os.scandir` traversal. The 4,096-entry resource cap now includes
  ignored top-level entries, `__pycache__` subtrees are pruned, and ignored names
  cannot bypass symlink or nonregular-file rejection; accepted manifests retain
  their canonical path ordering and digest.
- Updated the immutable GitHub Actions pins to official Node 24 releases:
  `actions/checkout` v7.0.1 and `actions/setup-python` v7.0.0, while preserving the
  Python 3.9/3.12/3.14 matrix.

## 0.3.0 — 2026-08-24

- Added a standard-library-only, preregistered study controller with immutable plan,
  case, prompt, artifact, generation, blind-assignment, rating-lock, and aggregate
  receipts plus versioned JSON Schemas.
- Added a typed, side-effect-free Codex argv/JSONL adapter, inert `host-plan`, and an
  explicit `host-run --execute` boundary with executable/workspace/framework
  digests, frozen complete argv/transcript format/adapter-source identity,
  plan-to-run exact comparison, `shell=False`, timeouts, bounded captures, and honest unsupported-control
  receipts. Controller-owned bindings prevent manual imports from impersonating
  adapter telemetry or an enforced provider cap; per-record locks detect later
  changes to records, responses, transcripts, or host bindings.
- Added portable generated-image ingest with traversal, symlink, type, size, and
  digest enforcement through validation and blinding.
- Added randomized A/B packets, owner-only assignment keys and rating templates,
  independent rating freeze bound to the full blind packet, case-level paired
  bootstrap, design prerequisites, and claim gates. Pilot summaries are
  schema-locked to `insufficient_evidence`.
- Bounded study JSON nesting, numeric tokens, and Cartesian products; aligned the
  runtime with the versioned schema/threshold profile; and made revision receipts,
  provider-enforced output caps, complete compaction/context observations, and the
  framework checkpoint lifecycle in compaction-required strata explicit claim
  prerequisites without forcing checkpoints onto short tasks.
- Separated the common strict final-audit observation from checkpoint-backed audit
  telemetry, so fresh short-task and 85%-occupancy rates use a comparable contract
  while checkpoint lifecycle gates remain scoped to compaction strata.
- Split caller generation input from controller-enriched stored records with two
  self-contained schemas; added shared boundary probes and controlled failures for
  unhashable JSON values instead of accepting traceback paths.
- Hardened Codex telemetry to credit only successful exact command events and kept
  an allowlisted argument grammar (rejecting help/unknown-option lookalikes), while
  keeping checkpoint artifact receipts explicitly unverified. Public profiles now require
  one controller-locked workspace per generation unit plus an external per-unit
  fresh-isolation receipt.
- Made visual gates fail closed on empty denominators, required both required and
  forbidden oracle coverage, added a 100% required-image/table-check gate, and
  preregistered semantic-slot density per 1,000 output tokens against baseline.
- Ran and published a redacted one-case, one-model, one-repeat Codex integration
  pilot. It observed treatment Skill activation but has no effectiveness standing;
  raw prompts, responses, transcripts, host receipts, and ratings remain private.
- Removed the redundant automatic `conclusions` module from `experiment-report`.
  The mode already carries calibrated conclusion rules, and a regression now keeps
  the default experiment bundle below 12,000 characters while preserving explicit
  composition for distinct decision needs.
- Documented real-host credential/network/cost boundaries, same-account baseline
  contamination, unpinned provider revisions, unenforced output-token caps, and the
  external isolation required for a public claim.

## 0.2.0 — 2026-08-24

- Added schema-v2 full-intent checkpoints and a same-checkpoint final audit that
  derives mode, rejects explicit conflicts, and gates bounded normalized literal
  anchors without replaying missing values. Schema v1 remains route/bundle-only.
- Replaced the audit and development benchmark's duplicated Markdown parsing with
  one shared bounded scanner while preserving consumer-specific policy.
- Documented the checkpoint fingerprint, literal-proxy, storage, output, and
  independent bundle-budget boundaries in the Skill, adapters, security review,
  architecture, benchmarks, and dedicated ADRs.
- Bounded pre-conversion JSON numbers, checkpoint diagnostics, and pre-NFC prose
  normalization to keep Python 3.9 behavior deterministic on adversarial inputs.

## 0.1.0 — 2026-08-24

- Introduced the persistent micro-contract, routed Agent Skill, and structural audit.
- Added eleven primary report modes and five on-demand display modules.
- Added the near-start checkpoint/final-reload lifecycle for long tasks and an
  optional structured report IR with deterministic Markdown rendering.
- Added Codex/AGENTS, Claude, Cursor, and GitHub Copilot adapters.
- Added an eight-case schema-validated activation contract, five positive route
  proxies, and a seven-scenario positive/negative fixture harness.
- Added fresh-agent development runs for experiment, long-context engineering, and
  evidence-bounded academic reports, retaining the failed iterations and reviews.
- Hardened installation with unresolved-target symlink checks, preflight, rollback,
  permission preservation, active Codex override routing, and digest-verified Skill
  reuse for pending adapter merges.
- Aligned the strict report validator, renderer, and structural audit, including
  catalog-derived semantic roles, escaped tables, encoded image paths, evidence
  fields, and non-finite JSON values.
- Added intent-priority and negation-aware routing regressions so review commands,
  explicit report purposes, and display exclusions outrank incidental vocabulary.
- Made distribution refresh transactional for ordinary filesystem failures by
  staging the complete generated set and restoring replaced or stale files on error.
- Replaced backtracking Markdown image regexes with bounded forward scanners,
  preindexed line lookup, image/finding amplification limits, and controlled failures
  for malformed URLs, deep JSON, and unresolved user paths.
- Made every human CLI/argparse/error surface terminal-safe, preserved JSON semantics
  with valid control escapes, and tightened both image scanners against nonportable
  Unicode whitespace, control-bearing targets, and cross-version symlink-loop drift.
- Normalized auditable images to blank-line-bounded, column-zero inline Markdown;
  required-image checks reject ambiguous containers, while forbidden-image checks
  conservatively include every unescaped Markdown image marker and every raw-HTML
  opening tag, including literal contexts, to close CSS/custom-element visual sinks
  without partial HTML interpretation.
- Aligned image destinations and alt text with CommonMark entity semantics: only
  valid semicolon-terminated references decode, rendered ampersands round-trip,
  ambiguous delimiters fail closed, and local targets must be regular files with a
  supported image suffix; pure fragment, query-only, and data-URI targets are
  outside the auditable subset.
- Corrected the CommonMark HTML-block owner state so isolated closing tags for
  `pre`, `script`, `style`, and `textarea` cannot swallow a later fence opener and
  falsely expose fenced image text.
- Limited Markdown block-state line endings to LF, CRLF, and CR, and blank lines to
  spaces/tabs, so Python-only control and Unicode separators cannot close a fence or
  HTML block that a CommonMark renderer keeps open.
- Preserved strict-renderer alternative text containing escaped backticks while
  continuing to reject renderer-dependent unescaped backtick forms.
- Made paragraph-sensitive CommonMark leaves conservative: setext-looking and link-
  definition-looking lines cannot incorrectly let a type-7 HTML block hide a later
  unclosed fence.
- Tracked list-container ownership for fenced code and kept ambiguous dedented
  content masked until a matching closer or EOF, so it cannot receive false image
  credit.
- Restricted required-image credit to canonical images occurring before raw
  triple-backtick/triple-tilde runs or paragraph-sensitive type-7 HTML markers;
  this conservative subset avoids parser drift and is documented as a false-negative
  trade-off rather than full CommonMark rendering.
- Applied the image-candidate cap only after merging and source-ordering parsed,
  Markdown-marker, and raw-HTML candidates, keeping audit and benchmark behavior
  identical when more than 1,000 candidates precede a later image.
- Rejected nonprinting structured locators before rendering and added full JSON
  key/string Unicode-scalar validation. Lone UTF-16 surrogates now produce controlled
  validation/render errors instead of encoder tracebacks.
