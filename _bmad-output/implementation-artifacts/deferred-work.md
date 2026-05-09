## Deferred from: code review of 1-1-secure-service-to-service-bridge.md (2026-05-09)
- Performance Anti-Pattern: Per-Request Configuration Parsing [agent/api_server.py:364] — Parsing ALLOWED_IPS on every request is inefficient and should be cached at startup.
