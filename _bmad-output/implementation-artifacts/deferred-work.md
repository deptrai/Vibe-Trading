## Deferred from: code review of 1-1-secure-service-to-service-bridge.md (2026-05-09)
- Performance Anti-Pattern: Per-Request Configuration Parsing [agent/api_server.py:364] — Parsing ALLOWED_IPS on every request is inefficient and should be cached at startup.
## Deferred from: code review of 2-1-async-job-queue-with-redis-celery.md (2026-05-10)
- Missing Rate Limiting for Resource-Intensive Queues [agent/api_server.py:1185] — deferred, pre-existing / out of scope
- Large payload bloating Redis broker [agent/api_server.py:1189] — deferred, payload is currently small configuration only
