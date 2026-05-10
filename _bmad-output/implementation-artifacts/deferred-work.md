## Deferred from: code review of 1-1-secure-service-to-service-bridge.md (2026-05-09)
- ~~Performance Anti-Pattern: Per-Request Configuration Parsing [agent/api_server.py:364]~~ — **Resolved 2026-05-11**: `_get_allowed_networks()` now caches by env string (auto-invalidates on runtime change); `_configured_api_key()` documented with fallback pattern.
## Deferred from: code review of 2-1-async-job-queue-with-redis-celery.md (2026-05-10)
- Missing Rate Limiting for Resource-Intensive Queues [agent/api_server.py:1185] — deferred, pre-existing / out of scope
- Large payload bloating Redis broker [agent/api_server.py:1189] — deferred, payload is currently small configuration only
## Deferred from: code review of 2-2-crypto-first-data-loading-system.md (2026-05-10)
- Flawed Asset Classification Heuristic (`endswith("USD")` etc.) [agent/src/worker.py:19] — deferred, pre-existing

## Deferred from: code review of 2-3-2-year-lookback-constraint-results-persistence.md (2026-05-10)
- Static Gas Fee Assumption [agent/src/worker.py:180] — Current logic uses a static gas fee instead of dynamic/market-based estimation.
- Missing Storage Limit/Safety check — The system does not verify disk space before saving large CSV files.

## Deferred from: code review of 3-2-knowledge-graph-integration-news-to-asset.md (2026-05-11)
- Singleton `get_kg_store()` not thread-safe at module level — low-probability startup race [agent/src/kg_store.py:264-279]
- `import hashlib` unused in kg_crawler.py — leftover from planned URL-hash dedup [agent/src/kg_crawler.py:3]

