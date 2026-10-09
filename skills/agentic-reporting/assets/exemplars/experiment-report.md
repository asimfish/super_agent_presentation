# Exemplar: experiment-report

Read for reasoning and register, not factual content; this is an illustrative
fixture. It answers a question, interprets a discriminating comparison, preserves
counterevidence, and proposes a test with different implications for its outcomes.
It omits metric definitions and row-by-row recitation. Full data stay in the
paired research-reporting examples; no real study or causal mechanism is claimed.

## English

Contrastive training improves in-domain retrieval but fails the tested
cross-domain check. The question was whether it learns a more transferable
representation. NDCG@10 rises from 0.410 to 0.450 in-domain and falls from 0.360
to 0.330 on the shifted corpus, with matched training and evaluation budgets.
This weakens the transfer hypothesis here; specialization remains a hypothesis.

The comparison uses five seeds, means and SD, with no significance test or
per-seed results available. Next, change only the domain composition of positive
pairs under the same budget. If shifted-corpus performance recovers while the
in-domain advantage remains, pursue pair composition; if both fall, revisit the
objective. Keep the current method as a candidate, pending that control.

## 中文

对比训练提升了域内检索，但没有通过这次跨域检查。我们要回答的是：它是否学到
了更可迁移的表示？在训练和评测预算一致时，NDCG@10 在域内从 0.410 升至
0.450，在域外从 0.360 降至 0.330。这削弱了当前设置下的迁移假设；是否发生了
领域特化，还需要对照。

每个配置 5 个种子，报均值和标准差，没做显著性检验，也没有逐种子结果。下一步
保持预算不变，只改变正例对的领域组成。如果域外表现恢复且域内优势保留，继续
研究样本组成；如果两边都退步，重新检查训练目标。目前保留为候选，等待这项对照。
