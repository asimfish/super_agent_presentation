# VLA profile：action chunking、OOD 与部署风险

主要结果是：一个合成 VLA checkpoint 在 seen suite 成功 16/20、在 OOD 视觉扰动下成功 8/20；OOD 同时出现 5 次人工接管和 2 次安全停机。只有一次训练运行，不能把差异归因于 OOD 或推广到其他机器人。

本报告仅使用合成展示数据，不代表真实研究或生产结果。

## 研究问题与系统协议

问题是固定 final checkpoint 后，视觉 OOD 条件下的成功、接管和部署时延如何变化。评估指标是 task success（越高越好）、人工接管/安全停机和 inference latency（越低越好）。策略由单次训练得到，训练包含 800 条单臂、固定相机的遥操作轨迹；连续 delta-pose action 以 10 Hz 执行，每次预测 4-action chunk，相当于最多 400 ms 不重规划。设备 X 上 100 次推理的 p50/p95 为 78/135 ms，控制周期为 100 ms。

## 评估结果与不确定性表

下表中的成功 CI 是 trial-level Wilson 95% interval；它不包含训练随机性。接管与安全停机均计为失败，无 retry。

| 协议组 | Trial | 成功（%，↑） | Wilson 95% CI | 人工接管 | 安全停机 |
|---|---:|---:|---|---:|---:|
| Seen | 20 | 16/20（80%） | [58.4%, 91.9%] | 1/20 | 0/20 |
| OOD visual perturbation | 20 | 8/20（40%） | [21.9%, 61.3%] | 5/20 | 2/20 |

观测上 OOD 成功更低且接管更多，但没有多训练 seed 或显著性检验。p95 inference 超过 100 ms 控制周期，且 4-action chunk 会延长无新感知反馈的动作窗口；当前证据没有逐 rollout 对齐 latency 与失败，不能宣称二者存在因果关系。

## 部署风险表、边界与下一实验

下表把现有控制与仍然存在的 residual risk、owner 和触发器分开。

| 风险 | 当前控制 | 残余风险 | 合成 owner / 触发器 |
|---|---|---|---|
| 400 ms chunk 内感知过时 | safety stop | 接触前仍可能执行陈旧动作 | Control role / p95>100 ms |
| 遥操作数据覆盖未知 | OOD suite | scene overlap 与扰动覆盖未核验 | Data role / 任一 overlap |
| OOD 时人工负担增加 | takeover | 5/20 接管，规模仍很小 | Safety role / takeover>预注册阈值 |

下一步应增加独立训练 seed，核验 train/eval scene overlap，并比较 chunk 1/2/4 在 matched compute 下的成功、接管、停机与 deadline miss。其他 embodiment、能耗、contention latency 和真实 teleoperation 覆盖未验证，不能声称跨机器人泛化或部署安全。数据来自[本地合成包](../inputs/vla.md)。
