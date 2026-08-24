# Skill benchmark status

This package includes a declarative activation contract; repository-level tests add
deterministic CLI checks, a seven-scenario fixture harness, and a private study
controller. The contract encodes expected host boundaries and locally testable
post-activation routes. Neither it nor the fixture harness invokes a host or model,
so neither can establish activation accuracy or improved Agent output.

A repository-level one-pair Codex pilot did observe one treatment Skill read and no
baseline Skill read. It used one public case, one unpinned model alias, one repeat,
same-account workspaces, and no blind human ratings. Its aggregate is permanently
`insufficient_evidence`; it is an integration signal, not activation-rate,
effectiveness, readability, or efficiency evidence.

A public effectiveness claim requires pinned baseline and framework conditions,
held-out cases, long-context and compaction conditions, blind independent ratings,
task-fidelity non-inferiority, token accounting, critical-error review, and paired
statistics. The repository-root `BENCHMARK.md` defines the preregistration and
provisional gates.

Current defensible claims are limited to:

- the package exposes eleven primary modes and five display modules;
- the router bounds a bundle to one mode and at most two modules;
- automatic routing skips a module whose capability the selected mode explicitly
  embeds; the experiment mode therefore defaults to `tables` without duplicating
  generic conclusion guidance;
- the local CLI implements structural checks and deterministic Markdown rendering;
- checked-in activation cases encode explicit/natural positives, adjacent negatives,
  an explicit exclusion, five governance rubrics, and five positive-route proxies.

Do not convert those structural facts into a measured readability, correctness,
token-efficiency, or long-context-retention claim.
