# Changelog

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
