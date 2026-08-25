# Agentic reporting showcase

本索引中的事实与数字全部来自本地 synthetic fixtures；它展示汇报结构，不代表真实研究或生产结果。

## 12 个核心模式

### Concise answer (`concise-answer`)

首句直接回答沙箱开关可启用，同时把生产批准排除在证据之外。

- 成品：[报告](modes/concise-answer.md)
- 路由：[route](routes/concise-answer.json) · [checkpoint](checkpoints/concise-answer.json) · [bundle](bundles/concise-answer.txt)
- 验收：strict audit **PASS**（0 errors / 0 warnings）· semantic oracle **PASS**（[记录](oracles/concise-answer.md))

### Implementation handoff (`implementation-handoff`)

以“部分完成”呈现 CSV 导出改动、8 项单元验证和三条未验证路径。

- 成品：[报告](modes/implementation-handoff.md)
- 路由：[route](routes/implementation-handoff.json) · [checkpoint](checkpoints/implementation-handoff.json) · [bundle](bundles/implementation-handoff.txt)
- 验收：strict audit **PASS**（0 errors / 0 warnings）· semantic oracle **PASS**（[记录](oracles/implementation-handoff.md))

### Status update (`status-update`)

按 Batch 1/2/3 展示已完成、checksum 阻塞和下一迁移前沿。

- 成品：[报告](modes/status-update.md)
- 路由：[route](routes/status-update.json) · [checkpoint](checkpoints/status-update.json) · [bundle](bundles/status-update.txt)
- 验收：strict audit **PASS**（0 errors / 0 warnings）· semantic oracle **PASS**（[记录](oracles/status-update.md))

### Investigation report (`investigation-report`)

用单变量重现与反事实将 flush timer 识别为合成重放范围内的根因。

- 成品：[报告](modes/investigation-report.md)
- 路由：[route](routes/investigation-report.json) · [checkpoint](checkpoints/investigation-report.json) · [bundle](bundles/investigation-report.txt)
- 验收：strict audit **PASS**（0 errors / 0 warnings）· semantic oracle **PASS**（[记录](oracles/investigation-report.md))

### Experiment report (`experiment-report`)

逐 run 与 mean±SD 展示 11 ms 延迟收益和 0.45pp 准确率代价。

- 成品：[报告](modes/experiment-report.md)
- 路由：[route](routes/experiment-report.json) · [checkpoint](checkpoints/experiment-report.json) · [bundle](bundles/experiment-report.txt)
- 验收：strict audit **PASS**（0 errors / 0 warnings）· semantic oracle **PASS**（[记录](oracles/experiment-report.md))

### Decision brief (`decision-brief`)

在统一约束下比较三种队列，推荐 B 但保留成本与扩容复审触发器。

- 成品：[报告](modes/decision-brief.md)
- 路由：[route](routes/decision-brief.json) · [checkpoint](checkpoints/decision-brief.json) · [bundle](bundles/decision-brief.txt)
- 验收：strict audit **PASS**（0 errors / 0 warnings）· semantic oracle **PASS**（[记录](oracles/decision-brief.md))

### Academic synthesis (`academic-synthesis`)

只围绕虚构 [S1]/[S2] 综合预测时域与风险转交，不冒充真实文献。

- 成品：[报告](modes/academic-synthesis.md)
- 路由：[route](routes/academic-synthesis.json) · [checkpoint](checkpoints/academic-synthesis.json) · [bundle](bundles/academic-synthesis.txt)
- 验收：strict audit **PASS**（0 errors / 0 warnings）· semantic oracle **PASS**（[记录](oracles/academic-synthesis.md))

### Research idea (`research-idea`)

把 uncertainty gate 设想绑定到 baseline、falsifier、失败模式和停止条件。

- 成品：[报告](modes/research-idea.md)
- 路由：[route](routes/research-idea.json) · [checkpoint](checkpoints/research-idea.json) · [bundle](bundles/research-idea.txt)
- 验收：strict audit **PASS**（0 errors / 0 warnings）· semantic oracle **PASS**（[记录](oracles/research-idea.md))

### Review report (`review-report`)

两个 finding 按严重级别置前，并给出精确行号、影响和最小修正。

- 成品：[报告](modes/review-report.md)
- 路由：[route](routes/review-report.json) · [checkpoint](checkpoints/review-report.json) · [bundle](bundles/review-report.txt)
- 验收：strict audit **PASS**（0 errors / 0 warnings）· semantic oracle **PASS**（[记录](oracles/review-report.md))

### Incident update (`incident-update`)

报告已恢复但仍监控；回滚的观测效果不等于 resolved 或根因确认。

