# World-models profile：误差感知的短视域刷新

研究想法是：在 action-conditioned latent world model 中加入 multi-step consistency 和 error-aware refresh gate，并每 5 个真实步骤重规划，以延缓长 rollout 的误差累积。这是机制假设，不是已验证贡献。

本报告仅使用合成展示数据，不代表真实研究或生产结果。

## 问题、角色与机制方法假设

世界模型的角色限定为 receding-horizon controller 的预测器，而不是通用环境模拟器。核心假设是单步误差会随想象 horizon 累积，refresh gate 可在模型进入低可靠区域前重新编码真实观察；候选 H 为 5、10、20、40 latent steps。当前[合成证据包](../inputs/world-models.md)没有预实验或文献，故“累积方式”和“refresh 有效”都只是待检验预测。

## 可证伪评估表

下表把开放环预测与闭环控制分开，避免用好看的预测直接替代控制证据。

| 层级 | 干预与对照 | 指标 | 支持信号 | 证伪/停止条件 |
|---|---|---|---|---|
| Open-loop | full；无 refresh；仅 one-step；无 action conditioning | H-conditioned latent error、decoded error（↓） | full 在 H=20/40 降低误差增长，同时 H=5 不退化 | 误差优势只在 teacher-forced 短步成立，或 refresh 与随机刷新相当 |
| Closed-loop | full；各模型基线；reactive policy | episodic return（↑）、constraint violations（↓） | matched planning budget 下同时改善 return 或约束 | 预测改善不转化为控制，或 planner exploitation 增加违规 |

最小实验固定数据、模型规模、规划样本数和真实交互预算；分别扫描 H，并报告模型计算和 wall-clock。新颖性、资源预算与具体数据分布尚未建立。

## 失败模式、证据边界与下一步

主要失败模式包括随机多模态动力学被均值化、gate 校准失败、planner exploitation、长 horizon 计算超预算，以及 decoded error 与任务相关误差不一致。下一步先构造可控动力学夹具并验证“无 action conditioning”与“随机 refresh”两个机制对照；若 full 不能在 H 增长时改变误差斜率，或闭环违规增加，则停止控制收益主张而不是扩大模型。
