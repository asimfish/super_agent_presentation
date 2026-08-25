# Semantic oracle: vla

- Result: **PASS**
- Bound report SHA-256: `611e0e9c4c0bd02fe5a7f98caeb3ae6c6a840d23cb78fb4404f62be60fd7c552`
- Evidence boundary: synthetic local fixture only; no real research or production claim accepted.

## Human semantic checks

- PASS — action interface、chunking、控制频率和时延完整
- PASS — seen/OOD、takeover/safety stop 与单训练 run 边界清楚
- PASS — 遥操作数据 overlap 与跨 embodiment 风险未隐藏

## Prohibited-claim check

- PASS — report-specific forbidden expressions and unresolved template markers are absent.
- PASS — required synthetic boundary is visible; unsupported and unverified claims remain explicit.

## Oracle boundary

This record combines a human content review with literal regression checks. It does not independently authenticate the synthetic fixture or establish real-world validity.
