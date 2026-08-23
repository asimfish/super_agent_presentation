# Incident update

Use this mode while an operational incident, outage, degradation, security event, or
recovery is active. Optimize for current truth, coordination, and the next update;
reserve complete causal analysis for a postmortem.

## Semantic order

1. **As of:** include an unambiguous timestamp and timezone.
2. **Impact:** state affected users, services, regions, data, or operations and the
   best verified magnitude. Label estimates.
3. **Current state:** state investigating, identified, mitigating, monitoring,
   recovered, or resolved, with plain-language evidence.
4. **Actions taken:** list material containment, rollback, failover, or recovery
   actions and their observed effect.
5. **Known and unknown:** distinguish confirmed facts, suspected causes, and open
   questions.
6. **Next action and update:** name the operational next step, responsible role when
   known, and next communication time or trigger.

## State discipline

- A rollback can restore user traffic while leaving a new release blocked. State
  both conditions.
- Use `resolved` only when impact has ended, recovery checks pass, and the selected
  incident process permits closure.
- Do not confirm a root cause from temporal proximity alone.
- If metrics are delayed, partial, or stale, state that explicitly.
- Preserve the previous update's important correction; do not silently replace a
  mistaken statement.
- Keep live updates short. Link the incident log or detailed technical investigation
  instead of copying it.

## Security and privacy

Do not expose credentials, customer-identifying data, private exploit detail, or
operational information that increases risk. Use the authorized incident channel and
audience. A public update may require a narrower statement than an internal update.

## Avoid

- Speculation presented as cause.
- `All clear` based on one recovering metric.
- A long technical chronology before impact and current state.
- Assigning blame to an individual or team.
- Promising an update time that has not been established.
