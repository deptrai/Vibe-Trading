---
stepsCompleted: ['step-01-init', 'step-02-context', 'step-03-starter', 'step-04-decisions', 'step-05-patterns', 'step-06-structure', 'step-07-validation', 'step-08-complete']
inputDocuments: ['_bmad-output/planning-artifacts/prd.md', '_bmad-output/project-context.md']
workflowType: 'architecture'
project_name: 'Vibe-Trading Integration (Nowing)'
user_name: 'Luisphan'
date: '2026-05-05'
---

# Architecture Decision Document

_This document outlines the technical solutioning and architecture decisions for integrating Vibe-Trading into the Nowing ecosystem, directly addressing the PRD requirements._

## 1. Technical Components & Data Flow (Nowing-Vibe Internal Bridge)

**Integration Pattern: Microservice Specialist Worker**
- **Nowing (Orchestrator):** Acts as the user-facing gateway, handling natural language NLP extraction, user authentication, and serving as the Source of Truth for system state.
- **Vibe-Trading (Execution Engine):** Acts as the "Stateless-ish" backend engine that executes quantitative computations, backtests, and AI processing behind the scenes.

**Data Flow:**
1. **User Input:** User submits a prompt via Nowing. Nowing extracts symbols, indicators, and timeframes (FR1).
2. **Preview (FR2):** If confidence score is < 0.9, Nowing hits a lightweight Vibe-Trading preview API to generate a Visual Strategy Preview Card.
3. **Execution:** Nowing submits a job to Vibe-Trading via internal REST API, which enqueues it to Celery/Redis.
4. **Execution Cache:** Vibe-Trading stores the running artifacts in the Shared File System (EFS/NFS) inside `runs/`.
5. **Updates:** Nowing tracks the progress via Server-Sent Events (SSE) or polling Redis task status.
6. **Delivery:** Once the job succeeds, Nowing fetches the Backtest Metrics and Equity Curve from the Shared File System to display to the user.

## 2. Standardized Payload Schema (The Contract)

To support rich data from user documents and standardize communication, Nowing and Vibe-Trading communicate via a strict JSON schema.

**Payload Structure (Zod/TypeScript):**
- **Simulation Environment:** `exchange`, `instrument_type` (SPOT/PERPETUAL), `initial_capital`, `trading_fees`, `slippage_tolerance`, `historical_range`, `gas_fee_model`, `track_impermanent_loss`.
- **Risk Management:** `max_drawdown_percentage`, `stop_loss/take_profit`, `position_sizing`, `leverage`.
- **Context Rules:** `assets`, `timeframe`, `indicators`, `natural_language_rules`, and `executable_code`.
- **Execution Flags:** `enable_monte_carlo_stress_test`, `enable_rl_optimization`, `wfa_config` (In-sample/Out-of-sample split).

Nowing is strictly responsible for parsing user intent/documents into this schema before dispatching the job.

## 3. Redis/Celery Implementation

**Architecture Details:**
- **Broker & State Backend:** Redis is used for high-throughput, reliable task queueing. It ensures jobs are not lost if an execution worker crashes mid-task.
- **Workers:** Auto-scaling Celery (or BullMQ) workers picking up asynchronous jobs.
- **Task Types:** Separated into queues (e.g., `backtest`, `rl_optimization`, `knowledge_graph_sync`, `monte_carlo_stress_test`).

**Scalability & Reliability (NFRs):**
- **Auto-scaling:** Workers scale automatically when the Redis queue length exceeds 10 jobs.
- **Latency:** Ensures the main API latency stays < 500ms, as the API only queues the job and returns a `job_id`. Backtests process asynchronously in < 30s.

## 4. Knowledge Graph, RL, & Monte Carlo Isolation

**Proactive Knowledge Graph (News-to-Asset Correlation) (FR4):**
- **Data Sync:** Independent background tasks crawl financial news and update the internal Knowledge Graph.
- **Integration:** Exposes an API endpoint `GET /api/v1/kg/suggestions` for Nowing to query proactively.

**Offline Reinforcement Learning (Strategy Tuning) (FR3):**
- **Worker Isolation:** RL tasks are extremely compute-intensive. They are routed to a dedicated `vibe-trading-rl-worker` queue.
- **Resource Quotas:** The RL workers are deployed in strictly isolated Docker containers.

**Monte Carlo Stress Test (Quick Win P3):**
- **Worker Isolation:** Resampling simulations (10,000+ runs) to calculate 'Black Swan' risk probabilities are routed to dedicated analytical workers.

