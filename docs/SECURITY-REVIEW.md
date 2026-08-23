# Security review — 2026-08-24

## Threat contract

- Assets: existing project/user instructions, installed Skills, generated reports,
  checkpoints, benchmark integrity, and any sensitive task text placed in them.
- Actor and privilege: a local user invokes the CLI with that user's filesystem
  permissions. There is no authentication or multi-tenant boundary.
- Entry points: CLI arguments, report Markdown, report/checkpoint JSON, output paths,
  install targets, existing instruction files, and packaged protocol data.
- Dependencies: Python standard library, the local filesystem, GitHub Actions for CI,
  and the eventual Markdown renderer. The tools make no network request.
- Required properties: never execute report content; fail closed on invalid schema,
  unsafe URI schemes, symlinked write paths, implicit replacement, or unsupported
  installation scope; never replay terminal-control or directional-format characters
  from untrusted text; bound parser memory; preserve existing instructions; do not
  claim that structural checks prove truth or safety.
- Credible abuse cases: path redirection through a repository symlink, overwriting an
  existing Skill/rule, oversized-file resource exhaustion, Markdown/HTML injection
  through a strict report spec, unsafe link schemes, a packaged source symlink, and
  accidental checkpoint disclosure.
- Out of scope: a malicious process with the same account racing filesystem checks,
  a compromised Python runtime or GitHub runner, renderer vulnerabilities, and a
  local user deliberately authorizing an exact `--force` overwrite.

## Source-to-sink review

| Source | Transformation | Sink / asset | Enforcement |
|---|---|---|---|
| Task text | route scoring, checkpoint serialization | checkpoint file | 20,000-character bound, fingerprint, explicit output, symlink-chain rejection, existing-file refusal |
| Markdown report | UTF-8 parse and structural checks | audit result | 4 MiB and 100,000-line bounds, bounded single-pass image scan, portable title whitespace, control-bearing target rejection, 1,000-image and 500-finding fail-closed limits; terminal-safe human output; no evaluation, shell, HTML rendering, or network fetch |
| JSON report spec | typed semantic validation and escaping | generated Markdown | 2 MiB, 100-level, and 100,000-value bounds; Unicode-scalar key/value validation; allowlisted status/kinds, evidence cross-references, printable HTTP(S)/local locator policy, Markdown/HTML and terminal-control escaping |
| Distribution output path | fixed generated filenames | local route pack | broad-root and symlink rejection, full-set staging, backup rollback, manifest-bounded stale deletion, explicit `--force` |
| Install target and host | static scope map and copied Skill | another project/user config | explicit target/scope, project `.git` check, active Codex override selection, unsupported scope denial, target/source/destination symlink rejection, preflight, digest-verified identical-Skill reuse only, best-effort rollback |
| Existing instruction file | marker check and optional append | host instruction integrity | 2 MiB UTF-8 bound, preserve by default, explicit append, timestamped backup, mode-preserving atomic replacement |
| Benchmark response | bounded UTF-8 parse and invariant checks | development score | 4 MiB and 100,000-line bounds; 1,000-image truncation signal; no model call or executable interpretation |

## Findings and remediation

### SR-01 — Symlinked destination parent could redirect writes

- Severity: medium before remediation; fixed.
- Source → sink: attacker-controlled project directory component → resolved output or
  install destination → file outside the intended project.
- Fix: both CLIs reject project/user-controlled symlink components in write
  destinations (while allowing privileged root-level platform aliases such as the
  macOS `/var` layout); the installer checks the unresolved target ancestor chain and
  also rejects symlinks inside the packaged Skill.
- Regression: installer and checkpoint tests construct destination and target-ancestor
  symlinks and verify that the external directory remains untouched.

### SR-06 — Installer validation could fail after copying the Skill

- Severity: medium before remediation; fixed.
- Source → sink: oversized instruction or non-directory parent → late adapter failure
  → partially installed Skill or raw filesystem traceback.
- Fix: apply preflights adapter text, instruction size/encoding, destination types,
  permissions, and adapter collisions before copying. Expected filesystem errors are
  mapped to `InstallError`; unexpected write failures trigger best-effort rollback.
  A status-3 retry can append safely only after the existing Skill's bounded
  file-digest manifest matches the source.
- Regression: apply-time oversized instruction, regular-file parent, adapter
  collision, and permission-preservation tests fail closed without a Skill residue.

