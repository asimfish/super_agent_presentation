# SBAR handoff: checkout latency escalation to the payments on-call

All facts below are synthetic showcase data; they demonstrate the template, not a
real incident.

## Situation

As of 2026-08-26 09:40 UTC, checkout requests in the synthetic EU region are
degraded: p95 latency is 2.4 s against a 400 ms reference, affecting an observed
41 of 210 sampled user sessions. Current status: mitigating, impact ongoing. I am
handing this to the payments on-call because the slow calls concentrate in the
payment-authorization dependency.

## Background

The payments client library was upgraded at 08:55 UTC in release 26.34. Traffic
and infrastructure dashboards show no deploy or load change on the checkout
service itself. Rolling back the checkout frontend at 09:15 had no observed
effect, which is evidence against a frontend cause. Detailed traces are in the
synthetic incident bundle referenced by this handoff.

## Assessment

My judgment: the library upgrade is the leading suspect because the latency step
change follows it within two minutes and the slow spans are verified to sit
inside authorization calls. This remains a suspected cause, not a confirmed one;
the connection-pool saturation seen in traces could also come from an upstream
provider change.

## Recommendation

Requested next action: roll the payments client back to release 26.33 in the
synthetic EU region by 10:10 UTC and watch the authorization p95 for 15 minutes.
If rollback is not possible by then, raise the connection-pool ceiling as the
holding measure and page the provider liaison. Please confirm which action you
will take.
