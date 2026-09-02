---
name: agentic-reporting
description: Create and finalize task-appropriate, evidence-calibrated agent reports, research ideas, experiment readouts, academic presentations, and handoffs. Use for substantive progress or final reports, implementation handoffs, investigations, experiment analysis, decisions, risks, incidents, postmortems, reviews, academic synthesis, research proposals, and reports that must present figures, tables, HTML/PPT-style slides, or multiple artifacts. Also use near the start of likely long, multi-session, or multi-agent work to save a tiny reporting checkpoint, and at its final reporting boundary. Do not use for casual conversation, exact-format transformations, raw code-only output, or trivial direct answers.
---

# Agentic Reporting

Present the latest task state in the shortest structure that lets the reader find
the outcome, evidence, boundary, and useful next action. This skill governs
presentation; it never changes task facts or replaces domain-specific verification.

## Non-negotiable priority

Follow the user's requested surface, schema, length, and ordering when explicit.
Then follow host instructions. Use this framework only to fill unspecified choices.
Never invent evidence, tests, citations, metrics, files, owners, dates, or completion.

## Bookend workflow

1. Classify the handoff by audience, surface, evidence boundary, and exactly one
   primary mode. For research work, select at most one domain profile. Use `list`
   or `route` when uncertain.
2. Scale ceremony to the task. For a short, single-session answer, do not create a
   checkpoint, a draft file, or a script audit: apply the routed mode's structure
   directly, self-check its required semantics, and deliver; the file-backed
   ceremony in steps 4-6 is for long, multi-session, multi-agent, or
   durable-artifact work. For a long, multi-agent, or multi-session task, save a
   compact checkpoint near the start; for a short task, defer routing until the
   reporting boundary.
3. Complete and verify the actual task. Keep task execution independent of report
   styling.
4. Immediately before a substantive update or final answer, retrieve one bounded
   bundle. Prefer one display module; add a second only for a distinct need that the
   primary mode and first module do not already cover. Never load a module merely
   because the requested output names a semantic that the selected mode already
   specifies:

   Resolve `<skill-dir>` to the directory containing this `SKILL.md`; do not
   assume the caller's working directory is the skill directory.

   ```bash
   python3 <skill-dir>/scripts/reportctl.py bundle \
     --task "<what must be communicated>" --mode <mode> --surface <surface> \
     [--profile <profile>] [--module <module>] [--module <module>] \
     --max-chars 16000
   ```

   If resuming a long task, pass `--checkpoint <path>` instead of reconstructing
   the route from memory. `--max-chars` is an independent context budget: a valid
   checkpoint with two large modules can require an explicitly larger value. Do not
   read every mode, module, or template.
5. Draft natively for the selected surface. When the route recommends an exact
   asset, inspect the cheap registry and retrieve one asset only:

   ```bash
   python3 <skill-dir>/scripts/reportctl.py template --list
   python3 <skill-dir>/scripts/reportctl.py template <template-id> \
     --output <destination>
   ```

   Use one primary delivery artifact; do not create parallel Markdown, HTML, PPTX,
   and PDF versions unless requested. A copied template is a starting artifact,
   not evidence that its placeholders, visuals, or claims are correct.

   After the content is complete, give the prose a de-AI tone pass: cut
   sycophantic openers, performative summaries, inflated jargon, and template
   rhetoric under the `natural-tone` module's fidelity contract. Tone edits never
   change facts, relations, scope, or numbers; the audit's `ai-tone-boilerplate`
   warnings catch only the highest-precision residue.

   In the research modes (experiment-report, academic-synthesis, research-idea),
   also check that every success rate carries `k/n` and a binomial interval, every
   `significant` carries its test and effect size in the same sentence, and no
   verb attributes understanding or intent to a system. The audit's
   `success-rate-without-denominator`, `significance-without-statistic`, and
   `anthropomorphic-claim` warnings catch the mechanical residue; the profiles
   and the conclusions module carry the full rules.