## 5. Fulfillment of PRD Requirements

**Functional Requirements:**
- **FR1 (NLP to Schema):** Nowing delegates parsing; Vibe-Trading receives strict `VibeTradingJobPayload` via message queue (Section 2).
- **FR2 (Preview Card):** Vibe-Trading provides a low-latency synchronous `/preview` endpoint (Section 1).
- **FR3 / FR7 (User-facing Optimize & Offline RL):** Consolidated path — user "Optimize" trigger in Nowing dispatches to isolated RL Celery workers (Section 4). Single implementation satisfies both FRs.
- **FR4 / FR8 (Knowledge Graph):** FR4 (News-to-Asset, Phase 1 crypto-focused) maintained asynchronously; FR8 (macro expansion) extends the same graph schema in Phase 2. Accessible via `/api/v1/kg/suggestions` (Section 4).
- **FR5 (PDF Reports & Marketplace Publishing):** Delegated to Sections 8.1 (Verified PDF) and 8.2 (Marketplace).
- **FR6 (2-year Lookback):** Enforced in the data-loader layer (truncates historical range before dispatch).
- **FR9 (Explainable AI):** See Section 6.
- **FR10 (Interactive Multi-Chart):** See Section 7.
- **FR11 (Verified Data PDF):** See Section 8.1.
- **FR12 (Strategy Marketplace):** See Section 8.2.
- **FR13 (Tiered Priority Queue):** See Section 9.1.
- **FR14 (Admin Monitoring Dashboard):** See Section 9.2.
- **FR15 (Monte Carlo Stress Test):** Worker isolation in Section 4; metrics persisted via Section 1 data flow.
- **FR16 (Generative Strategy Copilot):** See Section 10 (Sandbox execution).
- **FR17 (DeFi-Native Simulator) & FR18 (Perpetual Futures Engine):** Enforced inside the simulation layer consuming `SimulationEnvironment` fields (Section 2); worker-agnostic.
- **FR19 (Walk-Forward Analysis):** See Section 11.

**Domain & Non-Functional Requirements:**
- **Precision:** All PnL calculations use `Decimal` (6 decimal places) in Python, avoiding float drift.
- **Security:** Internal IP Whitelisting (Vibe-Trading only accepts traffic from Nowing). Strategies are encrypted (AES-256) at rest.
- **Caching:** L1 (Redis) & L2 (DuckDB/Parquet) implemented to ensure >70% cache hits and reduce external API calls.
- **Data Resilience:** Automated fallbacks programmed in the data loaders prioritizing Crypto (`ccxt` -> RPC nodes for Phase 1; `yfinance`/`akshare` deferred to Phase 2).
- **Retention:** Cron jobs automatically prune the `runs/` artifacts after 7 days or when disk usage hits 80%.

## 6. Explainable AI (XAI) Narrative Engine (FR9)

**Objective:** Whenever the RL worker (Story 3.1) emits an optimized parameter set, it must attach a structured `xai_trace` payload so Nowing can render a human-readable explanation (Story 3.3).

**Pipeline:**
1. **Trace Capture (Vibe-Trading):** The RL worker logs `{baseline_params, candidate_params, metrics_delta, market_regime_tag, data_window}` for each accepted mutation into `runs/<job_id>/xai_trace.json`.
2. **Explanation Generation (Nowing):** Nowing consumes the trace via `GET /api/v1/runs/{job_id}/xai` and passes it through an LLM prompt template that enforces:
   - Natural language reason (VN/EN)
   - Citation of concrete metric deltas (Sharpe, Max Drawdown, Win Rate)
   - Confidence qualifier (`high`/`medium`/`low`) derived from Out-of-sample decay (from WFA — FR19)
3. **Delivery Contract:** Response schema `{rationale: string, citations: [{metric, before, after, delta}], confidence: enum}` ensures deterministic UI rendering.

**Constraints:** XAI never invents metrics — LLM is constrained to cite only values present in `xai_trace.json`. Hallucination guard: regex-validate that every quoted number appears in the trace before returning.

## 7. Interactive Multi-Chart Payload (FR10)

**Objective:** Deliver a deterministic, ECharts-compatible payload from Vibe-Trading so Nowing can render Equity Curve + Candlestick + Trade Markers without client-side transformation.

**Endpoint:** `GET /api/v1/runs/{job_id}/chart` → `ChartPayload`.

