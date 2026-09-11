# Exemplar: status-update

Read this for register, not content; names, dates, and numbers are illustrative.
Notice what it does: says the state in the first three words, puts the one fact
that matters (the deadline) in the first sentence, names the owner and the hour,
and says what the reader will be asked to decide and when. Notice what it
omits: no "completed / in progress / blocked" scaffolding for a four-item
update, no restating of the plan, no list of what this update does not cover.

## English

Retrieval v2 is at risk: last night's regression passed 408 of 412 cases, the
four failures are all in rerank (R-102, R-118, R-240, R-333), and the release
freezes today at 18:00. Liang owns the fix and will open the PR before 14:00;
the working theory is the similarity threshold moved from 0.87 to 0.91, which
the fix will confirm or rule out. Trunk is not locked, so other teams are
unaffected. No decision is needed from you now. If the PR is not up by 14:00, I
will ask to move the freeze to Monday.

## 中文

检索服务 v2 有风险：昨夜回归 412 条过了 408 条，4 条失败都在 rerank（R-102、
R-118、R-240、R-333），今天 18:00 封板。梁工负责修复，14:00 前提 PR；初步归
因是相似度阈值从 0.87 调到了 0.91，修复合入后就能确认。主干没锁，其他团队不
受影响。目前不需要你拍板；如果 14:00 PR 还没到，我会申请把封板推到下周一。