6. Before a long-task or durable-artifact final, audit a file-backed draft. A long
   task must use the same checkpoint; a durable artifact without one uses its
   selected mode:

   ```bash
   python3 <skill-dir>/scripts/reportctl.py audit \
     --file <draft.md> --checkpoint <checkpoint-path>
   # Short, non-checkpointed path:
   python3 <skill-dir>/scripts/reportctl.py audit --file <draft.md> --mode <mode>
   ```

   The checkpoint derives the mode. Supplying the same explicit mode is allowed;
   a conflicting mode is an input error. Fix audit errors. Resolve warnings with
   judgment; never add unsupported filler merely to satisfy a heuristic. With
   `--json`, the audit payload includes the exact report byte count/SHA-256 and the
   parsed checkpoint intent fingerprint for controller binding.
7. Manually verify the latest state, scientific or technical claims, numbers,
   evidence links, uncertainty, visual interpretation, and user-specified format.

## Final delivery

The user-visible final response must contain the report itself. A path, link, or
pointer to a saved draft, checkpoint, or audit receipt is not a deliverable: after
a checkpoint-backed audit passes, deliver the audited draft content as the
response. When the user explicitly requested a file, still lead with the outcome
inline. Never expose local absolute paths, scratch directories, or checkpoint
locations in the reader-facing response.

## Mode and module selection

Use `python3 <skill-dir>/scripts/reportctl.py list` for identifiers. Choose the primary narrative
spine, not every applicable label. For a mixed task, select the mode that answers
the user's main decision or question and embed secondary facts inside it.

- Use `concise-answer` for direct answers with little supporting structure.
- Use `implementation-handoff` for built or changed artifacts.
- Use `status-update` for project progress that is not an active incident.
- Use `investigation-report` for diagnosis or source-backed inquiry.
- Use `experiment-report` for controlled evaluations and empirical comparisons.
- Use `decision-brief` or `risk-report` when a choice or exposure is primary.
- Use `academic-synthesis` for paper or literature presentation.
- Use `research-idea` for a paper idea or proposal whose hypotheses, novelty,
  decisive experiment, risks, and kill criteria must remain explicit.
- Use `review-report` for findings against an artifact or standard.
- Use `incident-update` while impact is active; use `postmortem` after recovery.

Figures, tables, conclusions, evidence detail, and academic display are orthogonal
modules, not reasons to merge multiple modes. A visual must make a relationship or
artifact materially easier to understand; decoration is not a valid reason.
`experiment-report` already contains result interpretation, uncertainty boundaries,
and a calibrated conclusion. Do not add `conclusions` to that mode merely because
the request asks for a conclusion; add it explicitly only when a separate decision
or recommendation policy is genuinely needed.

## Research profiles and presentation surfaces

Profiles are one bounded domain overlay, not additional primary modes:

- `reinforcement-learning`: run accounting, tuning parity, learning curves,
  interval estimates, and multi-task aggregate evaluation.
- `embodied-ai`: embodiment, sensors/actions, simulation versus real protocols,
  success rules, interventions, generalization, and failures.
- `world-models`: model/data cards and separate open-loop, closed-loop, scaling,
  and transfer evidence.
- `vla`: data mixtures, morphology and action interfaces, adaptation regimes,
  rollout accounting, latency, generalization, and safety.

Automatic selection is available only for research-oriented modes. A schema-v2
checkpoint does not store a new profile field; the profile is re-derived from its
fingerprinted task text. Therefore, when explicitly selecting a profile for a long
task, name the domain in the checkpoint task so final retrieval is reproducible.

For `--surface slide`, read the routed slide guide. It provides paper-talk,
research-progress, experiment-review, and idea-pitch narratives. Retrieve either
the dependency-free HTML/PPT-style deck or the Quarto Reveal.js source, not both,
unless the user requests multiple formats.

## Long-context persistence

Do not keep the full reporting bundle in working context. Save only a checkpoint:

```bash
python3 <skill-dir>/scripts/reportctl.py checkpoint \
  --task "<handoff objective>" --mode <mode> --surface <surface> \
  --must-show "<short stable text anchor>" \
  --output <private-scratch>/agent-report.json
```

