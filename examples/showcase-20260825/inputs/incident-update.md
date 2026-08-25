# Synthetic evidence pack: incident-update

- Nature: synthetic incident fixture; not production telemetry.
- Timezone: synthetic UTC.
- 09:10: API p95 rose from a 400 ms reference to 1.9 s; 18 of 200 synthetic requests exceeded 2 s.
- 09:18: the new batching path was rolled back.
- 09:23: p95 measured 440 ms over the next 100 synthetic requests.
- Current gaps: error-rate audit is incomplete; root cause is not confirmed; data-integrity review has not completed.
- Rollback is available and was executed, but incident closure criteria require stable latency plus completed error and integrity checks.
