# Research: persistent, low-context reporting instructions

- Review date: 2026-08-24
- Scope: long-running agent tasks, repository/user instructions, progressive Skill
  loading, and final-report consistency across Codex, Claude Code, Cursor, and
  GitHub Copilot
- Source policy: official vendor documentation, open specifications, and original
  repositories only

This note separates documented behavior from design inference. It does not claim
that prompt instructions guarantee compliance.

## Documented findings

### Repository and user instructions

| Host or standard | Documented mechanism | Documented limit relevant here | Primary source |
|---|---|---|---|
| OpenAI Codex | Codex constructs an instruction chain before work: one active global instruction file, then one file per directory from project root to working directory; nearer project files override earlier guidance. | Discovery occurs once per run. The combined project instruction size defaults to 32 KiB. A non-empty global `AGENTS.override.md` is used instead of global `AGENTS.md`. | [OpenAI Docs: AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) |
| AGENTS.md open convention | A repository can place human-readable agent guidance in `AGENTS.md`; nested files provide more local instructions. | Host adoption and exact precedence remain implementation-dependent; an explicit user prompt can override repository guidance. | [agents.md](https://agents.md/), [original repository](https://github.com/agentsmd/agents.md) |
| Claude Code | Project/user `CLAUDE.md` files provide persistent context; `.claude/rules/` can modularize or path-scope rules. Detailed task procedures belong in Skills. | Claude states that these are context, not enforced configuration, and shorter, specific instructions are followed more consistently. Imports organize content but still load it. | [Claude Code memory](https://code.claude.com/docs/en/memory), [feature overview](https://code.claude.com/docs/en/features-overview) |
| Cursor | Project Rules support Always Apply, intelligent, path-specific, and manual activation. Cursor also recognizes root and nested `AGENTS.md`. | Always Apply rules consume recurring context. User Rules affect Agent Chat, not all features such as Tab or Inline Edit. | [Cursor Rules](https://cursor.com/docs/rules) |
| GitHub Copilot | Repository-wide custom instructions use `.github/copilot-instructions.md`; path instructions and some agent instruction files are also supported. | GitHub says instructions accompany every chat request, support varies by Copilot surface, and nondeterministic responses may not follow them identically each time. | [response customization](https://docs.github.com/en/copilot/concepts/prompting/response-customization), [support matrix](https://docs.github.com/en/copilot/reference/custom-instructions-support) |

### Progressive disclosure through Skills

| Mechanism | Documented behavior | Relevance | Primary source |
|---|---|---|---|
| Agent Skills specification | Hosts can expose only Skill metadata initially, load `SKILL.md` when activated, and read referenced files or execute scripts as needed. The specification recommends keeping the main instructions bounded and references shallow. | Detailed report modes, tables, figures, and academic conventions need not remain in every task's context. | [Agent Skills specification](https://agentskills.io/specification), [original repository](https://github.com/agentskills/agentskills) |
| OpenAI Codex Skills | Codex discovers project and user Skills and selects them from their names and descriptions; detailed resources can be loaded on demand. | A compact trigger description can activate one reporting workflow without an always-on manual. | [OpenAI Docs: Build Skills](https://learn.chatgpt.com/docs/build-skills), [OpenAI skill-creator source](https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md) |
| Claude Code Skills | A Skill body loads when invoked or relevant; longer references have little context cost until used. | `CLAUDE.md` can contain only the activation contract while the reporting protocol stays in a Skill. | [Claude Code Skills](https://code.claude.com/docs/en/skills) |
| Cursor Skills | Cursor discovers Skills in project/user `.agents/skills` and `.cursor/skills` locations and progressively loads resources. | The canonical Skill can remain host-neutral; an Always Apply Cursor rule only activates it. | [Cursor Skills](https://cursor.com/docs/skills) |
| GitHub Copilot Skills | GitHub recommends custom instructions for simple rules relevant to almost every task and Skills for detailed, situational workflows. | This directly supports splitting the micro-contract from the reporting library. | [GitHub Copilot Skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills) |

### Context and enforcement boundaries

1. OpenAI recommends lean prompts and reports directional internal evaluation gains
   from removing duplicated instructions and unnecessary examples. Those numbers are
   not evidence that this repository improves any task; this project must run its
   own evaluation. [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model#favor-leaner-prompts)
2. Claude Code distinguishes behavioral guidance (`CLAUDE.md`) from client-enforced
   settings and hooks. Its output styles apply to every response and add input-token
   cost, so they are broader than this framework needs.
   [Claude memory](https://code.claude.com/docs/en/memory),
   [output styles](https://code.claude.com/docs/en/output-styles)
3. GitHub explicitly warns that custom-instruction adherence is nondeterministic.
   Cursor documents feature-specific rule coverage. Therefore no cross-host prompt
   file can honestly be described as a hard guarantee.

### Markdown parsing boundary

CommonMark 0.31.2 defines seven HTML-block forms and requires valid named and
numeric character references to end in a semicolon; decimal references contain at
most seven digits and hexadecimal references at most six. The audit implements
that bounded grammar rather than a browser-style permissive entity decoder. The
project's column-zero, blank-line-bounded image form is an intentionally narrower
machine-verifiable subset, not a claim about every Markdown dialect.
[CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/)

The implementation retains a single active block owner, portable CR/LF line
boundaries, paragraph-sensitive type-7 HTML activation, and list-continuation
ownership for fences. To avoid claiming full parser equivalence, required-image
credit also stops after the first raw triple-backtick/triple-tilde run or
paragraph-sensitive type-7 tag marker. This is a deliberately bounded source audit,
not a general-purpose Markdown renderer; ambiguous display syntax fails closed.

## Architecture candidates evaluated

| Candidate | Persistence | Context cost | Scenario fit | Failure mode |
|---|---:|---:|---:|---|
| Full reporting manual in every host instruction | High | High | Low | Crowds task context and encourages the same bloated template everywhere. |
| Pure on-demand Skill | Medium-low | Low | High | The agent may not activate it, especially at the end of a long run. |
| Micro-contract + routed Skill + final audit | High where the host loads the contract | Low | High | Still depends on model activation and audit invocation unless a wrapper enforces the gate. |
| Structured report specification + deterministic renderer | High in controlled workflows | Medium | Medium | Adds ceremony and is unsuitable for ordinary chat or tiny answers. |

The selected default is the third candidate. The fourth remains an optional strict
path for batch systems and durable reports.

## Design inferences adopted by this project

The following statements are project decisions inferred from the sources above;
they are not vendor guarantees:

1. **Use a three-layer bookend.** Keep only an activation/finalization contract in
   persistent host context, retrieve detailed guidance at the handoff boundary, and
   run a deterministic structural audit immediately before delivery.
2. **Keep the always-on contract below roughly 150 words.** The exact threshold is
   a project budget, not a documented universal optimum. Its job is to preserve
   activation, user-priority, bounded retrieval, and honest audit status only.
3. **Route to one primary mode and at most two display modules.** This bounds token
   use and prevents implementation, experiment, academic, and review templates from
   being merged into one report.
4. **Externalize only a tiny checkpoint during long work.** Save the reporting
   objective, audience, surface, mode, modules, and short must-show anchors. Do not
   keep the full report bundle, duplicate the task log, or store secrets.
5. **Reload at lifecycle boundaries.** After compaction, resume, or a multi-agent
   handoff, use the checkpoint to retrieve a fresh bundle instead of trusting the
   model to remember an earlier template; at finalization, audit the draft against
   that same checkpoint.
6. **Let subagents return facts; let the root agent render.** Centralizing the final
   presentation avoids incompatible subagent formats while preserving their raw
   evidence and uncertainty.
7. **Treat link-only use as best effort.** A raw URL is data, not a host-recognized
   persistent instruction. It may be inaccessible, compacted away, or lower priority
   than existing rules. More persistent prompt exposure requires explicit
   import/installation plus the host adapter, but still does not guarantee model
   compliance.
8. **Do not confuse structural audit with truth verification.** A local tool can
   detect placeholders, missing blocks, malformed tables, or inaccessible local
   images. It cannot prove citations, scientific claims, metric comparability, or
   the appropriateness of an interpretation.
9. **Use a lexical checkpoint gate, not a semantic claim.** A schema-v2 checksum can
   detect accidental route drift, and normalized literal anchors can catch bounded
   omissions. Neither authenticates the file nor proves meaning, authorship, truth,
   audience fit, or module appropriateness.

## Recommended deployment

```text
host-recognized micro-contract (always present, very small)
        ↓ requests activation near long-task start or at a reporting boundary
canonical Agent Skill (one routed mode + 0–2 display modules)
        ↓ produces a candidate handoff
structural audit + manual factual/evidence check
        ↓
user-visible report
```

Install the canonical Skill once, then merge exactly one adapter at the desired
scope. Prefer repository scope for team-specific behavior and user scope for a
personal default across repositories. Do not replace an existing instruction file;
preview and merge it because host precedence and unrelated user rules matter.

For controlled automation that needs a stronger gate, wrap report generation so the
delivery step cannot execute until a structured report validates and the audit
passes. This is a separate orchestration feature, not something an `AGENTS.md`,
`CLAUDE.md`, Cursor rule, or Copilot instruction can enforce by itself.

## Claims intentionally not made

- The framework does not guarantee identical wording across models or hosts.
- It does not guarantee that an agent reads a raw repository link.
- It does not guarantee correctness, citation validity, scientific rigor, or visual
  quality merely because a structural audit passes.
- It does not claim token, latency, readability, or task-quality improvement until
  the repository benchmark records a comparable baseline and framework run.
- Vendor paths, precedence, and feature support can change; `INSTALL.md` links the
  current primary documentation and should be checked at release time.