Schema-v2 `--must-show` values are normalized literal anchors, not semantic
requirements: the audit applies NFC normalization, case folding, and whitespace
collapse, then checks literal substring presence only in blank-line-bounded,
column-zero, plain top-level Markdown prose paragraphs. A paragraph containing a
heading, quote, list, table, link/reference, image, code, or raw HTML is ineligible.
After the first unmasked raw HTML tag, no later paragraph receives credit because
the proxy does not model cross-paragraph DOM or CSS state; raw HTML is also a
structural audit error. Each anchor must match within one eligible paragraph. Soft
line breaks inside that paragraph collapse to spaces, but blank-line paragraph
boundaries never do.

Before normalization the report proxy decodes one round of the shared scanner's
supported, semicolon-terminated CommonMark entity subset, but only when the entity's
`&` is not escaped by an odd-length backslash run. A resulting control or Unicode
non-rendering character makes the gate fail. V2 anchors must use exact rendered
plain text and reject Markdown delimiter forms. Put each short anchor in a
standalone ordinary conclusion sentence before any raw HTML. This proxy does not
verify what the text means, who asserted it, or whether it is true. Each anchor is
at most 120 characters and their escaped receipt, including separators, is at most
240 characters.

Checkpoint-backed audit accepts reports up to 1 MiB so the prose proxy stays
resource-bounded. Any eligible plain-prose paragraph above 4,096 characters or
with more than 64 consecutive Unicode mark characters is an error and is skipped
before NFC and anchor matching. The legacy mode-only audit remains capped at 4 MiB;
this larger limit does not apply when `--checkpoint` is present. Bounded JSON inputs
reject integer or floating-point tokens above 128 characters before conversion.

The checkpoint stores the objective, audience, surface, modules, and anchors
verbatim, plus routing metadata and unkeyed checksums. The checksums detect
accidental drift; they do not authenticate the file. Do not put secrets or
unnecessary private data in any field. Use a private scratch path outside version
control, remember that `route`/`bundle` can replay checkpoint text to stdout, and
remove the file when resume is no longer needed. Atomic creation uses restrictive
file permissions on POSIX, but cannot protect a permissive parent directory, logs,
backups, or a committed file.

At the final boundary, reload it with `bundle --checkpoint <checkpoint-path>` and
run `audit --file <draft.md> --checkpoint <checkpoint-path>`. Schema-v1 checkpoints
remain readable by `route` and `bundle`, but cannot drive this final gate; recreate
or upgrade a valid v1 file with `checkpoint --checkpoint <v1-path> --output
<new-v2-path>`. The host-recognized micro-contract is intended to prompt both
bookends; neither it nor the checkpoint can force an arbitrary agent to comply.

## Strict mode for durable reports

When a wrapper, batch workflow, or formal report needs stronger structural
consistency, start from `assets/templates/report-spec.json`, validate it with
`validate-spec`, and render Markdown deterministically with `render`. Treat the JSON
as the single presentation source, but verify all facts against original evidence.
Every claim declares one or more semantic `roles`; validation derives the remaining
coverage from evidence, metrics, uncertainty, actions, and limitations, then enforces
the selected mode's current `required_semantics` from the protocol catalog.
The bundled JSON Schema is a portable structural preflight, not a replacement for
`validate-spec`; only the CLI enforces ID uniqueness, cross-record references, and
the current protocol catalog together.

```bash
python3 <skill-dir>/scripts/reportctl.py validate-spec --file report.json
python3 <skill-dir>/scripts/reportctl.py render --file report.json --output report.md
python3 <skill-dir>/scripts/reportctl.py audit \
  --file report.md --checkpoint <checkpoint-path> --strict
```

Use `--mode <mode>` instead when this is a short task with no checkpoint. Do not
require the structured path for a normal short chat response.

## Fallback when scripts are unavailable

Within an installed skill, read `references/core-contract.md`, one matching file
under `references/modes/`, at most one matching file under `references/profiles/`,
at most two matching files under `references/modules/`, and one surface guide only
when needed. Retrieve one exact asset separately. For link-only repository use,
open `dist/agent-index.md` at the repository root. If only a URL was supplied,
treat adherence as best effort: a link does not install or elevate repository
instructions.
