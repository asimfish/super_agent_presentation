# Reinforcement-learning profile：五 seed 结果

主要结果是：在 `SyntheticReach-v0` 的同一合成协议下，Method P 的最高观测 mean return 为 510，但两种方法的 95% t 区间重叠；没有统计检验，不能据此宣布 P 显著优于 Q。

本报告仅使用合成展示数据，不代表真实研究或生产结果。

## 研究问题与方法协议

问题是固定训练交互预算后，两种方法的最终 episodic return 是否呈现可区分的种子级分布。环境是假想有限时域 MDP，horizon 200、discount 0.99；评估指标 return 是每个 seed 上 20 个 deterministic evaluation episodes 的未折扣平均回报，越高越好。每个方法使用 5 个独立训练 seed。

两种方法都报告 1 million environment steps 的最终 checkpoint；超参数配置在这 5 个 seed 之前固定。主机和交互预算相同，没有失败或排除 seed。wall-clock 与能耗未测，完整 fixture 见[合成证据包](../inputs/reinforcement-learning.md)。

## 逐 seed 与聚合结果表

下表保留所有 seed；`±` 是 seed-level sample SD，95% CI 是在 n=5 和 t 分布假设下对均值计算的双侧区间。

| 方法 | Seed 1 | Seed 2 | Seed 3 | Seed 4 | Seed 5 | Mean±SD（return，↑） | 95% t CI |
|---|---:|---:|---:|---:|---:|---:|---:|
| P | 510 | 530 | 490 | 520 | 500 | 510.0±15.8 | [490.4, 529.6] |
| Q | 500 | 505 | 495 | 510 | 490 | 500.0±7.9 | [490.2, 509.8] |

P 的 Seed 3 为 490，是与“稳定提高”叙事相矛盾的低值；不能只报告 Seed 2 的 530。Q 的观测离散度较小，但 n=5 不支持对总体稳定性作强结论。

## 不确定性边界与下一实验

这些 t 区间依赖小样本正态近似；同编号 seed 没有声明配对环境实例。没有假设检验、效应量预注册或多任务覆盖，因此允许的解释仅是 P 在这个合成任务上的观测均值较高。下一步是预先定义最小实际差异和配对规则，增加独立 seed，并在其他任务上重复；这些尚未执行。
