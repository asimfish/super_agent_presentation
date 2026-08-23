# Performance evidence

## Perf: malformed Markdown image scan — 2026-08-24

**Bottleneck.** The original inline-image regular expression restarted from every
unclosed `![` candidate. On malformed generated Markdown, doubling input size
approximately quadrupled scan time.

**Change.** `reportctl audit` and the development benchmark now use a bounded,
forward-only state machine. Alt text is limited to 2,048 characters and an image
target plus optional title to 4,096 characters. The supported subset still covers
escaped alt characters, safe local and strict HTTP(S) targets, and quoted titles.

**Workload.** Strings containing only repeated, unclosed `![`; five timed runs per
size after one warm-up. Measurements used Python 3.9.6 on an Apple M2 Max (`arm64`).

| Input | Old regex median ± SD | New scanner median ± SD | Median speedup |
|---:|---:|---:|---:|
| 4,096 bytes | 0.095257 ± 0.000301 s | 0.000277 ± 0.000025 s | 344× |
| 8,192 bytes | 0.380115 ± 0.026318 s | 0.000558 ± 0.000004 s | 681× |
| 16,384 bytes | 1.507332 ± 0.007342 s | 0.001142 ± 0.000030 s | 1,320× |

The new end-to-end audit measured a 0.010569-second median on the 65,536-byte
workload over five runs. This is development-machine evidence, not a universal
latency guarantee. Regression tests give both audit and benchmark processes a wide
five-second ceiling on that workload; the ceiling is intended to catch algorithmic
regression rather than enforce a service-level objective.

Audit additionally stops image inspection after detecting more than 1,000 images
and stops all analysis after 500 findings, emitting one explicit error that the
remaining content was not fully audited. Line numbers use a precomputed newline
index rather than rescanning the prefix for every match. A 680KB, 40,000-image
adversarial report and a repeated-placeholder finding-amplification case are both
covered by five-second end-to-end regression ceilings. Reports and benchmark
responses above 100,000 lines fail before allocating per-line structural lists.

## Perf: literal-mask memory — 2026-08-24

**Bottleneck.** A first implementation represented every backtick run with Python
tuples and a full per-character next-run table. A 4 MiB alternating-backtick input
peaked near 406 MiB in an isolated reviewer probe.

**Change.** An intermediate compact-array implementation reduced that peak to
71.8–88.2 MB. The final source-lexical broad gate no longer needs inline backtick
run tables: canonical credit only needs a fenced-code/HTML-block mask, while the
forbidden/audit gate scans raw markers directly. The same input produced no image
candidates and completed in 0.0166–0.0175 seconds across Python 3.9.6 and 3.14.3 on
the development machine. Observed process peaks were 27.3–41.6 MB, including
interpreter and module-import cost.

The isolated regression uses the exact 4 MiB workload for both scanners, permits a
wide 10-second scan ceiling, and requires process peak memory below 192 MiB. These
are regression tripwires, not latency or memory guarantees for every platform.
