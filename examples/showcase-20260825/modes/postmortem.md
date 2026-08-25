# 合成批处理延迟事故复盘

## 摘要与影响

在 synthetic UTC 10:02–10:20，空 pool-size 配置回退为单 worker，导致 500 个计划作业中 12% 晚于计划超过 10 分钟。10:13 禁用 fallback，10:20 队列恢复并重放延迟作业；检查过的合成 ledger 没有数据丢失证据，但这不是全系统无丢失证明。

本报告仅使用合成展示数据，不代表真实研究或生产结果。

## 时间线表

下表仅保留改变检测、缓解或恢复解释的关键事件。

| 时间（synthetic UTC） | 事件 | 证据类型 |
|---|---|---|
| 10:02 | 配置 promotion 启用空值 fallback | 合成事件记录 |
| 10:07 | queue-depth alert 触发 | 合成告警记录 |
| 10:13 | fallback 被禁用 | 合成响应记录 |
| 10:20 | 队列低于阈值，延迟作业完成重放 | 合成队列与作业记录 |

## 原因层次

- **触发：** 配置 promotion 带入空 pool-size 值。
- **近因机制：** 空值 fallback 解析为一个 worker，处理能力下降。
- **系统性因素：** 配置路径没有 canary，且 schema 没有 worker 数下界校验。
- **限制影响的因素：** queue-depth alert 在 5 分钟后触发，保留了可重放作业。

该因果链来自[合成证据包](../inputs/postmortem.md)；没有证据支持归因于个人，也未证明只有这一条贡献路径。

## 修复、预防与后续行动表

下表中的 owner、完成条件与状态全部来自合成 fixture；计划不等于已完成控制。

| 动作 | Owner（合成角色） | 完成条件 | 状态 |
|---|---|---|---|
| 拒绝空值与小于 2 的 pool size | Platform role | schema 负例和配置加载路径均拒绝 | 待执行 |
| 为配置 promotion 增加 canary | Release role | canary 检出单 worker 配置并阻止 promotion | 待执行 |
| 告警携带 active worker count | Observability role | 告警记录含 worker count 与配置版本 | 待执行 |

残余风险是这些控制尚未实施；不能把动作计划写成风险已消除。复盘也未覆盖其他配置字段或真实流量行为。
