# Context budget measurement

- Measured: 2026-08-24
- Revision: release tag `v0.2.0`
- Method: Python `len(text)` and `len(text.split())` over the exact files and output
  of `reportctl bundle --task "Context-budget measurement." --mode <mode>
  --max-chars 16000`. These are tokenizer-independent measurements, not model token
  counts; actual tokens depend on the host and language.

Run from the repository root to reproduce every row:

```bash
python3 - <<'PY'
from pathlib import Path
import json
import subprocess

root = Path(".")
artifacts = (
    root / "AGENTS.md",
    root / "adapters/agents/AGENTS.snippet.md",
    root / "skills/agentic-reporting/SKILL.md",
)
for path in artifacts:
    text = path.read_text(encoding="utf-8")
    print(path, len(text), len(text.split()))
skill = artifacts[-1].read_text(encoding="utf-8")
description = next(line.removeprefix("description: ") for line in skill.splitlines()
                   if line.startswith("description: "))
print("activation description", len(description), len(description.split()))
catalog = json.loads((root / "skills/agentic-reporting/references/protocols.json")
                     .read_text(encoding="utf-8"))
for mode in catalog["modes"]:
    result = subprocess.run(
        ["python3", "skills/agentic-reporting/scripts/reportctl.py", "bundle",
         "--task", "Context-budget measurement.", "--mode", mode,
         "--max-chars", "16000"],
        check=True, capture_output=True, text=True,
    ).stdout
    print(mode, len(result), len(result.split()))
PY
```

## Persistent and activation layers

| Artifact | Characters | Word-like units | Loaded when |
|---|---:|---:|---|
| Root `AGENTS.md` micro-contract | 1,057 | 149 | Host instruction discovery |
| Generic AGENTS adapter body | 944 | 127 | Every applicable host request after installation |
| Skill activation description | 599 | 77 | Skill discovery metadata |
| Full `SKILL.md` | 9,187 | 1,252 | Only after Skill activation |

The persistent contract remains under the project's 150-word budget. The detailed
Skill is deferred; likely long work activates it briefly near the start to save a
checkpoint, releases it during execution, and reloads one bundle at the reporting
boundary.

## Routed bundles

Each measurement includes the route receipt, universal contract, exactly one primary
mode, and that mode's default zero-to-two modules.

| Mode | Default modules | Characters | Word-like units |
|---|---|---:|---:|
| `concise-answer` | — | 7,334 | 1,095 |
| `status-update` | — | 7,750 | 1,131 |
| `decision-brief` | conclusions | 11,107 | 1,567 |
| `incident-update` | evidence | 10,833 | 1,569 |
| `investigation-report` | evidence | 11,005 | 1,607 |
| `implementation-handoff` | evidence | 11,039 | 1,613 |
| `postmortem` | evidence | 11,216 | 1,614 |
| `review-report` | evidence | 11,396 | 1,655 |
| `risk-report` | tables, conclusions | 14,192 | 2,055 |
| `experiment-report` | tables, conclusions | 14,866 | 2,129 |
| `academic-synthesis` | evidence, academic-display | 15,278 | 2,200 |

All measured task-based default bundles remain below the CLI's 16,000-character
guard. That guard is an independent caller-selected retrieval budget, not a promise
that every valid checkpoint and two-module combination fits: callers must raise
`--max-chars` explicitly when a selected combination needs more room. An agent does
not need to read `protocols.json`, every mode, every module, every template, or the
full distribution. The strict JSON schema is loaded only for a strict report-spec
task.

## Interpretation boundary

These measurements establish bounded retrieval, not lower end-to-end token usage.
The framework may change output length or cause additional tool calls. A comparable
baseline/treatment generation run must measure actual input tokens, cached tokens,
output tokens, calls, latency, task fidelity, and useful information per 1,000
output tokens before making an efficiency claim.
