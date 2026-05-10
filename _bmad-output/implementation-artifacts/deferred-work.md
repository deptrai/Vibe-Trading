## Deferred from: code review of 1-1-secure-service-to-service-bridge.md (2026-05-09)
- Performance Anti-Pattern: Per-Request Configuration Parsing [agent/api_server.py:364] — Parsing ALLOWED_IPS on every request is inefficient and should be cached at startup.
## Deferred from: code review of 2-1-async-job-queue-with-redis-celery.md (2026-05-10)
- Missing Rate Limiting for Resource-Intensive Queues [agent/api_server.py:1185] — deferred, pre-existing / out of scope
- Large payload bloating Redis broker [agent/api_server.py:1189] — deferred, payload is currently small configuration only
## Deferred from: code review of 2-2-multi-market-data-loading-system.md (2026-05-10)
- Flawed Asset Classification Heuristic (`endswith("USD")` etc.) [agent/src/worker.py:19] — deferred, pre-existing

## Deferred from: code review of 2-3-2-year-lookback-constraint-results-persistence.md (2026-05-10)
- Static Gas Fee Assumption [agent/src/worker.py:180] — Current logic uses a static gas fee instead of dynamic/market-based estimation.
- Missing Storage Limit/Safety check — The system does not verify disk space before saving large CSV files.
