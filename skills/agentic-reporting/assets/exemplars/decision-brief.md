# Exemplar: decision-brief

Read this for register, not content; the figures are illustrative. Notice what
it does. It opens with the recommendation and the deadline that makes it
urgent. It gives the three reasons as measured facts in one paragraph. It names
the only real alternative and what choosing it costs, and closes with the one
condition that would reopen the decision. Notice what it omits: no options
matrix for a two-option choice, no separate "risks" section repeating the same
caveat, no sentence explaining what a pilot cannot prove.

## English

Approve moving the CI build cluster from on-demand instances to a three-year
reserved plus spot mix before the price lock closes on 15 September. The monthly
bill falls from $48.2k to $21.7k, $318k a year; in a 30-day dual run of 528
builds no failed build escaped, and p95 build time rose from 14.2 to 14.6
minutes against a 15-minute SLO. Migration costs about $22k of engineering time,
under a tenth of the first year's saving, and the on-demand template stays as a
two-hour rollback. The only alternative is the status quo, which after 15
September means the same $48.2k without today's quote. Other cloud providers
were not compared. Revisit if spot interruptions climb above 5% a day, the
level at which p95 would cross the SLO.

## 中文

建议批准：在 9 月 15 日锁价窗口关闭前，把 CI 构建集群从按需实例迁到「3 年
期预留 + 竞价」混合方案。月账单从 $48.2k 降到 $21.7k，一年省 $318k；30 天双
跑 528 次构建没有失败逃逸，p95 构建时长从 14.2 分钟升到 14.6 分钟，SLO 是 15
分钟。迁移约花 $22k 工程时间，不到首年省额的一成；按需实例的配置模板保留，
2 小时内可以切回。唯一的备选是维持现状，9 月 15 日之后就是同样的 $48.2k 而
拿不到今天的报价。没有比较其他云厂商。如果竞价中断率超过每天 5%（p95 会
在这个水平越过 SLO），这个决定要重新讨论。
