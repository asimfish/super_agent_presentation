# Synthetic evidence pack: decision-brief

- Nature: synthetic showcase fixture; no decision has been authorized.
- Objective: select a batch ingestion design for 100 synthetic items/minute.
- Constraint: p95 acknowledgement below 150 ms and replay after process restart.
- Option A, memory queue: p95 80 ms; cannot replay after restart; low operating complexity.
- Option B, local durable queue: p95 110 ms; replay observed in 3/3 restart probes; medium operating complexity.
- Option C, managed broker: p95 145 ms; replay observed in 3/3 restart probes; high operating complexity and an unmeasured external dependency.
- Not measured: behavior above 100 items/minute, multi-region recovery, or cost.
