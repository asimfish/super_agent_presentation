# ADR-008: Composable research template packs

## Status

Accepted

## Context

The reporting core routes one narrative mode and at most two display modules. It
does not yet provide enough reusable structure for research ideas, domain-specific
experiments, or HTML/PPT-style academic talks. Adding one monolithic template for
every combination of report type, research domain, and output format would make
the library expensive to retrieve and difficult to keep consistent.

The extension must cover general experiments, reinforcement learning, embodied
AI, world models, and vision-language-action research. It must also expose exact
copyable assets without loading those assets into every reporting bundle.

## Driving Factors

- A normal route must still load exactly one narrative spine and no more than two
  display modules.
- Domain guidance must be specific enough to change experimental reporting
  decisions, not merely rename generic headings.
- A long-task schema-v2 checkpoint must remain readable and controller-verifiable.
- Link-only users need a small index and bounded files rather than the whole Skill.
- Source-derived rules require provenance, but third-party templates must not be
  copied into the repository without a compatible redistribution decision.
- HTML slide assets must work without network dependencies; richer authoring
  workflows may be offered separately.

## Candidates

### Option A: Full template matrix

Create a complete template for every combination such as RL experiment Markdown,
RL experiment HTML, embodied experiment Markdown, and embodied experiment HTML.

- Pros: each file is immediately concrete; little composition is required.
- Cons: combinations grow multiplicatively; shared rules drift; routing and token
  costs increase; small corrections require many synchronized edits.

### Option B: Mode + research profile + surface guide + exact asset

Keep one primary narrative mode, optionally add one domain research profile, load
one surface guide only when the surface needs it, and retrieve exactly one copyable
asset through a separate template registry.

- Pros: bounded context; shared rules have one owner; domain protocols remain
  independently maintainable; one asset can serve multiple compatible routes.
- Cons: the agent must compose a few small pieces; routing and compatibility need
  deterministic tests.

### Option C: Search external template repositories at runtime

Store only links and have the agent select a live external template for each task.

- Pros: minimal repository size; access to newly published material.
- Cons: unstable availability and licensing; unbounded retrieval; prompt-injection
  and supply-chain exposure; no reproducible output contract.

## Decision

Chosen: Option B.

The canonical composition is:

```text
one primary mode
  + zero or one research profile
  + zero to two display modules
  + zero or one surface guide
  -> recommend exact assets
  -> retrieve exactly one asset only when needed
```

Research profiles are deterministic derivatives of the bounded task text. This
keeps existing schema-v2 checkpoints unchanged: reloading a checkpoint re-runs the
same profile selection over the fingerprinted task. A caller may explicitly select
a profile for a short route. Checkpoint creation rejects an explicit selection
that the frozen task cannot reproduce.

This preserves checkpoint and controller compatibility, not cross-version profile
identity. If profile signals change in a later Skill release, the same schema-v2
task may select a different overlay. Study plans pin the Skill manifest; ordinary
long tasks that need the exact overlay should resume with the same reviewed release.

The template registry stores identifiers, intended modes/profiles/surfaces, and a
path below the Skill directory. `route` may recommend identifiers, but `bundle`
does not inline asset contents. `template` lists or retrieves one exact asset.
Domain profiles and surface guides are included in the generated link-only
distribution as separate bounded files.

The first research profiles are reinforcement learning, embodied AI, world models,
and VLA. The first new primary mode is research idea. The slide surface receives an
academic-talk guide and both a dependency-free HTML deck asset and a Quarto
Reveal.js authoring asset.

## Interfaces

- `reportctl list`: lists modes, profiles, display modules, surfaces, and assets.
- `reportctl route`: returns the selected profile and compatible asset IDs.
- `reportctl bundle`: loads core + mode + optional profile + modules + optional
  surface guide, subject to the explicit character budget.
- `reportctl template --list`: provides cheap asset discovery.
- `reportctl template <id>`: prints or copies exactly one registered asset.
- `reportctl build-dist`: emits routes, profiles, modules, and surface guides with
  a manifest-controlled transactional update.

## Impact

- The protocol catalog gains `profiles`, `surface_guides`, and `templates`.
- Profile inference becomes part of route behavior but not checkpoint intent.
- Existing schema-v1 and schema-v2 checkpoints remain valid.
- Adding a domain no longer requires duplicating every mode and surface.
- Source provenance is maintained separately from agent-facing bounded guidance.
- Template quality still requires factual review and artifact rendering; structural
  routing alone does not prove scientific or visual quality.
