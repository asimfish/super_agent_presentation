# Provenance and upstream boundary

- Review date: 2026-08-24
- Relationship: independent synthesis; no vendored or adapted third-party assets
- Detailed repository ledger: `docs/TEMPLATE-SOURCES.md` (outside the installed
  Skill); the portable source list below remains with the Skill

Agentic Reporting is an independent synthesis created for this repository. No
third-party Skill, template, prose block, chart asset, or code file was copied or
adapted into the package.

The design was informed at the level of public concepts by primary documentation:

- Agent Skills specification and progressive disclosure:
  <https://agentskills.io/specification>
- Agent Skills creation guidance:
  <https://agentskills.io/skill-creation/best-practices>
- OpenAI report and visualization workflows:
  <https://github.com/openai/role-specific-plugins/tree/main/plugins/data-analytics/skills>
- OpenAI Codex `AGENTS.md` and Skills:
  <https://learn.chatgpt.com/docs/agent-configuration/agents-md> and
  <https://learn.chatgpt.com/docs/build-skills>
- W3C image and table accessibility tutorials:
  <https://www.w3.org/WAI/tutorials/images/> and
  <https://www.w3.org/WAI/tutorials/tables/>
- GitHub Markdown and diagram documentation:
  <https://docs.github.com/en/get-started/writing-on-github>

The v0.4 research extensions were informed at the protocol level by these primary
or original sources:

- NeurIPS Paper Checklist, ICLR 2025 Author Guide, CVPR 2025 Suggested Practices,
  and DARPA's Heilmeier Catechism;
- `Deep Reinforcement Learning that Matters`, `Deep RL at the Edge of the
  Statistical Precipice`, RLiable, and `Empirical Design in Reinforcement Learning`;
- the Habitat Challenge, CALVIN, Open X-Embodiment, and OpenVLA repositories;
- DreamerV3, TD-MPC2 and its evaluation repository, and the original World Models
  project;
- Assertion-Evidence guidance, Quarto presentations, and Reveal.js.

The scientific-claim discipline added after v0.7.0 was informed at the protocol
level by these primary sources:

- `Interval Estimation for a Binomial Proportion` (Brown, Cai & DasGupta 2001),
  `How Generalizable Is My Behavior Cloning Policy?` (Vincent et al. 2024), and
  RoboArena (Atreya et al. 2025) for success-rate intervals, rollout counts, and
  matched pairwise real-robot comparisons;
- `Accounting for Variance in Machine Learning Benchmarks` (Bouthillier et al.
  2021) for named variance sources;
- `Leakage and the reproducibility crisis in machine-learning-based science`
  (Kapoor & Narayanan 2023), Sainz et al. 2023, and Jacovi et al. 2023 for leakage
  and contamination disclosure;
- `Troubling Trends in Machine Learning Scholarship` (Lipton & Steinhardt 2019) for
  explanation, attribution, and language discipline;
- Artstein & Poesio 2008 and `Judging LLM-as-a-Judge` (Zheng et al. 2023) for human
  and model-judge reporting.

Exact URLs, the design signal taken from each source, and non-transfer boundaries
are recorded in the repository ledger. The packaged profiles retain provenance IDs
so a maintainer can trace each rule without treating the source as a universal
template.

Anthropic's public PPTX Skill and the open-source Onepage Skill were studied only to
understand high-level routing, progressive loading, artifact separation, and QA
patterns. Their templates, prose, scripts, and visual assets were not copied,
adapted, bundled, or redistributed. Repository `docs/RESEARCH.md` records the broader
research trail and which statements are source facts versus design inferences.

There is no imported upstream package, pinned upstream commit, or compatibility
claim. Future imports must record exact source, revision, license, local changes,
and revalidation before release.
