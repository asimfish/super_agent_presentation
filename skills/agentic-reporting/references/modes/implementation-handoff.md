# Implementation handoff

Use this mode after changing code, configuration, data, documentation, or another
project artifact. Report the real terminal state: complete, partial, or blocked.

## Semantic order

1. **Outcome:** state what now works or what prevented completion.
2. **Scope:** summarize user-visible behavior and the material artifacts changed.
3. **Verification:** list the checks run and their observed results.
4. **Boundary:** expose failed, skipped, unavailable, or out-of-scope checks and
   remaining risks.
5. **Handoff:** link the relevant files, commit, pull request, or generated artifact;
   name the next action only when work remains.

Rename or merge sections when the report remains easy to scan. For a tiny successful
edit, a short outcome sentence plus one verification bullet may be enough.

## Verification rules

- Identify the check, relevant scope, and result. Include a command only when it
  improves reproducibility or diagnosis.
- Distinguish unit, integration, static, security, build, and user-journey checks.
- Report the latest material failure even when earlier checks passed.
- Do not write `all tests passed` when only a subset ran. Do not infer runtime
  behavior from compilation or static inspection alone.
- If no check was run, state why and what remains unverified.

## Artifact rules

- Link to the smallest useful set of files or durable artifacts.
- Describe behavior rather than dumping a file list with no meaning.
- Keep raw diffs, complete logs, and generated output outside the main narrative.
- Preserve unrelated user changes; do not imply ownership of work not performed in
  this run.

## Completion language

Use `complete` only when the requested change exists and the material acceptance
path passed. Use `partial` when a useful change exists but required work remains.
Use `blocked` when a dependency, authority, credential, environment, or user choice
prevents progress, and state the smallest unblock action.

## Avoid

- A chronological diary of commands.
- Claims such as `ready to ship` without release-relevant evidence.
- Hiding a late integration failure below a success headline.
- Suggesting unrelated cleanup as if it were required to complete the task.
