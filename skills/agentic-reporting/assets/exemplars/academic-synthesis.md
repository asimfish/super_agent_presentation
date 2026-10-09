# Exemplar: academic-synthesis

Read for reasoning and register. Papers A and B below are fictional teaching
sources, not citations or evidence of novelty. The passage separates the authors'
explanation, the measured result, and the reader's assessment; it ends on the
missing comparison rather than a list of techniques or scores.

## English

Paper A proposes memory retrieval to reduce long-context errors, but the
inspected evidence does not isolate retrieval from extra inference compute.
Its Table 2 compares the memory system at twice the baseline's token budget;
that supports a system-level comparison at those budgets, not the claimed
mechanism. Paper B's Table 1 compares a larger budget without memory on a
different corpus, so its result cannot resolve A's confound.

For our project, ask whether memory helps at matched inference token budgets.
Compare on the same corpus and budget, and measure retrieval overhead before
claiming matched total compute. This is a proposed control, not a reported result. The
source set is limited to the supplied excerpts; broader novelty is unresolved.

## 中文

论文 A 用记忆检索减少长上下文错误，但目前查到的证据没有把检索作用和额外推理
计算区分开。表 2 中，记忆系统的 token 预算是基线的两倍；它支持这两个预算下的
系统比较，还不足以确认作者提出的机制。论文 B 的表 1 测了不带记忆的更大预算，
但语料不同，无法补上 A 的对照。

对我们而言，关键问题是相同推理 token 预算下记忆是否仍有收益。先在同一语料和
token 预算下比较，并测量检索开销，再判断总计算量是否对齐。这是我们提出的
对照，不是两篇论文的结论。
目前只查了提供的节选，更广范围的创新性仍未确定。
