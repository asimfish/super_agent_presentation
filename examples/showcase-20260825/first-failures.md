# 首次失败轨迹

## 路由批次：reinforcement-learning bundle

- 阶段：写作前 bounded bundle 生成。
- 首次命令：`python3 skills/agentic-reporting/scripts/reportctl.py bundle --checkpoint /private/tmp/agent-report-showcase-20260825-agent/checkpoints/reinforcement-learning.json --max-chars 16000`
- 首次结果：退出码 1。
- 原始错误：`reportctl: Bundle is 16789 characters, above --max-chars=16000. Remove a module or increase the explicit bound.`
- 分类：显式上下文预算不足；不是报告语义、证据或产品测试失败。
- 修正：保留既定 `experiment-report`、`reinforcement-learning` profile、`tables` 与 `evidence` 两个必要模块，将显式预算提高为 24000；重跑全部 route/checkpoint/bundle，以统一留下完整收据。

## 路由批次：vla profile

- 阶段：写作前 route。
- 首次组合：`risk-report` + `vla` profile。
- 首次结果：退出码 1。
- 原始错误：`reportctl: Research profiles are not applicable to primary mode 'risk-report'`。
- 分类：模式/profile 组合不合法；不是成品审计失败。
- 修正：改为研究型主模式 `experiment-report` + `vla` profile，并在成品中保留评估结果与部署风险边界；领域 profile 仍与 12 个核心模式样例分开。

## 12 个核心模式：首次 strict audit

- 阶段：首稿 checkpoint-bound `audit --strict --json`。
- 首次结果：12 份中 1 份通过，11 份因 warning 在 strict 下失败。
- 主要 finding：`missing-semantic`、`table-without-context`、`over-sectioned` 与一项 `outcome-not-first`；没有 audit error。
- 修正原则：补充真实存在的语义标签与表格说明，合并过度标题；不添加证据包以外的事实，不降低 strict。
- 附带工具失败：首次收据汇总片段把整数 `errors`/`warnings` 误当成数组调用 `len()`，产生 `TypeError`；该错误不影响原始 JSON 收据，后续按整数字段读取。
- 第二次结果：10/12 通过；`academic-synthesis` 的“限制”未命中审计器要求的“局限/limitations”词项，`experiment-report` 仍有 6 个标题。修正为显式“局限”并合并结果标题后再次重跑。
- 第三次结果：11/12 通过；合并标题后 `experiment-report` 首段没有显式“结果”词项，触发 `outcome-not-first`。在原事实句前补“主要结果是”，不改变数据或结论。

## 4 个领域 profile：首次 strict audit

- 首次结果：0/4 strict 通过；均为 warning，无 error。
- `reinforcement-learning`、`embodied-ai`、`vla` 缺少显式“指标”语义词；`world-models` 缺少显式“方法”语义词；VLA 第二张风险表缺少邻近说明。
- 修正：在原协议中显式标注“评估指标/方法”，并为风险表增加说明；不改变任何合成数字、比较或边界。

## HTML academic-talk：首次 checkpoint

- 首次组合：冻结任务文本同时包含 `reinforcement-learning` 和 `VLA/action chunking`，显式选择 RL profile。
- 首次结果：退出码 1；`Checkpoint profiles must be reproducible from the frozen task text`。
- 修正：按内容主域选择 `vla` profile，并从任务文本删除冲突的 RL 域标签；保留 `experiment-report`、slide surface、visuals 与 tables。

## HTML 静态门禁：首次检查 harness

- 首次结果：`seven_slides=FAIL`，其余 8 项通过。
- 原因：一次性检查片段使用 `r'<section\\b...'`，把正则词边界误写成字面反斜线；同次 `</section>` 计数为 7。
- 修正：使用 `r'<section\b...'` 重跑同一 HTML；不修改产物来迁就错误检查。

## HTML 成品：首次真实渲染

- 通过：7 页、1152×648、7 张 1760×990 PNG、每页非空、7 个标题左侧余量均大于 4 CSS px。
- 失败：slide 5 的 results figure 继承 `min-height:48vh` 并被 grid 拉伸，slide scroll height 为 935、client height 为 863；footer 的 PDF yMax 为 648.81 pt，确有成品溢出。每页底边另有模板的 `border-bottom`，导致 edge oracle 每页检出 1760 个深色边缘像素。
- 修正：仅在该 showcase 的 print CSS 中给 results evidence 显式 42vh 高度并限制 SVG 高度，同时移除打印页装饰性底边；不修改生产模板，也不放宽文本边界或 edge oracle。

## 16 份 semantic oracle：首次执行

- 首次结果：6/16 PASS。
- 诊断：10 个失败均无 required 字段缺失；简单 forbidden substring 把“不能声称显著优于/跨机器人泛化/风险已消除”等明确否定句误判为违规主张。
- 修正：保留同一禁止词集合，但逐 occurrence 检查同一局部上下文中的中文/英文否定词；只有未被否定的 forbidden assertion 才失败。报告事实不因 oracle 误报而改写。
- 第二次结果：15/16 PASS；`status-update` 使用更具体的“不报告三批完成”，首版否定词表未包含“不报告”。补充该否定操作词后重跑。

## Overall audit summary：首次 strict audit

- 首次结果：must-show 1/1，0 errors，1 warning；`outcome-not-first`。
- 原因：开头两个段落是文档标题和“最终判定”标题，没有出现审计器的“结果/状态”词项。
- 修正：把同一 ALL PASS 句移动为标题后的首个普通段落并增加“最终结果”前缀；总数、证据和边界不变。