- 成品：[报告](modes/incident-update.md)
- 路由：[route](routes/incident-update.json) · [checkpoint](checkpoints/incident-update.json) · [bundle](bundles/incident-update.txt)
- 验收：strict audit **PASS**（0 errors / 0 warnings）· semantic oracle **PASS**（[记录](oracles/incident-update.md))

### Postmortem (`postmortem`)

分开触发、近因和系统性因素，并为三项预防控制指定合成 owner。

- 成品：[报告](modes/postmortem.md)
- 路由：[route](routes/postmortem.json) · [checkpoint](checkpoints/postmortem.json) · [bundle](bundles/postmortem.txt)
- 验收：strict audit **PASS**（0 errors / 0 warnings）· semantic oracle **PASS**（[记录](oracles/postmortem.md))

### Risk report (`risk-report`)

用三个稳定 risk ID 展示 ordinal rating、控制、残余风险、owner 与 trigger。

- 成品：[报告](modes/risk-report.md)
- 路由：[route](routes/risk-report.json) · [checkpoint](checkpoints/risk-report.json) · [bundle](bundles/risk-report.txt)
- 验收：strict audit **PASS**（0 errors / 0 warnings）· semantic oracle **PASS**（[记录](oracles/risk-report.md))

## 4 个领域 profile

以下四份仍使用核心 primary mode；profile 只提供领域协议覆盖层。

### Reinforcement learning (`reinforcement-learning`)

完整列出 5 个 seed、mean±SD、95% t CI、final-checkpoint 规则和显著性边界。

- 成品：[报告](profiles/reinforcement-learning.md)
- 路由：[route](routes/reinforcement-learning.json) · [checkpoint](checkpoints/reinforcement-learning.json) · [bundle](bundles/reinforcement-learning.txt)
- 验收：strict audit **PASS**（0 errors / 0 warnings）· semantic oracle **PASS**（[记录](oracles/reinforcement-learning.md))

### Embodied AI (`embodied-ai`)

把 sim/real 的硬件、控制频率、成功定义、latency 与安全停机严格分组。

- 成品：[报告](profiles/embodied-ai.md)
- 路由：[route](routes/embodied-ai.json) · [checkpoint](checkpoints/embodied-ai.json) · [bundle](bundles/embodied-ai.txt)
- 验收：strict audit **PASS**（0 errors / 0 warnings）· semantic oracle **PASS**（[记录](oracles/embodied-ai.md))

### World models (`world-models`)

围绕 H={5,10,20,40} 的误差累积假设，分开 open-loop 与 closed-loop falsifier。

- 成品：[报告](profiles/world-models.md)
- 路由：[route](routes/world-models.json) · [checkpoint](checkpoints/world-models.json) · [bundle](bundles/world-models.txt)
- 验收：strict audit **PASS**（0 errors / 0 warnings）· semantic oracle **PASS**（[记录](oracles/world-models.md))

### VLA (`vla`)

联合呈现 action chunk、控制周期、OOD、遥操作覆盖、人工接管和部署风险。

- 成品：[报告](profiles/vla.md)
- 路由：[route](routes/vla.json) · [checkpoint](checkpoints/vla.json) · [bundle](bundles/vla.txt)
- 验收：strict audit **PASS**（0 errors / 0 warnings）· semantic oracle **PASS**（[记录](oracles/vla.md))

## HTML 演示

### Adaptive Action Chunking（7 页 synthetic VLA academic talk）

Assertion–evidence 叙事把长中文标题、机制图、协议表、精确计数横条、metric cards、边界和下一实验组织为一条 7 页阅读路径。

- 成品：[HTML](html/deck.html) · [PDF](render/academic-talk.pdf) · [contact sheet](render/contact-sheet.png)
- 逐页：[1](render/slide-1.png) · [2](render/slide-2.png) · [3](render/slide-3.png) · [4](render/slide-4.png) · [5](render/slide-5.png) · [6](render/slide-6.png) · [7](render/slide-7.png)
- 路由：[route](routes/html-academic-talk.json) · [checkpoint](checkpoints/html-academic-talk.json) · [bundle](bundles/html-academic-talk.txt)
- 验收：静态 9/9；Chrome PDF 7 页、1152×648；DOM/text/edge/title-safe checks 全通过；人工逐页 7/7 PASS。

## 验收与可追溯性

- [Audit summary](audit-summary.md)
- [Machine manifest](manifest.json)
- [首次失败与修正轨迹](first-failures.md)
- [Markdown audit commands](audit-commands-all.json)
- [Semantic oracle summary](semantic-oracle-summary.json)
