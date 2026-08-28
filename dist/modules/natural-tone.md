# Display module: natural-tone

# Natural tone module

Load this module when reader-facing prose needs a dedicated de-AI pass: the draft
carries machine-flavored ceremony, template rhetoric, inflated jargon, or
translationese, or the user asks for text that reads like a careful human author.
Run the pass after the content is complete and before the final audit. Tone
rewriting changes wording only; it never changes facts.

Do not load it for code, configuration, logs, verbatim quotations, or legal text,
and do not apply it inside those spans when they appear in a report.

## Fidelity contract

Every rewrite must survive a two-direction reread:

- Forward: every fact in the input is recoverable from the output.
- Backward: every relation asserted in the output traces to the input.

Protected spans are copied, never paraphrased: numbers with the objects they
measure, units, versions, identifiers, commands, paths, API names, error strings,
quoted text, and attribution of who did or said what.

Preserved semantics, each treated as a fact rather than a style choice:

- **Relations:** `shows potential for X` never becomes `achieves X`; correlation
  never becomes adoption or causation.
- **Scope and conditions:** qualifiers such as `on the validation split` or
  `under seed 1-3` stay attached to their claims.
- **Negation, modality, tense, direction, intensity:** `may reduce` is not
  `reduces`; `did not regress` is not `improved`.
- **Abstraction level:** an abstract claim (`提升效率`) is not concretized into a
  specific one (`省时间`) the input never made.
- **Gaps:** missing sources, numbers, or owners become named gaps, never filler.

## Processing order

1. Mark protected spans first.
2. Structural passes next: delete performative opener and closer layers, remove
   meta-commentary about the writing itself, split translationese chains, and
   convert nominalizations back to verbs.
3. Phrase-level substitutions last, so structural deletions do not orphan them.
4. Reread both directions against the fidelity contract before handing off.

## Signals and actions

| Signal | Typical form | Action |
|---|---|---|
| Sycophantic or meta layer | 好问题！让我来为你解释；Great question! I hope this helps | Delete the layer; answer directly |
| Performative closer | 综上所述 / 总而言之 / In conclusion before a trailing summary | Delete; the conclusion already leads under the reader contract |
| Value inflation | 赋能 / 取得显著成效 / 充分体现了；testament to / game-changer / paradigm shift | Replace with the concrete action, number, or delete |
| Hype comparatives | 前所未有 / 史无前例 / 颠覆性；groundbreaking / cutting-edge | Give the comparison data or delete |
| Unsourced authority | 研究表明 / 数据显示 / 有专家指出；studies show | Name the source, or state the claim as the report's own bounded finding, or mark the gap |
| Translationese | 基于…通过…来… chains; stacked passives (被优化、被改进) | Short subject-verb sentences in the active voice |
| Nominalization | 对模型进行了优化 | 优化了模型 |
| Throat-clearing | 值得注意的是 / 需要指出的是；It's worth noting that | Delete; state the point |
| Synonym rotation | 重要 → 关键 → 核心 to dodge repetition | Keep one term; repeating a precise term is correct, rotation is the tell |
| Connective saturation | 然而 / 此外 / 与此同时；however / moreover clustered in one paragraph | Keep at most one; let sentence order carry the logic |
| Intensity saturation | 重要 / 显著 / robust / comprehensive across the whole text | Replace the excess with specifics; do not thin it with synonyms |

## Misfire protection

Leave these untouched even when they match a signal above:

- Domain terms in their technical sense: 闭环 (closed-loop control), 抓手
  (gripper hardware), 收敛 (training convergence), 根因 (incident root cause),
  对齐 (alignment research), 落地 (deployment), leverage (finance), navigate and
  traverse (graphs and topology).
- 显著 when it states statistical significance next to a test and p-value.
- A term under discussion or definition (`什么是赋能`).
- Conventional academic passive voice (`was conducted`, `was published`).
- Real network vernacular grounded in specific first-person detail.

When a phrase matches a banned pattern but carries load-bearing meaning in its
sentence, keep it and improve the sentence around it. The lists name rhetorical
moves, not forbidden strings; a paraphrase that performs the same move is still a
hit, and a listed string doing honest work is not.

## Relationship to the audit

`reportctl audit` flags only the highest-precision subset of these signals as
`ai-tone-boilerplate` warnings. Passing the audit is the floor, not the target:
the target is prose a careful human author would sign, with every fact intact.

This module distills the fidelity contract, tier discipline, and misfire
protections of the MIT-licensed `shuorenhua` skill into this framework's
contract form.
