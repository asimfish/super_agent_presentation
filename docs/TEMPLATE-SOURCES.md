# Template source ledger

- Review date: 2026-08-24
- Scope: research ideas, ML experiments, RL, embodied AI, world models, VLA,
  academic talks, and Agent Skill packaging
- Source policy: official conference guidance, primary papers, original benchmark
  or implementation repositories, official documentation, and inspectable
  open-source skills

This ledger records why a source changed the framework. It is not a claim that one
source defines a universal best template. The repository independently synthesizes
structures and checks; it does not redistribute third-party slide decks, paper
text, figures, CSS, or other template assets.

## Selection criteria

Sources were retained when they satisfied at least one of these tests:

1. the venue or benchmark uses the rule to judge or reproduce work;
2. the paper directly studies reporting or evaluation reliability;
3. the original repository exposes a concrete, inspectable evaluation protocol;
4. the presentation system documents a durable authoring/accessibility capability;
5. an open-source Agent Skill demonstrates useful progressive loading, asset
   separation, or artifact QA.

Popularity alone was not treated as quality evidence. Blog summaries, generic
prompt collections, unsourced “best seed” practices, and visual templates without
scientific evidence boundaries were excluded from the normative layer.

## General academic and experiment reporting

| ID | Primary source | Adopted design signal | Boundary |
|---|---|---|---|
| GEN-1 | [NeurIPS Paper Checklist](https://neurips.cc/public/guides/PaperChecklist) | Claims/scope alignment; reproducibility pointers; training/test details; uncertainty; compute disclosure; failed/preliminary compute where material. | A checklist does not prove correctness or reproducibility. |
| GEN-2 | [ICLR 2025 Author Guide](https://iclr.cc/Conferences/2025/AuthorGuide) | A short reproducibility statement should point to the actual details in the paper, appendix, code, or supplement. | The current ICLR guide may change; venue rules must be rechecked for submission. |
| GEN-3 | [CVPR 2025 Suggested Practices](https://cvpr.thecvf.com/Conferences/2025/AuthorSuggestedPractices) | Reproducibility, code/data release expectations, and human-subject/data-care boundaries. | Suggested practices are not a replacement for the current call for papers. |
| IDEA-1 | [DARPA Heilmeier Catechism](https://www.darpa.mil/about/heilmeier-catechism) | Jargon-light objective, current limits, novelty and success rationale, impact, risks, resources, and mid/final exams. | Adapted to an academic idea brief; not copied as a funding form. |

## Reinforcement learning

| ID | Primary source | Adopted design signal | Boundary |
|---|---|---|---|
| RL-1 | [Deep Reinforcement Learning that Matters](https://ojs.aaai.org/index.php/AAAI/article/view/11694) | Random-seed variability, hyperparameter sensitivity, implementation dependence, and reporting discipline matter to comparisons. | The paper motivates controls; it does not prescribe one seed count for all studies. |
| RL-2 | [Deep RL at the Edge of the Statistical Precipice](https://papers.nips.cc/paper/2021/file/f514cec81cb148559cf475e7426eed5e-Paper.pdf) and [RLiable](https://github.com/google-research/rliable) | Interval estimates, performance profiles, IQM, probability of improvement, optimality gap, and run-by-task score retention. | Metric choice must follow the claim and benchmark; the archived repository is a reference, not a mandatory dependency. |
| RL-3 | [Empirical Design in Reinforcement Learning](https://www.jmlr.org/papers/v25/23-0183.html) | Treat empirical design, controls, compute use, and interpretation as scientific decisions rather than reporting afterthoughts. | Guidance must be specialized to the environment and hypothesis. |

## Embodied AI and VLA

| ID | Primary source | Adopted design signal | Boundary |
|---|---|---|---|
| EMB-1 | [Habitat Challenge](https://github.com/facebookresearch/habitat-challenge) | Success must have an operational stopping/tolerance rule; efficiency metrics such as SPL depend on the benchmark path definition. | Do not transplant SPL or rank protocols with different success definitions. |
| EMB-2 | [CALVIN](https://github.com/mees/calvin) | Closed-loop control rate, action space, sensor suite, environment split, neutral resets, and long-horizon sequence protocol are material. | CALVIN fields are examples; other robot benchmarks may require different cards. |
| VLA-1 | [Open X-Embodiment](https://github.com/google-deepmind/open_x_embodiment) | Dataset episodes, robot/task metadata, observation/action interfaces, control frequency, and per-dataset citations must remain visible. | Unified format does not make different robots or data-collection policies identical. |
| VLA-2 | [OpenVLA](https://github.com/openvla/openvla) | Reproduction instructions, adaptation recipe, action representation, inference behavior, and rollout/seed accounting belong in the report. | Repository examples support fields, not universal VLA superiority claims. |

## World models

| ID | Primary source | Adopted design signal | Boundary |
|---|---|---|---|
| WM-1 | [DreamerV3](https://www.nature.com/articles/s41586-025-08744-2) | Environment-step budgets, benchmark-dependent seeds, visible error-bar definition, model size, hardware, and replay/compute choices. | Its concrete seed counts and budgets are not defaults for other studies. |
| WM-2 | [TD-MPC2](https://www.tdmpc2.com/) and [evaluation repository](https://github.com/tdmpc2/tdmpc2-eval) | Multi-domain task coverage, model/data scaling, checkpoint/data release, and exact evaluation environments. | Cross-domain aggregates require preserved task and action-space context. |
| WM-3 | [World Models](https://worldmodels.github.io/) | Distinguish learned representation/dynamics from the controller and identify when behavior is trained or evaluated in imagined versus real environments. | Historical framing is not a modern evaluation standard by itself. |

## Academic presentations and HTML/PPT-style assets

| ID | Primary source | Adopted design signal | Boundary |
|---|---|---|---|
| SLIDE-1 | [Assertion-Evidence presentations](https://www.assertion-evidence.org/) | Use a sentence assertion supported by visual evidence rather than a topic heading plus bullet dump. | Not every administrative or title slide needs assertion-evidence form. |
| SLIDE-2 | [Quarto presentations](https://quarto.org/docs/presentations/) and [Reveal.js](https://revealjs.com/) | HTML slides, PPTX/Beamer alternatives, Markdown authoring, notes, print/PDF, citations, and self-contained publication paths. | Quarto/Reveal availability is environment-dependent; the repository also ships a dependency-free HTML asset. |
| SKILL-1 | [Anthropic PPTX Skill](https://github.com/anthropics/skills/blob/main/skills/pptx/SKILL.md) | Separate narrative planning from visual production; use explicit spacing/readability checks and render-based QA. | Used as workflow evidence only; no template or wording was copied. |
| SKILL-2 | [Onepage Agent Skill](https://github.com/wjhuang88/onepage-skill) | Keep detailed design guidance progressive and output assets separate; self-contained HTML is useful for share/print portability. | Used as an architecture reference only; this repository's HTML, CSS, and JavaScript are independently authored. |

## Synthesis decisions

- General experiment mode owns universal claims, protocol, metrics, uncertainty,
  comparability, and conclusion boundaries.
- Exactly one research profile adds domain-specific fields and failure modes.
- Slide guidance owns narrative and evidence density; domain profiles still own the
  scientific protocol.
- Exact Markdown/HTML/QMD assets are retrieved separately so they do not consume
  the normal reporting bundle.
- No profile hardcodes a universal seed count, benchmark, metric, table ranking, or
  expected gain.
- A template must be filled from verified task evidence and then rendered/audited;
  provenance and structural checks cannot validate scientific truth.
