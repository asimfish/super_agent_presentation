# Postmortem

Use this mode after an incident to create a blameless, durable record of impact,
causes, response, learning, and owned prevention work. Do not use it as a substitute
for a live incident update.

## Semantic order

1. **Metadata:** incident date, report status, owner, audience, and relevant service
   or system boundary.
2. **Executive summary:** state impact, duration, trigger, root or contributing
   causes, and recovery at a decision-useful level.
3. **Impact:** quantify affected population, operations, data, SLOs, duration, or
   cost where evidence permits; label estimates and gaps.
4. **Timeline:** record decision-relevant detection, escalation, mitigation,
   recovery, and verification events with timestamps and timezones.
5. **Cause analysis:** distinguish trigger, proximate mechanism, root control gaps,
   contributing conditions, and factors that limited impact.
6. **Response analysis:** explain detection, recovery, communication, what worked,
   what did not, and where luck affected the outcome.
7. **Actions:** specify preventive and mitigative work with owner, priority, tracker,
   due state, and a verifiable completion condition.
8. **Lessons and residual risk:** state reusable learning and what remains exposed.

## Blameless analysis

- Describe what the system, process, interface, automation, or information allowed to
  happen. Do not reduce the cause to an individual's mistake.
- Assume responders acted with the information and constraints available at the
  time; analyze how those conditions can be improved.
- Include counterevidence and competing causes when the root-cause account remains
  uncertain.
- Separate observed events from hindsight interpretation.

## Action quality

Avoid vague actions such as `improve`, `be careful`, or `train everyone` without an
observable end state. Prefer controls that prevent recurrence, bound blast radius,
shorten detection, accelerate mitigation, or improve verification. Give every
accepted action a single accountable owner or role and a tracking mechanism.

## Avoid

- Writing a postmortem before evidence is stable while presenting it as final.
- Omitting impact because an exact number is unavailable; provide a bounded estimate
  or name the measurement gap.
- A detailed timeline with no causal analysis.
- Action items that only address people while leaving the enabling system unchanged.
- Declaring recurrence impossible or risk eliminated.