**Schema (`ChartPayload`):**
```json
{
  "meta": { "symbol": "BTC/USDT", "timeframe": "1h", "tz": "UTC" },
  "candles": [[ts, open, high, low, close, volume]],
  "equity_curve": [[ts, equity_value]],
  "trade_markers": [
    { "ts": 1712345600, "side": "BUY|SELL", "price": "decimal", "pnl": "decimal", "label": "string" }
  ],
  "overlays": [
    { "name": "MA20", "series": [[ts, value]] }
  ]
}
```

**Contract Rules:**
- Timestamps are Unix seconds (UTC). All monetary fields are serialized as `Decimal`-compatible strings to preserve 6-digit precision (per NFR5).
- Marker `label` is pre-translated by Vibe-Trading (no additional i18n on client).
- Payload is cache-friendly: immutable per `job_id`, served from L1 Redis with 7-day TTL (aligned with `runs/` retention).

**Performance:** Payload capped at ~5 MB per run; for longer windows, Vibe-Trading downsamples candles (LTTB algorithm) to ≤ 2,000 points while preserving trade-marker precision.

## 8. Verified Data PDF & Strategy Marketplace (FR11, FR12)

### 8.1 Verified Data PDF (FR11 — Story 4.2)

**Trust Chain:**
1. **Data Hashing:** When a backtest completes, Vibe-Trading computes `sha256(canonical_json(metrics + trade_log + equity_curve))` and stores it as `runs/<job_id>/manifest.sha256`.
2. **Manifest Signing:** A detached signature is generated using an Ed25519 service key held in Vibe-Trading's secrets store (`VT_REPORT_SIGNING_KEY`). Signature + public-key-id are embedded in PDF metadata (XMP).
3. **PDF Assembly:** A PDF renderer (WeasyPrint) composes stats, charts, trade log, watermark, and a QR code linking to `/api/v1/verify/{job_id}`.
4. **Public Verification:** `GET /api/v1/verify/{job_id}` returns `{sha256, signature, public_key_id, signed_at}` so any recipient can re-compute the hash from the downloaded payload and verify authenticity offline.

**Revocation:** A `revoked` flag in the DB allows Admin to invalidate a published report without regenerating PDFs (verification endpoint returns 410 Gone).

### 8.2 Strategy Marketplace (FR12 — Story 4.3)

**Ownership Model:** Nowing is authoritative for marketplace metadata (author, description, tags, subscription terms). Vibe-Trading only exposes the underlying `job_id` performance metrics (read-only).

**Publish Flow:**
1. User triggers "Publish" in Nowing → Nowing validates ownership of `job_id`.
2. Nowing calls `POST /api/v1/marketplace/snapshot` on Vibe-Trading with `{job_id, visibility}` to freeze the metrics (prevents post-publish tampering).
3. Vibe-Trading returns an immutable `snapshot_id` + signed metrics digest. Nowing stores `(snapshot_id, author_id, tags, price)` in its own DB.

**Discovery API (Nowing-side):** `GET /marketplace?sort=sharpe|winrate&filter=asset_class`. Results are paginated; rankings use cached pre-aggregated scores (recomputed hourly).

**Protection:** Strategy source code (`executable_code`) is NEVER exposed in marketplace responses. Subscribers receive signal outputs only (unless the author opts into full disclosure).

## 9. Priority Queue & Admin Observability (FR13, FR14)

### 9.1 Tiered Priority Queue (FR13 — Story 5.1)

**Queue Topology:**
- `backtest.premium` — dedicated Celery queue for Premium users; SLA < 5s pickup.
- `backtest.standard` — default queue; best-effort.
- `rl_optimization.premium` / `rl_optimization.standard` — mirrored split for RL workloads.

**Routing Logic:** The API server inspects `payload.user_tier` (signed claim from Nowing JWT) and routes the task to the matching queue. Tampering is prevented by verifying the JWT signature on the Vibe-Trading side.

**Worker Allocation:**
- Minimum 2 workers always reserved for `*.premium` queues to guarantee pickup latency.
- Standard workers auto-scale (NFR6) but never drain the premium reserve.
- Prometheus metric `queue_wait_seconds{tier="premium"}` feeds a PagerDuty alert if p95 > 5s for 3 consecutive minutes.

**Fairness Safeguard:** To avoid starvation of standard tier, each premium worker yields to the standard queue after processing 10 consecutive premium jobs (token-bucket with 10:1 ratio).

