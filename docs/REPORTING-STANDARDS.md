# Absorbed reporting standards

This registry names the external reporting standards and research findings the
framework draws on, the core rule taken from each, and where that rule is encoded
so the mapping stays auditable. Encoding locations are the canonical statement;
this file is documentation, not an additional contract layer. Domain-template
provenance (ML, RL, embodied, VLA, academic talks) lives separately in
[TEMPLATE-SOURCES.md](TEMPLATE-SOURCES.md).

| Standard / source | Core rule absorbed | Encoded in |
|---|---|---|
| BLUF (US Army AR 25-50 correspondence standard) | The first sentence carries the conclusion or requested action; background follows. | `references/modes/concise-answer.md` required shape; `outcome-not-first` and `process-diary-opening` audit warnings; core-contract reader contract rule 1 |
| Inverted pyramid (journalism; NN/g "Inverted Pyramid: Writing for Comprehension") | Order content most-important-first at page, section, paragraph, and sentence level; front-load headings and first words. | Semantic order sections of every mode file; `outcome-not-first` audit warning |
| Minto Pyramid Principle / SCQA (Barbara Minto) | One governing thought stated as a complete claim, supported by two to four non-overlapping reasons; a reader of only the top layer holds the full picture. | `references/modes/decision-brief.md` decision discipline; `assets/templates/executive-onepager.md` |
| SBAR (IHI/AHRQ/WHO handoff standard) | Situation, background, assessment (explicit judgment, separate from data), recommendation with time bound and contingency. | `references/modes/incident-update.md` semantic order; `assets/templates/sbar-handoff.md` |
| Google SRE postmortem culture (SRE Book ch. 15) | Blameless systemic analysis; quantified impact; timeline; what went well / wrong / where we got lucky; owned, tracked, typed action items. | `references/modes/postmortem.md`; `assets/templates/postmortem.md` |
| US federal plain language guidelines (plainlanguage.gov, OPM; ISO 24495-1) | 15-20 word average sentences; one idea per paragraph; short paragraphs; common words; descriptive unique headings; lists with lead-ins, kept shallow. | `long-sentence`, `dense-paragraph`, `deep-list-nesting`, `generic-heading` audit warnings; core-contract reader contract |
| NN/g scanning research (layer-cake pattern; "How Users Read on the Web") | Readers scan headings first; meaningful (not clever or generic) subheadings, one idea per paragraph, and roughly half the conventional word count raise measured usability. | `generic-heading`, `over-sectioned` audit warnings; core-contract surface and proportionality |
| WCAG 2.2 heading and structure guidance | Descriptive headings; consecutive heading levels; meaningful link text; alternative text for informative images. | `heading-level-skip`, `missing-image-alt`, `image-without-context` audit findings; accessibility section of core-contract |
| IBCS SUCCESS formula (IBCS Standards 2.0, aligned with ISO 24896:2026) | One message per chart; assertion titles that state the finding rather than the topic; visual integrity (honest scales); condensed, consistent notation. | `references/modules/visuals.md` charts section; `wide-table` and `table-without-context` audit warnings |
| Assertion-evidence slide design (Alley) | Each slide is one full-sentence assertion supported by visual evidence, not a topic plus bullets. | `references/surfaces/slide.md`; `assets/presentations/academic-talk.html` |
| IMRaD and structured-abstract norms | Question, method, results with uncertainty, and interpretation are distinct roles; claims stay within evidence scope. | `references/modes/experiment-report.md`; `references/modes/academic-synthesis.md`; experiment templates |
| ADR (architecture decision records) | A decision record states status, context, options, decision, and consequences, and is superseded rather than rewritten. | `references/modes/decision-brief.md` decision discipline |

## Update discipline

When absorbing a new standard, encode the smallest testable rule in the narrowest
location first: a deterministic audit finding when the rule is structural, a mode
or module line when it is judgment guidance, and an on-demand template when it is
a document shape. Always-resident text (adapters, core contract) has strict word
and character budgets that are enforced by tests; prefer on-demand assets. Record
the mapping here with the source named precisely enough to re-check it.
