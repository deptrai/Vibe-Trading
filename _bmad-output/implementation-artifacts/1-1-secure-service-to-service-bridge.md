---
story_id: '1.1'
story_key: '1-1-secure-service-to-service-bridge'
epic_num: 1
story_num: 1
title: 'Secure Service-to-Service Bridge'
status: 'done'
---

# Story 1.1: Secure Service-to-Service Bridge

## User Story
**As a** System Admin,
**I want** to establish a secure connection between Nowing and Vibe-Trading using Bearer Token and IP Whitelisting,
**So that** only Nowing can access the execution engine.

## Acceptance Criteria
- **Given** Vibe-Trading API server is running
- **When** Nowing sends a request with the correct `API_AUTH_KEY` and from a whitelisted IP
- **Then** Vibe-Trading returns a 200 OK response
- **And** any request without a valid key or from an unknown IP returns 401 Unauthorized or 403 Forbidden

## Developer Context

### 🔬 Exhaustive Analysis & Guardrails

#### Current State (api_server.py)
- The current server uses `HTTPBearer` for authentication.
- `require_auth` dependency validates `API_AUTH_KEY`.
- `require_local_or_auth` protects settings endpoints.
- `_is_local_client` helper identifies loopback clients.
- `API_AUTH_KEY` is currently commented out in `.env.example`.

#### Technical Requirements
- **IP Whitelisting:** Implement a check for `ALLOWED_IPS` environment variable. This should be a comma-separated list of IP addresses.
- **Middleware/Dependency:** Integrate the IP check into the existing `require_auth` or as a new dependency applied to relevant routes.
- **Environment Variables:**
  - `API_AUTH_KEY`: Existing, ensure it is enforced.
  - `ALLOWED_IPS`: New, e.g., `ALLOWED_IPS=127.0.0.1,192.168.1.100`.
- **Security:** Use `ipaddress` module to safely parse and compare IPs. Handle the case where `ALLOWED_IPS` is empty (allow all or allow local).

#### Architecture Compliance
- **Microservice Specialist Worker Pattern:** Vibe-Trading is the worker; Nowing is the orchestrator.
- **Stateless-ish:** The bridge should not introduce session affinity.

#### Library & Framework Requirements
- **FastAPI:** Use `Depends` for reusable security logic.
- **Python:** Use `from __future__ import annotations` and strict type hints as per `project-context.md`.
- **Pydantic v2:** For any new settings/schemas.

### 📂 Files to Modify

| File | Change Description |
|------|--------------------|
| `agent/api_server.py` | Update `require_auth` or add `require_whitelisted_ip` dependency. Implement `ALLOWED_IPS` check. |
| `agent/.env.example` | Add `ALLOWED_IPS` with example values and descriptive comments. |

### 🧪 Testing Requirements
- **Unit Test:** Create a test to mock `request.client.host` and verify 200/401/403 behaviors.
- **Integration Test:** Verify that setting `ALLOWED_IPS` in `.env` actually blocks/allows traffic.

### 📜 Project Context Reference
- **Security:** Do NOT log sensitive keys or whitelisted IPs.
- **Naming:** Use `snake_case` for Python functions and variables.
- **Linting:** Must pass `ruff check` and `ruff format`.

---
**Status:** ready-for-dev
**Note:** Ultimate context engine analysis completed - comprehensive developer guide created.

### Review Findings
- [x] [Review][Decision] Potential IP Spoofing / Reverse Proxy Masking — The app relies on `request.client.host`. If behind a proxy, `X-Forwarded-For` is needed. Should we support `X-Forwarded-For`?
- [x] [Review][Patch] Missing IP verification when API key is configured [agent/api_server.py:457]
- [x] [Review][Patch] Unhandled TypeError during IPv4/IPv6 Mixed Comparison [agent/api_server.py:375]
- [x] [Review][Patch] Fragile Error Handling Invalidates Entire Whitelist [agent/api_server.py:374]
- [x] [Review][Patch] Strict Subnet Parsing Fails Silently [agent/api_server.py:374]
- [x] [Review][Patch] Missing required automated tests [agent/tests]
- [x] [Review][Patch] Direct use of os.getenv instead of Pydantic [agent/api_server.py:364]
- [x] [Review][Defer] Performance Anti-Pattern: Per-Request Configuration Parsing [agent/api_server.py:364] — **Resolved 2026-05-11** via env-string-keyed cache in `_get_allowed_networks()`
