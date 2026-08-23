# Install and activate Super Agent Presentation

The recommended deployment is **an installed Agent Skill plus one merged
micro-contract**. Giving an agent only a GitHub URL is a useful bootstrap, but a URL
is neither an installation nor an instruction-priority mechanism. Use
`AGENT_START.md` only when installation is impossible.

Installation is deliberately preview-first. The commands below never tell you to
overwrite an existing instruction file. Preserve higher-priority organization,
user, and repository rules and resolve conflicts before enabling the adapter.

## 1. Keep a complete local checkout

Clone the repository to a stable path that your agent can read. The examples below
use a task-specific variable for that absolute directory.

```bash
SAP_ROOT="/absolute/path/to/super_agent_presentation"
git clone https://github.com/asimfish/super_agent_presentation.git "$SAP_ROOT"
```

Inspect the canonical contract and Skill before installing them:

```bash
sed -n '1,180p' "$SAP_ROOT/AGENTS.md"
sed -n '1,240p' "$SAP_ROOT/skills/agentic-reporting/SKILL.md"
```

Keep the checkout as the reviewed release source. The installable Skill is
self-contained: its `scripts/`, `references/`, and `assets/` directories must travel
with `SKILL.md`. Do not copy only `SKILL.md`.

## 2. Preview a project installation

The standard-library installer has a read-only `plan` command. Point it at an
existing Git repository and select one or more hosts. Use `agents` for a generic
AGENTS-compatible host or `codex` for the Codex-specific adapter.

```bash
SAP_TARGET="/absolute/path/to/target-project"
python3 "$SAP_ROOT/scripts/install.py" plan \
  --target "$SAP_TARGET" --scope project --host codex
```

Repeat `--host` to preview a multi-host project:

```bash
python3 "$SAP_ROOT/scripts/install.py" plan \
  --target "$SAP_TARGET" --scope project \
  --host codex --host claude --host cursor --host copilot
```

Read the plan. The installer refuses to replace an existing Skill. For an existing
instruction file, the default apply preserves it and reports that a manual merge is
pending. Only the explicit `--append-adapter` option appends a marked block, and it
first creates a timestamped backup.

When the plan is correct, apply it without `--append-adapter` first:

```bash
python3 "$SAP_ROOT/scripts/install.py" apply \
  --target "$SAP_TARGET" --scope project --host codex
```

An exit status of 3 means the Skill was copied but at least one existing instruction
file still needs a manual adapter merge. It is not permission to overwrite that
file. Review the adapter as described below. Use `--append-adapter` only after you
have inspected the pending destination and want the installer to append the marked
block with a backup. On that second apply, the installer reuses the installed Skill
only when a bounded manifest and every file digest match the current source; a
different or locally edited Skill still fails closed.

### User-scope installation

The installer supports only file-backed user paths verified by this release:
`codex` and `claude`. Give the user's actual home/config base explicitly; the
installer does not guess it. Generic `agents`, Cursor, and Copilot user scope fail
closed because their global rule location is host-, UI-, or surface-dependent.

```bash
SAP_USER_ROOT="/absolute/path/to/user-home"
python3 "$SAP_ROOT/scripts/install.py" plan \
  --target "$SAP_USER_ROOT" --scope user --host codex
python3 "$SAP_ROOT/scripts/install.py" apply \
  --target "$SAP_USER_ROOT" --scope user --host codex
```

The same preview-first and existing-file rules apply. Use `--host claude` only after
confirming the current official path below. For Cursor user scope, install the Skill
manually and add the micro-contract through the documented User Rules UI.

### Manual installation

If you are not using the installer, place the **entire**
`skills/agentic-reporting/` directory at one supported discovery path listed below.
First inspect whether the destination exists. Copy or link only when the destination
is absent; otherwise compare versions and upgrade deliberately.

The framework CLI lives inside the self-contained Skill. To verify the source
checkout before installation, run:

```bash
python3 "$SAP_ROOT/skills/agentic-reporting/scripts/reportctl.py" list
```

## 3. Merge one host adapter

Open the existing destination, if any, and the matching adapter side by side:

```bash
SAP_EXISTING_INSTRUCTIONS="/absolute/path/to/existing/instruction-file"
SAP_ADAPTER="$SAP_ROOT/adapters/agents/AGENTS.snippet.md"
sed -n '1,200p' "$SAP_EXISTING_INSTRUCTIONS"
sed -n '1,200p' "$SAP_ADAPTER"
```

Merge the adapter as a short, clearly labeled section. Do not duplicate it at
multiple scopes unless you intentionally need both personal and repository policy.
The user's explicit request remains authoritative over presentation defaults.

### Generic AGENTS-compatible hosts

- Project Skill: `.agents/skills/agentic-reporting/`
- Project instruction: merge `adapters/agents/AGENTS.snippet.md` into the repository-root
  `AGENTS.md`.
- Global locations and precedence are host-specific; verify the host's documentation
  before installing globally.

### OpenAI Codex

- Project Skill: `.agents/skills/agentic-reporting/`
- User Skill: `~/.agents/skills/agentic-reporting/`
- Project instruction: repository-root `AGENTS.md`
- User instruction: `~/.codex/AGENTS.md`

For a project or user installation, pass `--host codex` with the corresponding
`--scope`. The default apply preserves an active Codex instruction file and returns
a pending-merge status instead of replacing it.

Codex uses `~/.codex/AGENTS.override.md` instead of `~/.codex/AGENTS.md` when the
override is non-empty. In user scope the installer detects that condition and routes
the adapter plan to the active override; the default apply preserves it and returns
status 3. Inspect it, then explicitly use `--append-adapter` or merge manually. An
empty override leaves `~/.codex/AGENTS.md` active. Codex also combines project
instructions from the repository root toward the working directory; nearer files
take precedence. At project scope the installer likewise targets a non-empty
repository-root `AGENTS.override.md` instead of creating an ignored `AGENTS.md`.
Merge `adapters/codex/AGENTS.md`, never replace the active file.