### 9.2 Admin Monitoring Dashboard (FR14 — Story 5.2)

**Metrics Exposure:** Vibe-Trading exposes `/metrics` (Prometheus format) and a Nowing-facing aggregated endpoint `GET /api/v1/admin/stats` returning:
```json
{
  "avg_latency_ms": { "preview": 210, "submit": 140, "p95": 480 },
  "cache_hit_rate": { "l1_redis": 0.78, "l2_duckdb": 0.62 },
  "active_workers": { "backtest": 4, "rl": 2, "monte_carlo": 1 },
  "queue_depth": { "premium": 0, "standard": 7 },
  "error_rate_5m": 0.012
}
```

**Alerting:** Nowing Admin UI polls every 10s. Alert channel (email + Slack) fires when:
- `error_rate_5m > 0.05` (AC from Story 5.2)
- `queue_wait_seconds{tier="premium"}` p95 > 5s
- `cache_hit_rate.l1_redis < 0.50` for 10 min (caching SLA regression)

**Access Control:** `/admin/stats` requires a dedicated `VT_ADMIN_KEY` (separate from `API_AUTH_KEY`) scoped to Nowing's admin backend only.

## 10. Generative Strategy Copilot Sandbox (FR16)

**Objective:** Safely execute user-authored `executable_code` (Python/PineScript) generated by the Generative Copilot (Story 6.1) without compromising the host worker.

**Execution Isolation:**
- **Process-level:** Each copilot job runs inside a disposable Docker container (`vibe-trading-sandbox` image) with `--read-only` root FS, no network except a scoped outbound allowlist (only market-data adapters), and CPU/RAM quotas enforced via cgroups (default 1 vCPU / 512 MB).
- **Language-level:** Python code runs under RestrictedPython AST transformer (blocks `exec`, `eval`, `__import__` on disallowed modules). PineScript is transpiled server-side to an internal AST and rejected if it references undefined identifiers.
- **Filesystem:** Only `/tmp/run` (tmpfs, 128 MB) is writable; artifacts must be copied to `/runs/<job_id>/` through a supervised bridge process.

**Validation Pipeline (before execution):**
1. **Static Analysis:** `ruff` + custom linter rejects forbidden imports (`socket`, `subprocess`, `ctypes`, `os.system`).
2. **Dry-Run:** Strategy is first compiled against a 5-trade replay to detect exceptions before real backtest starts.
3. **Resource Budget:** Hard kill after 60s wall-clock or 2× normal memory footprint (`watchdog` sidecar).

**Failure Modes:** Any sandbox breach attempt logs a security event (`vt.security.sandbox_violation`) to the Admin dashboard (FR14). The offending `executable_code` is hashed and added to a deny-list so it cannot be resubmitted.

**Contract with Nowing:** Copilot output must include `{code, language, estimated_complexity}`. Vibe-Trading returns `{status: "compiled"|"rejected", reasons: [...]}` synchronously before accepting the backtest job.

## 11. Walk-Forward Analysis (WFA) (FR19)

**Objective:** Validate strategy robustness by evaluating Out-of-sample (OOS) performance during RL optimization (Story 3.4), guarding against overfitting.

**Algorithm:**
1. **Window Generator:** Given a `wfa_config = {train_window, test_window, step, mode: "rolling"|"anchored"}` (from Standardized Payload Schema, Section 2), the RL worker computes N non-overlapping train/test pairs across the historical range.
2. **Optimization Loop:** For each window i:
   - Train RL tuner on `train_i` → candidate parameters `P_i`.
   - Evaluate `P_i` on `test_i` (OOS) → metrics `M_i_oos`.
   - Compare against in-sample metrics `M_i_is` to compute `decay_rate_i = 1 - (M_oos / M_is)` for Sharpe and PnL.
3. **Aggregation:** Final report contains:
   - `avg_oos_sharpe`, `median_decay_rate`, `worst_window` (for failure analysis).
   - A per-window table surfaced in the PDF report (FR11) and the XAI trace (FR9).

**Acceptance Gate:** The RL worker flags a strategy as `overfit_warning` if median decay rate > 0.40 or if > 30% of OOS windows show negative Sharpe. Nowing surfaces this warning in the Strategy Preview Card (FR2) before the user accepts the optimized parameters.

**Performance:** WFA runs in parallel across windows using Celery chord; target ≤ 2× the baseline single-window RL runtime for a 10-window WFA.
