## What and why

<!-- One paragraph: the problem, the change, and the evidence it works. -->

## Checklist

- [ ] `python3 scripts/check_test_env.py` shows no local filesystem hazard
- [ ] `python3 -m unittest discover -s tests` is green locally
- [ ] `python3 scripts/presentation_benchmark.py smoke` passes
- [ ] `dist/` rebuilt in this PR if references or the routing catalog changed
- [ ] Rendering-visible template changes come with real-render regression fixtures
- [ ] No new effectiveness claim outside the BENCHMARK.md evidence gates
- [ ] Every number added to docs points at the code, receipt, or artifact that produced it