### Claude Code

- Project Skill: `.claude/skills/agentic-reporting/`
- User Skill: `~/.claude/skills/agentic-reporting/`
- Project instruction: `CLAUDE.md` or `.claude/CLAUDE.md`
- User instruction: `~/.claude/CLAUDE.md`

Link the full Skill directory into Claude's chosen skill path, then merge
`adapters/claude/CLAUDE.snippet.md` into the existing instruction file. Do not paste the
entire reporting manual into `CLAUDE.md`; Claude loads it as persistent context.
Use `/memory` to inspect which instruction files are active. Claude documents these
files as behavioral context, not hard enforcement.

The installer supports both `--scope project --host claude` and
`--scope user --host claude`; always run `plan` first.

### Cursor

- Project Skill: `.agents/skills/agentic-reporting/` or
  `.cursor/skills/agentic-reporting/`
- User Skill: `~/.agents/skills/agentic-reporting/` or
  `~/.cursor/skills/agentic-reporting/`
- Project rule: `.cursor/rules/agentic-reporting.mdc`

Preview any existing same-name rule, then merge or add
`adapters/cursor/agentic-reporting.mdc`. Its `alwaysApply: true` frontmatter keeps
only the micro-contract active; the detailed Skill remains on demand. For a global
preference, paste only the rule body into Cursor **Customize → Rules → User Rules**.
Cursor rules apply to Agent Chat, not every Cursor surface such as Tab or Inline
Edit.

The installer supports `--scope project --host cursor`. It deliberately rejects
Cursor user scope because Cursor documents User Rules through **Customize → Rules →
User Rules**, not a verified file path that this installer can activate. Install the
user Skill at a currently supported Skill discovery path, then paste only the rule
body into that UI and run the manual host smoke test in a fresh session.

### GitHub Copilot

- Project Skill: `.github/skills/agentic-reporting/` or
  `.agents/skills/agentic-reporting/`
- Personal CLI Skill: `~/.copilot/skills/agentic-reporting/` or
  `~/.agents/skills/agentic-reporting/`
- Repository instruction: `.github/copilot-instructions.md`

Merge `adapters/copilot/copilot-instructions.snippet.md` into the existing repository
instruction. Keep it short: GitHub says repository custom instructions accompany
each chat request. Support for AGENTS files, skills, and instruction types differs
across Copilot surfaces, so check the current support matrix for the surface you
use. Copilot instructions guide a nondeterministic model and are not guaranteed to
be followed identically every time.

The installer intentionally supports only `--scope project --host copilot`.

## 4. Run a manual host smoke test

For an `agents` project installation, first verify that the copied Skill is complete:

```bash
python3 "$SAP_TARGET/.agents/skills/agentic-reporting/scripts/reportctl.py" list
```

Start a fresh host session in a disposable or read-only test repository. A model's
answer that it "would activate" is not activation evidence. When the host exposes a
trace, inspect the actual Skill/tool invocation; otherwise record the controlled
session as a manual observation with host version and configuration. Ask:

```text
Without changing files, list the reporting instructions and Skills currently
available. Would a substantive experiment handoff activate agentic-reporting? Do
not write the report.
```

Then run a small end-to-end check with known facts. Confirm that the result:

1. honors an explicit user format override;
2. selects one primary mode and no more than two display modules;
3. separates evidence from interpretation and limitations;
4. does not invent tests, metrics, citations, or completion;
5. reports whether the structural audit actually ran.

Also exercise the long-task opening boundary in the disposable repository:

```text
This will be a long multi-agent implementation. The final handoff must show changed
files, verification evidence, remaining risks, and the next action. Before doing
the implementation, create the tiny reporting checkpoint and then stop.
```

Use the host trace, when available, to verify actual Skill/tool invocation rather
than accepting a claim that it happened. Inspect that the checkpoint contains only
the reporting objective, mode, audience, surface, and must-show items; then remove
the disposable checkpoint.

Run the repository's automated checks from the checkout as an additional release
check; they do not prove that every model or host will comply:

```bash
python3 -m pip install -r "$SAP_ROOT/requirements-dev.txt"
python3 -m unittest discover -s "$SAP_ROOT/tests" -v
python3 "$SAP_ROOT/scripts/presentation_benchmark.py" smoke
```

## Upgrade and uninstall

Upgrade the checkout with a reviewed Git change, inspect the diff, and rerun the
verification above. A symlinked Skill then uses the reviewed version. For a copied
Skill, compare and merge intentionally.

To uninstall, remove only the exact Skill link or directory you installed and delete
only the clearly labeled micro-contract section you merged. Do not delete an entire
shared `AGENTS.md`, `CLAUDE.md`, Cursor rule set, or Copilot instruction file.

## Primary host documentation

- OpenAI Codex `AGENTS.md`: <https://learn.chatgpt.com/docs/agent-configuration/agents-md>
- OpenAI Codex Skills: <https://learn.chatgpt.com/docs/build-skills>
- Claude Code memory and `CLAUDE.md`: <https://code.claude.com/docs/en/memory>
- Claude Code Skills: <https://code.claude.com/docs/en/skills>
- Cursor Rules: <https://cursor.com/docs/rules>
- Cursor Skills: <https://cursor.com/docs/skills>
- GitHub Copilot response customization:
  <https://docs.github.com/en/copilot/concepts/prompting/response-customization>
- GitHub Copilot support matrix:
  <https://docs.github.com/en/copilot/reference/custom-instructions-support>
- GitHub Copilot Skills:
  <https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills>
