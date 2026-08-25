# 合成模型上线风险报告

## 风险态势

首个 30 天假设窗口内，最需要在 rollout 前升级处理的是 R1 数据重叠风险：影响为高、发生可能性为中，但证据置信度低。以下等级是序数优先级，不是校准概率；风险接受权未由证据指定。

本报告仅使用合成展示数据，不代表真实研究或生产结果。

## 量表与风险登记

Likelihood 与 impact 均使用 Low/Medium/High。总体优先级由两轴的定性组合给出，不做数值相乘。

下表汇总三个风险的证据、控制、owner、触发器和残余风险。

| ID | 条件→事件→后果 | 可能性 / 影响 / 置信 | 现有控制 | 处理与 owner | 触发器 | 残余风险 |
|---|---|---|---|---|---|---|
| R1 | 重叠未知→评估被污染→错误 rollout 决策 | M / H / Low | held-out manifest | 运行 overlap audit；Evaluation role | 发现任一共享记录 | audit 前仍为 M/H |
| R2 | 输入漂移→准确率下降→服务质量退化 | M / M / Medium | drift dashboard | 分层复核；Monitoring role | weekly proxy 下降 3 个百分点 | 控制后仍为 M/M |
| R3 | rollback 工件不可用→恢复延迟→影响扩大 | L / H / Medium | artifact checksum | rollback rehearsal；Release role | rehearsal 失败 | rehearsal 通过后 L/M |

登记事实来自[本地合成包](../inputs/risk-report.md)。Owner 是合成责任角色，不代表真实授权；计划中的控制在完成条件未验证前不能计作已生效。

## 边界与监测

真实流量频率、财务影响和校准概率均未测，因此不支持期望损失或精确概率结论。任何 overlap、3 个百分点 proxy 下降或 rollback rehearsal 失败都应触发复评；最终是否接受残余风险仍需有授权的决策者决定。