### SR-02 — Unbounded report/JSON/instruction reads could exhaust memory

- Severity: low to medium for local automation; fixed.
- Source → sink: oversized untrusted file → `read_text` and regex/JSON parse → process
  memory and availability.
- Fix: report, JSON, benchmark response, and existing-instruction inputs have explicit
  byte limits and UTF-8 failure handling.
- Regression: the report audit rejects a file one byte above its 4 MiB limit.

### SR-03 — Strict renderer accepted active-looking Markdown and URI schemes

- Severity: medium in a permissive downstream renderer; fixed at this boundary.
- Source → sink: report-spec text/locator → Markdown link or prose → downstream
  renderer/user.
- Fix: the strict schema path allowlists local, HTTP, and HTTPS locators; rejects
  control/delimiter characters and network-path references; escapes Markdown and
  HTML-significant text; and validates evidence IDs before rendering.
- Regression: tests reject `javascript:` and verify escaped emphasis/HTML entities.

### SR-04 — Future packaged symlinks could escape the reviewed Skill tree

- Severity: medium in a compromised source checkout; fixed.
- Source → sink: symlink in `skills/agentic-reporting` → `copytree` → external file
  copied into an installation.
- Fix: installer preflight rejects any source symlink before the first copy.

### SR-05 — Checkpoint can retain sensitive task text

- Severity: contextual; mitigated and documented.
- Source → sink: reporting objective → durable JSON → version control or backup.
- Control: the Skill explicitly says the objective is stored verbatim, forbids
  secrets/unnecessary private data, recommends keeping it outside version control,
  and asks the agent to remove it when resume is no longer needed.

### SR-07 — Untrusted controls could alter terminal presentation

- Severity: medium before remediation; fixed.
- Source → sink: report fields, route arguments, Markdown image targets, validation
  keys, or filesystem paths → human CLI output → terminal state or misleading display.
- Fix: all human-output paths, including argparse and error diagnostics, pass through
  one visible control-character sanitizer. Generated Markdown escapes the same C0,
  C1, DEL, line-separator, and bidirectional-format set. JSON output uses valid
  `\\u` escapes so parsing preserves the original value without emitting raw control
  bytes.
- Regression: route human/JSON, strict rendering, audit, validation, path errors, and
  argparse failures are checked for raw terminal controls on Python 3.9 and 3.14.

### SR-08 — Unicode whitespace could certify a non-rendering image

- Severity: medium for benchmark and audit integrity before remediation; fixed.
- Source → sink: VT, FF, Unicode line separator, or paragraph separator in Markdown
  image syntax → permissive scanner boundary → false local-file/artifact success.
- Fix: both forward scanners recognize only portable space, horizontal tab, CR, and
  LF as title separators, retain other characters in the target, and reject raw or
  decoded control/directional-format characters before path resolution. A `stat`
  probe also preserves symlink-loop classification across `pathlib` version changes.
- Regression: delimiter and fragment variants for VT, FF, U+2028, and U+2029 fail in
  both the audit and benchmark on Python 3.9 and 3.14.

### SR-09 — Literal or container Markdown could receive image credit

- Severity: medium for audit and benchmark integrity before remediation; fixed.
- Source → sink: image-like text in code, comments, HTML blocks, indentation,
  lists, block quotes, nested labels, or renderer-dependent targets → permissive
  image-presence check → false presentation credit.
- Fix: scanners preserve offsets while masking fenced code and CommonMark HTML
  block types for required-image credit. Independent, blank-line-bounded,
  column-zero placement excludes inline code, comments, containers, and mixed prose.
  List-owned fences retain their continuation indentation; ambiguous dedented
  content remains masked until a matching closer or EOF instead of receiving image
  credit.
  Setext- and link-definition-looking lines preserve the paragraph context needed
  to prevent a type-7 block from swallowing a later fence.
  Audit and forbidden-image checks use a context-agnostic broad gate: every
  unescaped `![` and every raw HTML opening tag fails conservatively, even in
  literals. Rejecting every opening tag closes inline-CSS and custom-element image
  sinks without attempting partial HTML/CSS interpretation. Literal examples must
  escape the Markdown marker or entity-encode the opening `<`. This explicit
  false-positive trade-off avoids dependence on any one Markdown renderer's full
  inline grammar.
