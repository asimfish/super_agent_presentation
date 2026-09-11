# Exemplar: experiment-report

Read this for register, not content; the numbers are illustrative. Notice what it
does: leads with the finding and its cost, gives numbers in prose, states the
boundaries once in one paragraph, and ends with one position and the condition
that would reverse it. Notice what it omits: no metric definitions, no sentence
about what the numbers cannot be read as, no inventory of every missing detail,
no branch of if-then cases in place of a recommendation.

## English

Energy-guided sampling lowers FID on CIFAR-10 at the cost of coverage. At λ=2,
the best of five weights tested, FID falls from 3.42 to 2.87 (−0.55, 16%) while
Recall drops from 0.61 to 0.58; beyond λ=2 both metrics worsen, and at λ=8 FID
is worse than the unguided baseline. ImageNet-64, tested at two weights only,
moves the same way (18.7 to 16.9). Guidance adds 21% to per-step sampling time
on one A100.

Three seeds per configuration, means with standard deviations, no significance
test; ImageNet-64 Recall was not measured. There is no classifier-free-guidance
arm, so the comparison with the standard alternative is still open.

Take λ=2 into the next round as the candidate, not the default. Fix a Recall
floor and a sampling-time budget before rerunning, add seeds at λ=0, 1, and 2,
and measure ImageNet-64 Recall. If λ=2 misses the floor, or the FID gain does
not hold with new seeds, drop it.

## 中文

能量引导采样在 CIFAR-10 上用覆盖率换 FID。五个权重里 λ=2 最好：FID 从 3.42
降到 2.87（降 0.55，16%），Recall 从 0.61 降到 0.58；λ 再往上两项都变差，λ=8
的 FID 已不如无引导基线。ImageNet-64 只测了两个权重，方向一致（18.7 到
16.9）。引导让单张 A100 上每步采样时间多 21%。

每个配置 3 个种子，报均值和标准差，没做显著性检验；ImageNet-64 没测 Recall。
没有 classifier-free guidance 对照，和标准做法的比较还是空白。

λ=2 带进下一轮，作为候选而不是默认。重跑前先定 Recall 下限和采样耗时预算，
给 λ=0、1、2 加种子，补测 ImageNet-64 的 Recall。如果 λ=2 达不到下限，或者
新种子下 FID 收益不成立，就放弃它。
