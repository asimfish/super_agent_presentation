# Showcase audit summary

最终结果：ALL PASS：16 份 Markdown、HTML、PDF 与 7 张 PNG 全部通过。

## 最终判定

这里的 ALL PASS 仅表示本轮定义的 synthetic、结构、语义和本机真实渲染验收全部满足；它不表示真实研究结论、生产有效性或跨浏览器兼容性。

## 验证结果表

下表汇总最终一次、与成品 SHA 绑定的验收结果。

| 验收面 | 总数 | 通过 | 失败 | 证据 |
|---|---:|---:|---:|---|
| Markdown checkpoint strict audit | 16 | 16 | 0 | `audits/*.json`、`audit-commands-all.json` |
| Report-specific semantic oracle | 16 | 16 | 0 | `oracles/*.md`、`semantic-oracle-summary.json` |
| HTML static/self-contained checks | 9 | 9 | 0 | `html/static-validation.json` |
| PDF/DOM/text/PNG render checks | 11 | 11 | 0 | `render/validation.json` |
| 人工逐页视觉检查 | 7 | 7 | 0 | `render/manual-visual-check.md` |

## 修正过的首次失败

失败轨迹未删除，完整记录见 `first-failures.md`。包括：bundle 16,000 字符预算不足；不合法的 risk-report+VLA profile；核心模式 strict 首稿 1/12；profile strict 首稿 0/4；HTML profile checkpoint 冲突；静态 slide-count 正则 harness 错误；slide 5 首次真实渲染溢出与打印底边；semantic oracle 对否定句的误报。所有受影响检查均在修正后从相同或更严格边界重跑。

## 产物与交接

- 主索引：`index.md`
- 机器清单：`manifest.json`
- HTML/PDF/contact sheet：`html/deck.html`、`render/academic-talk.pdf`、`render/contact-sheet.png`
- 路由、checkpoint、bundle、audit、oracle 和 render receipt 均位于本目录。

## 未验证边界与下一步

所有内容均为 synthetic fixture；未核验真实论文、模型、机器人或生产系统。渲染仅覆盖 macOS、Chrome 151.0.7922.172、当前系统字体与本机 Poppler；未验证 Firefox、Safari、Linux、其他 CJK 字体、Quarto 或 Reveal.js。showcase 回合没有运行生产仓库测试，也没有修改、暂存、提交、推送、打标签或发布。下一步仅需导师按 `index.md` 进行独立观感复验。