- Required-image credit additionally stops after the first raw contiguous
  triple-backtick/triple-tilde run or paragraph-sensitive type-7 tag marker. This
  conservative false-negative boundary was checked against 100,000 fixed-seed
  CommonMark differential cases with zero false credits; it is not a proof of parser
  equivalence. URI autolinks are excluded from the tag marker.
- Both scanners merge parsed and broad-gate candidates by source offset before the
  1,000-candidate cap. This prevents a later parsed image from displacing earlier raw
  markers in one implementation but not the other.
- Regression: canonical, reference-style, raw-HTML, container/lazy-continuation,
  and adversarial forms; HTML blank-line termination; type-1 opening versus
  type-6 closing-tag boundaries; non-CommonMark Unicode/control line separators;
  quoted `>` attributes; and both Python 3.9 and 3.14 are covered.

### SR-10 — Markdown entity and filesystem semantics could drift from the renderer

- Severity: medium for audit and benchmark integrity before remediation; fixed for
  the documented CommonMark subset.
- Source → sink: entity-encoded destination or alt text, directory, or arbitrary
  local file → source-level scanner → false image/accessibility credit.
- Fix: both scanners decode exactly one CommonMark-valid entity-reference round:
  named HTML5 references must end in `;`, decimal references contain 1–7 digits,
  and hexadecimal references contain 1–6 digits. Decoded whitespace and delimiter
  escapes are noncanonical; strict rendering preserves literal ampersands across
  one Markdown parse. Local targets must resolve to regular files with an allowlisted
  raster/vector suffix; pure fragments, query-only targets, and data URIs are not in
  the auditable subset. Decoded empty alt text and control/directional characters
  fail accessibility checks. Raw and decoded locator targets also reject nonprinting
  Unicode characters. HTTP(S) authorities are validated without fetching.
- Regression: semicolon and non-semicolon named/numeric references, renderer
  round-trips, entity-derived alt controls, angle targets, directory targets,
  unsupported suffixes, and malformed remote authorities are covered in the audit
  and benchmark implementations.

### SR-11 — Lone JSON surrogates could crash validation or rendering

- Severity: medium for local automation availability before remediation; fixed.
- Source → sink: a syntactically escaped lone UTF-16 surrogate in a report field or
  object key → URL quoting, sorting, JSON output, or terminal encoding → traceback
  and an uncontrolled command failure.
- Fix: the authoritative validator walks every JSON key and string scalar and
  rejects non-scalar surrogate code points before field access or rendering. Human
  and JSON output sanitizers escape an unexpected surrogate defensively, and the CLI
  maps residual Unicode I/O errors to a controlled status-2 diagnostic.
- Regression: locator values, ordinary text values, and unknown object keys exercise
  `validate-spec` and `render`; validation returns structured invalid-data output,
  rendering fails without a traceback, and the portable schema rejects the covered
  string fields.

## Supply-chain controls

The runtime installs no Python dependency. CI installs the version-pinned
`jsonschema` validation-only test dependency so shared Draft 2020-12/CLI boundary
tests cannot silently skip; it is not copied into the Skill. The portable schema is
a structural and conditional preflight, while `validate-spec` remains authoritative
for complete Unicode printability, identifier uniqueness, cross-record references,
and catalog-derived semantics that JSON Schema cannot fully express. CI actions are pinned to exact Git commit
identities rather than movable tags. The Skill has an independent provenance record
and includes no copied third-party assets. These controls reduce ambiguity; they do
not prove publisher identity or runtime safety.

## Residual risk

- File checks and writes are not a cross-process transaction. A malicious process
  with the same account could race a checked path; this local same-privilege threat is
  not eliminated.
- Rollback is best effort, not a crash-safe filesystem transaction; abrupt process or
  machine termination can still leave a partial installation or distribution
  transaction artifact. Ordinary staging, permission, replacement, and stale-delete
  failures are covered by byte-preservation/rollback tests. A pending manual merge
  intentionally returns status 3 after copying the Skill and is never described as
  full activation.
- `--force` can replace the exact report/distribution file selected by the invoking
  user. It does not broaden the target or bypass symlink checks.
- Generated Markdown must still be rendered by a maintained, sanitizing consumer.
  The normal free-form report path is not transformed by the strict renderer.
- Clean tests and static inspection are not proof of security. The release gate must
  retain the documented trust assumptions and rerun source-to-sink regression tests.
