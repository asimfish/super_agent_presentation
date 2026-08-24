# Context budget measurement

- Measured: 2026-08-24
- Revision: release tag `v0.3.0`
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
| Full `SKILL.md` | 9,936 | 1,360 | Only after Skill activation |

The persistent contract remains under the project's 150-word budget. The detailed
Skill is deferred; likely long work activates it briefly near the start to save a
checkpoint, releases it during execution, and reloads one bundle at the reporting
boundary.

## Routed bundles

Each measurement includes the route receipt, universal contract, exactly one primary
mode, and that mode's default zero-to-two modules.

| Mode | Default modules | Characters | Word-like units |
|---|---|---:|---:|
| `concise-answer` | — | 7,090 | 1,059 |
| `status-update` | — | 7,506 | 1,095 |
| `decision-brief` | conclusions | 11,249 | 1,584 |
| `incident-update` | evidence | 10,589 | 1,533 |
| `investigation-report` | evidence | 10,761 | 1,571 |
| `implementation-handoff` | evidence | 10,795 | 1,577 |
| `postmortem` | evidence | 10,972 | 1,578 |
| `review-report` | evidence | 11,152 | 1,619 |
| `risk-report` | tables, conclusions | 14,334 | 2,072 |
| `experiment-report` | tables | 11,597 | 1,685 |
| `academic-synthesis` | evidence, academic-display | 15,034 | 2,164 |

All measured task-based default bundles remain below the CLI's 16,000-character
guard. That guard is an independent caller-selected retrieval budget, not a promise
that every valid checkpoint and two-module combination fits: callers must raise
`--max-chars` explicitly when a selected combination needs more room. An agent does
not need to read `protocols.json`, every mode, every module, every template, or the
full distribution. The strict JSON schema is loaded only for a strict report-spec
task.

The experiment mode's default fell from the v0.2 two-module route to 11,597
characters because the mode already includes conclusion calibration; automatically
loading the generic conclusion module duplicated that policy. Explicit composition
remains available when a distinct decision or recommendation protocol is required.

## Interpretation boundary

These measurements establish bounded retrieval, not lower end-to-end token usage.
The framework may change output length or cause additional tool calls. A comparable
baseline/treatment generation run must measure actual input tokens, cached tokens,
output tokens, calls, latency, task fidelity, and useful information per 1,000
output tokens before making an efficiency claim.
