---
name: agentic-reporting
description: Create and finalize task-appropriate, evidence-calibrated agent reports and handoffs. Use for substantive progress or final reports, implementation handoffs, investigations, experiment analysis, decisions, risks, incidents, postmortems, reviews, academic synthesis, and reports that must present figures, tables, or multiple artifacts. Also use near the start of likely long, multi-session, or multi-agent work to save a tiny reporting checkpoint, and at its final reporting boundary. Do not use for casual conversation, exact-format transformations, raw code-only output, or trivial direct answers.
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
   primary mode. Use `list` or `route` when uncertain.
2. For a long, multi-agent, or multi-session task, save a compact checkpoint near
   the start. For a short task, defer routing until the reporting boundary.
3. Complete and verify the actual task. Keep task execution independent of report
   styling.
4. Immediately before a substantive update or final answer, retrieve one bounded
   bundle. Add at most two display modules and only when the content needs them:

   Resolve `<skill-dir>` to the directory containing this `SKILL.md`; do not
   assume the caller's working directory is the skill directory.

   ```bash
   python3 <skill-dir>/scripts/reportctl.py bundle \
     --task "<what must be communicated>" --mode <mode> --surface <surface> \
     [--module <module>] [--module <module>] --max-chars 16000
   ```

   If resuming a long task, pass `--checkpoint <path>` instead of reconstructing
   the route from memory. Do not read every mode, module, or template.
5. Draft natively for the selected surface. Use one primary delivery artifact; do
   not create parallel Markdown, HTML, and PDF versions unless requested.
6. Audit a file-backed draft:

   ```bash
   python3 <skill-dir>/scripts/reportctl.py audit --file <draft.md> --mode <mode>
   ```

   Fix errors. Resolve warnings with judgment; never add unsupported filler merely
   to satisfy a heuristic.
7. Manually verify the latest state, scientific or technical claims, numbers,
   evidence links, uncertainty, visual interpretation, and user-specified format.

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
- Use `review-report` for findings against an artifact or standard.
- Use `incident-update` while impact is active; use `postmortem` after recovery.

Figures, tables, conclusions, evidence detail, and academic display are orthogonal
modules, not reasons to merge multiple modes. A visual must make a relationship or
artifact materially easier to understand; decoration is not a valid reason.

## Long-context persistence

Do not keep the full reporting bundle in working context. Save only a checkpoint:

```bash
python3 <skill-dir>/scripts/reportctl.py checkpoint \
  --task "<handoff objective>" --mode <mode> --surface <surface> \
  --output .agent-report.json
```

The checkpoint stores its reporting objective verbatim. Do not put secrets or
unnecessary private data in it; keep it outside version control and remove it when
the handoff no longer needs to be resumed.

At the final boundary, reload it with `bundle --checkpoint .agent-report.json` and
audit the draft. The host-recognized micro-contract is intended to prompt both the
near-start checkpoint and final reload; neither it nor the checkpoint can force an
arbitrary agent to comply.

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
python3 <skill-dir>/scripts/reportctl.py audit --file report.md --mode <mode> --strict
```

Do not require the structured path for a normal short chat response.

## Fallback when scripts are unavailable

Within an installed skill, read `references/core-contract.md`, one matching file
under `references/modes/`, and at most two matching files under
`references/modules/`. For link-only repository use, open `dist/agent-index.md` at
the repository root. If only a URL was supplied, treat adherence as best effort: a
link does not install or elevate repository instructions.
