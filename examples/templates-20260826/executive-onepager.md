# Recommendation: adopt the managed event queue for order processing before the Q4 change freeze

All facts below are synthetic showcase data; they demonstrate the template, not a
real decision.

The self-hosted broker has been stable for two years, but the synthetic Q4
traffic forecast doubles peak order volume while the team that operates the
broker shrinks from four engineers to two. A decision is needed before the
change freeze on 2026-09-15.

## Why: the three reasons

- Reliability evidence favors the managed queue: in the synthetic 30-day trial
  it delivered 99.98% availability versus 99.72% for the self-hosted broker,
  and the broker's two outages both required manual failover.
- Operating cost shifts from people to a bounded bill: the trial invoice
  projects $3,100 per month, while broker upkeep currently consumes a verified
  0.8 engineer-months per month, more than the team can staff after Q4.
- Migration risk is smallest now: order-event consumers already read through
  the shared client interface, so the trial required no consumer code changes.

## Options considered

The alternative of staying self-hosted and automating failover was evaluated
and scored on the same criteria; it removes the single manual step but leaves
capacity and upgrade work with the smaller team. Deferring past Q4 was
rejected because the freeze blocks migration during the highest-risk period.

## What it costs and what could change the answer

The trade-off is vendor lock-in at the transport layer and a caveat on the cost
figure: the $3,100 projection assumes the forecast volume, and a 3x overrun
would exceed the current broker cost. Revisit this decision if the trial's
availability advantage does not hold for a full billing cycle or if the vendor
changes egress pricing.

## Decision requested

Approve the migration budget and the 2026-09-08 cutover window by 2026-09-01.
Next action on approval: the platform lead schedules the cutover rehearsal. If
the decision is deferred, order processing enters Q4 on the understaffed
self-hosted path.
