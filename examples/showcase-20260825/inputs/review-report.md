# Synthetic evidence pack: review-report

- Nature: synthetic document review fixture; no real API is represented.
- Review target: `SYN-API-DOC v0.2`, sections 2–4 only.
- Criterion: retries must define duplicate-write behavior; result schemas must distinguish zero from missing.
- Locator section 2, line 14: "Clients may retry writes after timeout." No idempotency key or duplicate-write semantics follow in the reviewed section.
- Locator section 3, line 26: omitted counts and measured zero are both encoded as numeric `0`.
- Locator section 4, line 41: authentication failure is explicitly specified as typed error `AUTH_DENIED`.
- Not reviewed: implementation, tests, deployment config, or sections outside 2–4.
