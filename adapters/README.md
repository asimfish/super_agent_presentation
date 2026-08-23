# Host adapters

These files contain the same host-neutral micro-contract in host-recognized forms.
They activate the canonical `agentic-reporting` Skill; they do not fork its report
rules.

| Host | Adapter in this directory | Merge destination |
|---|---|---|
| Generic AGENTS-compatible host | `agents/AGENTS.snippet.md` | repository `AGENTS.md` |
| OpenAI Codex | `codex/AGENTS.md` | repository `AGENTS.md` or active global Codex instruction file |
| Claude Code | `claude/CLAUDE.snippet.md` | repository or user `CLAUDE.md` |
| Cursor | `cursor/agentic-reporting.mdc` | `.cursor/rules/agentic-reporting.mdc` |
| GitHub Copilot | `copilot/copilot-instructions.snippet.md` | `.github/copilot-instructions.md` |

Never copy an adapter over an existing destination. Preview both files and merge
the small contract into the existing rule set. Keep local precedence and remove or
resolve contradictions. See `../INSTALL.md` for host-specific locations and checks.

These are behavioral instructions, not a security boundary. Model-based hosts can
miss or interpret instructions differently. Deterministic enforcement requires a
wrapper or lifecycle hook that blocks delivery on a failed audit; this repository's
portable adapters intentionally stop short of changing host execution policy.
