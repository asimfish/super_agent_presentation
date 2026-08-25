# Synthetic evidence pack: postmortem

- Nature: synthetic postmortem fixture; not a real incident.
- Incident window: 10:02–10:20 synthetic UTC.
- Impact: 12% of 500 scheduled jobs completed more than 10 minutes late; no data-loss evidence in the inspected synthetic ledger.
- 10:02: configuration promotion enabled an empty-value fallback.
- 10:07: queue-depth alert fired.
- 10:13: fallback disabled.
- 10:20: queue returned below threshold and delayed jobs were replayed.
- Proximate mechanism: empty pool-size value resolved to one worker.
- Systemic factors: no canary for the configuration path and no lower-bound validation.
- Action owners supplied by fixture: Platform role for validation; Release role for canary; Observability role for alert context.
