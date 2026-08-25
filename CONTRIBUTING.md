# Contributing

Contributions are welcome. This repository holds itself to the same standard it
asks of agent reports: every claim needs evidence, every artifact needs a
verifiable receipt.

## Development setup

```bash
git clone https://github.com/asimfish/super_agent_presentation.git
cd super_agent_presentation
python3 -m pip install -r requirements-dev.txt   # validation-only test deps
```

Runtime code is Python standard library only (3.9+); do not add runtime
dependencies without an ADR in `docs/adr/`.

## Before you open a PR

1. **Run the full test suite** — it must stay green on Python 3.9:

   ```bash
   python3 -m unittest discover -s tests -v
   python3 scripts/presentation_benchmark.py smoke
   ```

2. **Keep `dist/` reproducible.** If you change anything under
   `skills/agentic-reporting/references/` or the routing catalog, rebuild and
   commit the distribution in the same change:

   ```bash
   python3 skills/agentic-reporting/scripts/reportctl.py build-dist \
     --output dist --force
   ```

   CI diffs a fresh build against the committed `dist/` and fails on drift.

3. **Template or protocol changes need regression coverage.** Rendering-visible
   changes to `assets/presentations/` require the filled-deck real-render tests
   in `tests/test_template_assets.py` to pass; add fixtures (including long CJK
   and mixed-script titles) for any new layout-sensitive element.

4. **Never add an effectiveness claim without evidence.** Statements like
   "improves readability/quality/efficiency" are gated by the preregistered
   study pipeline and claim gates in [BENCHMARK.md](BENCHMARK.md). Anything not
   measured under those gates must be phrased as a mechanism or a boundary, not
   a result. The checked-in pilot is permanently `insufficient_evidence`; do not
   cite it as proof.

5. **Documented numbers need pointers.** Any count or measurement in docs
   (context budgets, test counts, audit results) must point at the code,
   receipt, or artifact that produced it.

## Commit style

Follow the existing history: a conventional prefix (`feat:`, `fix:`, `docs:`,
`release:`, `test:`) plus a short imperative subject, with a body explaining the
why when it is not obvious.

## Security

Do not include secrets, tokens, or private run data (checkpoints, private study
directories) in commits. See [SECURITY.md](SECURITY.md) for the threat model and
reporting process.
