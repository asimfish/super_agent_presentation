# Research idea brief

Use this mode to present, challenge, or decide whether to pursue a paper idea,
research hypothesis, or proposed empirical contribution. It is an argument for a
testable program, not an abstract for work that has already succeeded.

## Semantic order

1. **Thesis:** state the proposed change and intended outcome in one jargon-light
   sentence.
2. **Problem and current limit:** identify who or what is affected, how the problem
   is handled now, and the specific unresolved limitation.
3. **Hypothesis and mechanism:** state why the proposed intervention should change
   the measured outcome. Separate prior evidence from conjecture.
4. **Novelty delta:** compare against the closest approaches on an explicit axis;
   do not claim novelty from unfamiliar wording.
5. **Decisive evaluation:** define the smallest experiment that could support or
   falsify the hypothesis, including baselines, metrics, controls, and failure
   criteria.
6. **Risk and feasibility:** expose scientific, data, compute, implementation, and
   evaluation risks together with mitigations or kill criteria.
7. **Decision:** state the next evidence-producing step, resource envelope, and
   mid-point/final checks.

## Idea evidence contract

- Label observations from papers, preliminary runs, or existing artifacts as
  evidence and locate them.
- Label the proposed mechanism, expected result, and impact as hypotheses until
  tested.
- Name the closest alternatives before claiming a gap or novelty.
- Define what negative or null evidence would make the idea change or stop.
- Avoid fabricated expected gains, target venues, timelines, or implementation
  ease.

## Useful displays

- A one-row claim-to-test table: claim, intervention, control, metric, falsifier.
- A comparison matrix with explicit axes rather than a generic related-work list.
- A compact risk register when feasibility drives the decision.
- One mechanism diagram only when it makes the causal or computational proposal
  easier to inspect.

## Avoid

- Writing a future experiment as if it were a verified contribution.
- Defining the gap as “no one has combined A and B.”
- Treating an implementation plan as scientific evidence.
- Listing many experiments without identifying the decisive one.

Provenance: the question sequence is independently synthesized from the DARPA
Heilmeier Catechism and ML conference reproducibility/checklist criteria. See
`docs/TEMPLATE-SOURCES.md` in the repository for source links and boundaries.
