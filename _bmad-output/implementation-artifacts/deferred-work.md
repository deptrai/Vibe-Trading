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


## Deferred from: code review of 3-4-walk-forward-analysis-wfa.md (2026-05-11)
- Rủi ro cạn kiệt tài nguyên (OOM/DoS) khi đọc file kết quả [agent/api_server.py:1284] — API server đọc toàn bộ JSON vào bộ nhớ mà không kiểm tra kích thước.
- Lỗ hổng bảo mật truy cập resource job của user khác [agent/api_server.py:1275] — Thiếu kiểm tra ownership job (Multi-tenancy).

## Deferred from: code review of 5-3-automated-cleanup-scaling-policy.md (2026-05-11)
- Hardcode danh sách queue trong Autoscaler [agent/src/autoscaler.py:17] — Danh sách queue bị hardcode lặp lại với file cấu hình worker.py.

## Deferred from: code review of 5-1-tiered-priority-queue-for-premium-users.md (2026-05-11)
- Naive Timezone Handling & crash if tz-aware/tz-naive mismatch [agent/src/rl_optimizer.py:168] — deferred, pre-existing from story 3-4
- timeframe_override invalid date format parser crash [agent/src/rl_optimizer.py:162] — deferred, pre-existing from story 3-4
- Inconsistent Math Signage in Decay Calculation [agent/src/rl_optimizer.py] — deferred, pre-existing from story 3-4
- Flawed WFA Window Constraint via Strict Intersection [agent/src/rl_optimizer.py] — deferred, pre-existing from story 3-4
- Non-Atomic File Writes Risking JSON Decode Errors [agent/src/rl_optimizer.py] — deferred, pre-existing from story 3-4
- Arbitrary and Silent WFA Truncation at 20 windows [agent/src/rl_optimizer.py] — deferred, pre-existing from story 3-4
- Hardcoded and Inflexible JWT Algorithm (HS256) [agent/api_server.py] — deferred, pre-existing
- Fake Integration Tests testing `apply_async` mock instead of real Redis [agent/tests/integration/test_worker_tiered_routing.py] — deferred, pre-existing

## Deferred from: code review of 6-1-generative-strategy-copilot.md (2026-05-11)
- Queue name injection from JWT `user_tier`. — deferred, pre-existing
- Timezone Mismatch Risks in RL Optimizer. — deferred, pre-existing
- Inconsistent WFA Decay Calculation. — deferred, pre-existing
- Tautological Tests for Tiered Routing. — deferred, pre-existing
