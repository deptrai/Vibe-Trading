---
stepsCompleted: ['step-01-validate-prerequisites', 'step-03-create-stories', 'step-04-final-validation']
inputDocuments: ['_bmad-output/planning-artifacts/prd.md', '_bmad-output/planning-artifacts/architecture.md']
workflowType: 'epics'
---

# Vibe-Trading Integration (Nowing) - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Vibe-Trading Integration (Nowing), decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: Bóc tách các tham số (Mã tài sản, Chỉ báo, Tham số, Khung thời gian) từ câu lệnh ngôn ngữ tự nhiên và chuyển thành Standardized Payload Schema.
FR2: Hiển thị Strategy Preview Card để xác nhận thông số khi độ tự tin của AI dưới 0.9.
FR3: Tính năng "Optimize Strategy" tự động tìm bộ tham số tốt nhất qua Reinforcement Learning.
FR4: Tự động phát hiện sự kiện tin tức và đề xuất mã tài sản/chiến lược liên quan từ Knowledge Graph.
FR5: Xuất báo cáo PDF "Verified Data" (Shadow Account Report) và tính năng chia sẻ lên Marketplace.
FR15: Monte Carlo Stress Test - mô phỏng trượt giá/thiệt hại để đo rủi ro "Thiên nga đen".
FR16: Generative Strategy Copilot - Tự động viết mã Python/PineScript dựa trên yêu cầu.
FR17: DeFi-Native Simulator - Mô phỏng chi phí Gas, thanh khoản AMM và Impermanent Loss cho Crypto.
FR18: Perpetual Futures Engine - Mô phỏng Funding Rates, Margin (Cross/Isolated), và Liquidations.
FR19: Walk-Forward Analysis (WFA) - Cơ chế chia In-sample/Out-of-sample để chống Overfitting.

### NonFunctional Requirements

NFR1: Performance - API Latency cho các yêu cầu cơ bản (không tính backtest) < 500ms.
NFR2: Performance - 80% yêu cầu backtest dữ liệu 2 năm hoàn thành trong < 30 giây.
NFR3: Security - 100% giao tiếp nội bộ qua kênh TLS/SSL; IP Whitelisting cho Nowing Backend.
NFR4: Reliability - Hệ thống đạt độ khả dụng 99.9% (Uptime SLA); Hàng đợi Redis bền vững.
NFR5: Accuracy - Sử dụng kiểu dữ liệu Decimal cho mọi tính toán tài chính với độ chính xác 6 chữ số thập phân.
NFR6: Scalability - Worker pool tự động mở rộng instance dựa trên độ dài hàng đợi (> 10 jobs).

### Additional Requirements

- **Microservice Specialist Worker Pattern**: Nowing là Orchestrator, Vibe-Trading là Stateless-ish Execution Engine.
- **Async Job Pattern**: Sử dụng Redis/Celery cho các tác vụ nặng (Backtest, RL).
- **Shared Persistence**: Sử dụng Shared File System (EFS/NFS) cho thư mục `runs/`.
- **Worker Isolation**: RL tasks chạy trên dedicated worker pool với Docker resource quotas (cgroups).
- **Symbol Normalization**: Nowing chịu trách nhiệm chuẩn hóa mã tài sản trước khi gọi Vibe-Trading. Traced implicitly in Story 1.2 (Standardized Payload Schema & NLP Extraction) — normalization rules live inside the Nowing NLP layer and produce canonical symbols consumed by `VibeTradingJobPayload`.
- **Hybrid State Model**: Nowing giữ Source of Truth; Vibe-Trading giữ Execution Cache.
- **Data Resilience**: Tích hợp cơ chế fallback tự động ưu tiên Crypto: `ccxt` → On-chain RPC nodes (Phase 1), `yfinance`/`akshare` (Phase 2). Traced implicitly in Story 2.2 (Crypto-First Data Loading System) — fallback chain is enforced inside the data-loader abstraction.

### UX Design Requirements

(No separate UX document found. Functional requirements FR2 and User Journeys provide core visual/interaction scope.)

### FR Coverage Map

FR1: Epic 1 (Story 1.2) — NLP Extraction & Payload Schema
FR2: Epic 1 (Story 1.3) — Strategy Preview Card
FR3 + FR7: Epic 3 (Story 3.1) — Optimize Strategy & Offline RL (consolidated — a single story covers both the user-facing trigger and the backend RL implementation)
FR4: Epic 3 (Story 3.2) — Knowledge Graph News-to-Asset (Phase 1, crypto-focused)
FR5: Epic 4 (Stories 4.2 + 4.3) — PDF Report + Marketplace Publish
FR6: Epic 2 (Story 2.3) — 2-year Lookback Constraint
FR8: Epic 3 (Story 3.2) — Knowledge Graph macro expansion (Phase 2 scope; same graph schema as FR4, extended to macro news and traditional-finance assets)
FR9: Epic 3 (Story 3.3) — Explainable AI (XAI)
FR10: Epic 4 (Story 4.1) — Interactive Multi-Chart Visualization
FR11: Epic 4 (Story 4.2) — Verified Data PDF Report
FR12: Epic 4 (Story 4.3) — Strategy Marketplace Publish & Discovery
FR13: Epic 5 (Story 5.1) — Tiered Priority Queue
FR14: Epic 5 (Story 5.2) — Admin Monitoring Dashboard
FR15: Epic 2 (Story 2.4) — Monte Carlo Stress Test
FR16: Epic 6 (Story 6.1) — Generative Strategy Copilot
FR17: Epic 2 (Story 2.5) — DeFi-Native Simulation Environment
FR18: Epic 2 (Story 2.6) — Perpetual Futures & Liquidation Engine
FR19: Epic 3 (Story 3.4) — Walk-Forward Analysis (WFA)

### NFR Coverage Map

NFR1 (API Latency < 500ms): Epic 1 (Story 1.3 — Preview endpoint SLA); Epic 2 (Story 2.1 — async enqueue returns immediately); architecture §3 (auto-scaling).
NFR2 (Backtest < 30s): Epic 2 (Story 2.3 — 2-year lookback constraint limits data volume); architecture §3 (Celery async workers).
NFR3 (TLS/SSL + IP Whitelisting): Epic 1 (Story 1.1 — Secure Bridge enforces IP whitelist + API key auth).
NFR4 (Uptime 99.9% + Redis durability): Epic 2 (Story 2.1 — Redis persistent queue); Epic 5 (Story 5.3 — auto-scaling + cleanup).
NFR5 (Decimal precision 6dp): Project-wide coding rule (project-context.md). Enforced implicitly in all financial calculation stories (2.3, 2.4, 2.5, 2.6). No dedicated story — validated via code review.
NFR6 (Auto-scale workers > 10 jobs): Epic 5 (Story 5.3 — Automated Cleanup & Scaling Policy); architecture §3 (auto-scaling trigger).

## Epic List

### Epic 1: Intelligent Trading Assistant & Secure Order Transmission
Thiết lập kết nối bảo mật và bóc tách lệnh từ ngôn ngữ tự nhiên, bảo vệ chiến lược của người dùng.
**FRs covered:** FR1, FR2.

### Epic 2: Crypto-Native Async Execution Engine (Phase 1)
Xây dựng hệ thống hàng đợi Redis/Celery cho backtest chuyên biệt Crypto (Mở rộng đa thị trường ở Phase 2).
**FRs covered:** FR6, FR15, FR17, FR18.

### Epic 3: AI-Driven Strategy Evolution (RL & Graph)
Tối ưu hóa tham số qua RL và kết nối tri thức qua Knowledge Graph.
**FRs covered:** FR3, FR4, FR7, FR8, FR9, FR19.

### Epic 4: Advanced Reporting & Social Marketplace
Hoàn thiện báo cáo PDF và hệ sinh thái chia sẻ chiến lược.
**FRs covered:** FR5, FR10, FR11, FR12.

### Epic 5: Premium User Experience & Enterprise Stability
Quản trị Admin, tối ưu trải nghiệm người dùng Premium và đảm bảo tính ổn định của hệ thống.
**FRs covered:** FR13, FR14.

### Epic 6: Generative Strategy Copilot (Phase 2)
Tự động tạo mã thực thi chiến lược giao dịch từ yêu cầu ngôn ngữ tự nhiên.
**FRs covered:** FR16.

## Epic 1: Intelligent Trading Assistant & Secure Order Transmission
Thiết lập kết nối bảo mật giữa Nowing và Vibe-Trading, bảo vệ tài sản và chiến lược cốt lõi của người dùng, đồng thời xây dựng khả năng bóc tách lệnh thông minh từ ngôn ngữ tự nhiên.

### Story 1.1: Secure Service-to-Service Bridge
As a Nowing End-User,
I want my trading strategies and financial parameters to be transmitted securely to the execution engine,
So that my proprietary trading logic and account details are protected from unauthorized access.

**Acceptance Criteria:**
**Given** Vibe-Trading API server is running
**When** Nowing sends a request with the correct `API_AUTH_KEY` and from a whitelisted IP
**Then** Vibe-Trading returns a 200 OK response
**And** any request without a valid key or from an unknown IP returns 401 Unauthorized

### Story 1.2: Standardized Payload Schema & Natural Language Parameter Extraction
As a Trader (Alex),
I want Nowing to extract trading parameters (Symbol, RSI, Timeframe) from my text prompt or uploaded documents,
So that I don't have to manually fill out a form, and the data is formatted into a strict `VibeTradingJobPayload`.

**Acceptance Criteria:**
**Given** a user prompt or uploaded strategy document
**When** the Nowing NLP engine processes the text
**Then** it returns a validated JSON object conforming to `VibeTradingJobPayload` (SimulationEnvironment, RiskManagement, ContextRules)
**And** it gracefully handles missing parameters by assigning defaults or asking for clarification

**Error Path:**
**Given** the NLP engine cannot extract any recognizable parameters from the input
**When** processing completes
**Then** the system returns a structured clarification request (not a crash) listing which required fields are missing

### Story 1.3: Strategy Preview API
As a Frontend Developer,
I want a lightweight API endpoint to generate preview data for the Strategy Card,
So that I can show the user what the AI understood before running a heavy backtest.

**Acceptance Criteria:**
**Given** extracted parameters from Story 1.2
**When** Nowing calls the `/preview` endpoint
**Then** Vibe-Trading returns a summary of the strategy and a "Confidence Score"
**And** the latency for this response is < 500ms

**Error Path:**
**Given** the `/preview` endpoint receives an invalid or incomplete payload
**When** validation fails
**Then** it returns `400 Bad Request` with a structured error listing missing fields, without crashing the worker

## Epic 2: Crypto-Native Async Execution Engine (Phase 1)
Xây dựng hệ thống hàng đợi Redis/Celery cho backtest chuyên biệt Crypto (Mở rộng đa thị trường ở Phase 2).

### Story 2.1: Async Job Queue with Redis/Celery
As a Trader,
I want my heavy backtest jobs to be processed in the background without freezing the chat interface,
So that I can continue interacting with the AI assistant or submit other tasks while waiting for results.

**Acceptance Criteria:**
**Given** a backtest request from Nowing
**When** the API receives the request
**Then** it enqueues a job to Redis and returns a unique `job_id` immediately
**And** a background Celery worker picks up the job for execution

**Error Path:**
**Given** Redis is unavailable when a job is submitted
**When** the enqueue attempt fails
**Then** the API returns `503 Service Unavailable` with a retry-after header, and no partial job state is left in the queue

### Story 2.2: Crypto-First Data Loading System
As a Trader,
I want the system to prioritize fetching data via CCXT and On-chain RPCs for Crypto assets, while maintaining an open architecture for future VN/US stock expansion,
So that I can seamlessly backtest high-frequency crypto strategies without data latency.

**Acceptance Criteria:**
**Given** a valid symbol (e.g., "BTC/USDT", "ETH/USDC")
**When** the execution engine runs
**Then** it correctly routes the request to CCXT or a fallback RPC node
**And** it gracefully ignores VN/US symbols (returning a "Phase 2 feature" error) if requested
**And** it handles API rate limits using the built-in retry mechanism

### Story 2.3: 2-Year Lookback Constraint & Results Persistence
As a Trader,
I want my backtest results to be reliably saved and accessible for later review, with a sensible 2-year data limit to ensure fast processing,
So that I don't experience timeouts and can always revisit my past strategy reports.

**Acceptance Criteria:**
**Given** a backtest request for "5 years" of data
**When** the job starts
**Then** it automatically truncates the period to the last 2 years
**And** the output (CSV/JSON/Plots) is saved to the shared `/runs/` directory for retrieval

**Error Path:**
**Given** the requested symbol has fewer than 30 days of available data (sparse or new asset)
**When** the job starts
**Then** it returns a warning `{"warning": "insufficient_data", "available_days": N}` and either proceeds with available data or aborts gracefully based on a configurable `min_data_days` threshold

### Story 2.4: Monte Carlo Stress Test
As a Risk-Averse Trader,
I want the engine to run Monte Carlo simulations (resampling) on my backtest results,
So that I can see the probability of "Black Swan" events and extreme drawdowns.

**Acceptance Criteria:**
**Given** a successfully completed backtest job with `enable_monte_carlo_stress_test=true`
**When** the worker processes the flag
**Then** it runs 10,000+ resampled paths on the historical trade series
**And** it outputs a risk distribution graph and 95% Confidence Interval metrics

**Error Path:**
**Given** the backtest has fewer than 30 trades (insufficient sample for meaningful resampling)
**When** Monte Carlo is triggered
**Then** the worker skips simulation and returns `{"warning": "monte_carlo_skipped", "reason": "insufficient_trades", "trade_count": N}` without failing the job

### Story 2.5: DeFi-Native Simulation Environment
As a Crypto/DeFi Trader,
I want the backtest engine to simulate on-chain conditions including Gas Fees, AMM slippage, and Impermanent Loss,
So that my crypto strategies (especially LP strategies) have realistic performance metrics.

**Acceptance Criteria:**
**Given** a backtest job targeting DEXes (`exchange = 'UNISWAP_V3'`)
**When** the simulation executes trades
**Then** it deducts dynamic Gas Fees based on the `gas_fee_model`
**And** it calculates slippage dynamically based on pool liquidity depth rather than a static percentage
**And** it tracks and reports Impermanent Loss if the strategy involves providing liquidity

**Error Path:**
**Given** the pool liquidity data for the requested DEX/pair is unavailable or stale (> 24h)
**When** the simulation attempts to calculate slippage
**Then** it falls back to the `slippage_tolerance` static value from the payload and logs a `{"warning": "stale_liquidity_data", "fallback": "static_slippage"}` in the job result

### Story 2.6: Perpetual Futures & Liquidation Engine
As a Derivatives Trader,
I want the backtest engine to simulate Perpetual Futures mechanics including Funding Rates and Margin Liquidations,
So that I can accurately backtest high-leverage strategies.

**Acceptance Criteria:**
**Given** a backtest job trading Perpetual Futures with leverage > 1x
**When** the simulation executes
**Then** it deducts/adds Funding Rate payments based on simulated 8-hour intervals
**And** it accurately triggers liquidation if the margin ratio drops below the maintenance threshold

**Error Path:**
**Given** the Funding Rate oracle data is unavailable for the requested period
**When** the simulation runs
**Then** it falls back to a configurable default funding rate (e.g., 0.01% per 8h) and logs `{"warning": "funding_rate_fallback", "rate_used": 0.0001}` in the job result

## Epic 3: AI-Driven Strategy Evolution (RL & Graph)
Tối ưu hóa tham số qua RL và kết nối tri thức qua Knowledge Graph.

### Story 3.1: Offline RL Strategy Tuner
As a Trader,
I want the system to automatically suggest the best parameters for my strategy using Reinforcement Learning,
So that my strategy can adapt to different market phases without me being a math expert.

**Acceptance Criteria:**
**Given** a base strategy and a historical dataset
**When** I trigger the "Optimize" command
**Then** a dedicated RL worker runs multiple iterations (mutations) to find the highest Sharpe/PnL ratio
**And** it returns the optimized parameter set (e.g., RSI Period: 10 instead of 14)

**Error Path:**
**Given** the RL optimization fails to converge (all mutations produce worse metrics than baseline) after the maximum iteration budget
**When** the job completes
**Then** it returns the original baseline parameters unchanged with a `{"warning": "rl_no_improvement", "iterations_run": N}` flag, rather than returning a degraded parameter set

### Story 3.2: Knowledge Graph Integration (News-to-Asset)
As a Long-term Investor,
I want Nowing to proactively suggest assets based on crypto and macro news using a Knowledge Graph,
So that I don't miss opportunities when significant on-chain or global events occur.

**Acceptance Criteria:**

**Phase 1 — Crypto-Native Events (in scope):**
**Given** a crypto-specific news event (e.g., "ETH Shanghai upgrade", "BTC halving", "USDC depeg")
**When** the Knowledge Graph is queried
**Then** it returns a list of correlated crypto assets (e.g., ETH, stETH, USDC-related pairs) based on historical on-chain impact
**And** Nowing presents these as a "Proactive Insight" in the chat

**Given** the KG background sync job runs
**When** new crypto news is ingested
**Then** the graph is updated within 5 minutes and `GET /api/v1/kg/suggestions` reflects the new correlations

**Phase 2 — Macro News Expansion (deferred, not in current sprint):**
**Given** a macro-economic event (e.g., "FED interest rate hike")
**When** the Knowledge Graph is queried (Phase 2 feature flag enabled)
**Then** it returns correlated traditional assets (Gold, DXY, Tech Stocks) in addition to crypto
**And** this AC is explicitly gated behind a `ENABLE_MACRO_KG=true` environment flag; default is disabled

**Error Path:**
**Given** the KG service is unavailable or returns empty results
**When** Nowing queries for suggestions
**Then** the system returns an empty suggestion list gracefully (no crash)
**And** logs a warning without surfacing an error to the end user

### Story 3.3: Explainable AI (XAI) for Strategy Changes
As a Skeptical User,
I want the AI to explain the reasoning behind its suggested strategy modifications in natural language,
So that I can trust the AI and understand the "Why" before I trade.

**Acceptance Criteria:**
**Given** an optimized strategy from Story 3.1
**When** the user asks "Why these parameters?"
**Then** the Agent provides a structured explanation conforming to `{rationale: string, citations: [{metric, before, after, delta}], confidence: enum}`
**And** it cites specific metrics (Sharpe improvement, Max Drawdown reduction) with before/after values

**Hallucination Guard:**
**Given** the XAI response is generated
**When** the response contains any numeric value
**Then** every quoted number must be present in the underlying `xai_trace.json` (validated server-side before returning)
**And** if validation fails, the system returns `confidence: "low"` and a warning flag instead of fabricated numbers

**Error Path:**
**Given** `xai_trace.json` is missing or malformed for a given `job_id`
**When** the user requests an explanation
**Then** the system returns a graceful message ("Explanation unavailable — optimization trace not found") without crashing
**And** the error is logged for debugging

### Story 3.4: Walk-Forward Analysis (WFA)
As a Quant Analyst,
I want the system to perform Walk-Forward Analysis during strategy optimization,
So that I can ensure my strategy works on unseen data and isn't overfitted to the past.

**Acceptance Criteria:**
**Given** a request to optimize a strategy via RL
**When** the optimization job runs
**Then** it splits the historical data into rolling In-sample (train) and Out-of-sample (test) windows (default N=10 windows)
**And** it compares performance between the two sets and reports the "Out-of-sample decay rate"

**Error Path:**
**Given** the historical data range is too short to produce at least 3 valid WFA windows
**When** the WFA job starts
**Then** it returns `{"error": "wfa_insufficient_data", "windows_possible": N, "minimum_required": 3}` and aborts gracefully

## Epic 4: Advanced Reporting & Social Marketplace
Hoàn thiện báo cáo PDF và hệ sinh thái chia sẻ chiến lược.

### Story 4.1: Interactive Multi-Chart Visualization [STATUS: PENDING - Frontend Only]
As a Trader (Alex),
I want to see an interactive Equity Curve and Candlestick chart with trade markers in Nowing,
So that I can visually inspect where my strategy bought and sold.

**Acceptance Criteria:**
**Given** a successful backtest run
**When** Nowing receives the `price_series` and `trade_markers`
**Then** it returns a specific JSON payload structured for the ECharts UI component (including datasets for candlesticks, equity curve line, and scatter points for markers)
**And** Nowing renders an interactive ECharts dashboard
**And** users can hover over markers to see trade details (Price, PnL, Date)

**Error Path:**
**Given** the backtest run has zero trades (strategy never triggered)
**When** the chart payload is requested
**Then** it returns a valid `ChartPayload` with an empty `trade_markers` array and a populated `equity_curve` (flat line at initial capital), without crashing the chart renderer

### Story 4.2: "Verified Data" PDF Report Generation [STATUS: PENDING - Frontend Only]
As a Professional Investor,
I want to export a comprehensive PDF report of my backtest with a "Verified Data" trust badge,
So that I can share my results with partners knowing the data has been cross-checked.

**Acceptance Criteria:**
**Given** a completed run in Vibe-Trading
**When** I click "Export PDF"
**Then** the system generates a multi-page PDF including stats, equity curve, and the "Verified" watermark
**And** it performs a data checksum validation before signing the report

**Error Path:**
**Given** the checksum validation fails (data tampered or corrupted after job completion)
**When** PDF export is attempted
**Then** the system aborts PDF generation and returns `{"error": "checksum_mismatch"}` — no unsigned PDF is produced or served

### Story 4.3: Strategy Marketplace: Publish & Discovery [STATUS: PENDING - Frontend Only]
As a Strategy Creator,
I want to publish my successful backtest results to the Nowing Marketplace,
So that other users can discover, follow, or (optionally) subscribe to my strategy.

**Acceptance Criteria:**

**Publish Flow:**
**Given** a private strategy with high performance
**When** I select "Publish to Marketplace"
**Then** Vibe-Trading creates an immutable `snapshot_id` + signed metrics digest (per architecture §8.2)
**And** the strategy and its verified metrics are added to the public discovery feed
**And** the `executable_code` field is NEVER exposed in marketplace responses (subscribers receive signal outputs only)

**Discovery:**
**Given** the marketplace discovery feed
**When** a user searches or browses
**Then** they can filter strategies by Sharpe ratio, Win rate, asset class, and timeframe
**And** results are paginated (default 20 per page)

**DB Schema (inline migration):**
**Given** this story is first deployed
**When** the migration runs
**Then** a `marketplace_snapshots` table is created with columns `(snapshot_id, job_id, author_id, tags, price, visibility, created_at, revoked)`
**And** the migration is idempotent (safe to re-run)

**Moderation & Takedown:**
**Given** an Admin triggers a takedown for a published strategy
**When** `PATCH /api/v1/marketplace/snapshot/{snapshot_id}` is called with `{revoked: true}`
**Then** the strategy is removed from the discovery feed immediately
**And** `GET /api/v1/verify/{job_id}` returns `410 Gone` for the associated report

**Error Path:**
**Given** a user attempts to publish a strategy they do not own
**When** the publish request is submitted
**Then** the system returns `403 Forbidden` and does not create a snapshot

## Epic 5: Premium User Experience & Enterprise Stability
Đảm bảo trải nghiệm người dùng mượt mà, phân quyền ưu tiên cho người dùng Premium và bảo vệ tính ổn định của toàn bộ nền tảng giao dịch.

### Story 5.1: Tiered Priority Queue for Premium Users
As a Business Owner (Victor),
I want to implement a priority-based task queue where Premium users jump to the front of the line,
So that I can monetize the platform effectively and provide better service to paying customers.

**Acceptance Criteria:**
**Given** multiple backtest jobs in the Redis queue
**When** a job from a Premium user is submitted
**Then** it is placed in a high-priority queue and processed before standard jobs
**And** the system maintains a maximum wait time of < 5s for these users

**Fairness Safeguard:**
**Given** a burst of Premium jobs fills the premium queue
**When** 10 consecutive premium jobs have been processed
**Then** the worker yields to the standard queue for at least 1 job before resuming premium (token-bucket 10:1 ratio per architecture §9.1)

**Error Path:**
**Given** the `user_tier` claim in the JWT is missing or invalid
**When** the job is submitted
**Then** it is routed to the standard queue (fail-safe default) and a warning is logged — the job is NOT rejected

### Story 5.2: Admin Monitoring Dashboard [STATUS: PENDING - Frontend Only]
As a System Admin (Minh),
I want a real-time dashboard to monitor API latency, cache hit rates, and worker health,
So that I can proactively identify and resolve performance bottlenecks.

**Acceptance Criteria:**
**Given** the Nowing Admin panel
**When** I navigate to the "Infrastructure" tab
**Then** I see live metrics for Vibe-Trading: `avg_latency`, `cache_hit_rate`, and `active_workers`
**And** the system sends an alert if the error rate exceeds 5%

**Access Control:**
**Given** a request to `GET /api/v1/admin/stats`
**When** the request does not include a valid `VT_ADMIN_KEY` header
**Then** the endpoint returns `401 Unauthorized` (separate from the standard `API_AUTH_KEY`)

**Error Path:**
**Given** the metrics collection pipeline is temporarily unavailable
**When** the Admin dashboard polls for stats
**Then** it displays the last known values with a "stale data" indicator and timestamp, rather than showing empty or crashing

### Story 5.3: Automated Cleanup & Scaling Policy
As a Premium User,
I want the execution platform to automatically scale up its processing power during high traffic,
So that my complex backtests and Monte Carlo simulations always complete within the SLA timeframe regardless of system load.

**Acceptance Criteria:**
**Given** a disk usage threshold of 80% or artifacts older than 7 days
**When** the cleanup cron job runs
**Then** it deletes old files from the shared `/runs/` directory
**And** additional Celery worker containers are spun up automatically when the queue length > 10

**Error Path:**
**Given** a file deletion fails mid-cleanup (e.g., permission error or NFS timeout)
**When** the cron job encounters the error
**Then** it logs the failed path and continues cleaning remaining files — partial cleanup is acceptable; the job does NOT abort entirely

## Epic 6: Generative Strategy Copilot (Phase 2)
Tự động tạo mã thực thi chiến lược giao dịch từ yêu cầu ngôn ngữ tự nhiên.

### Story 6.1: Generative Strategy Copilot (P2)
As a Quantitative Analyst,
I want Nowing to auto-generate Python/PineScript execution code based on my natural language description,
So that Vibe-Trading can run custom, complex logic directly without me writing the code.

**Acceptance Criteria:**

**Happy Path:**
**Given** a natural language rule ("Buy when RSI < 30 and MACD crosses over")
**When** Nowing processes the intent
**Then** it generates valid execution code (e.g., Python `def next(self):`)
**And** populates the `executable_code` field in the payload
**And** Vibe-Trading correctly compiles/executes this code safely in the sandbox (per architecture §10)

**Static Analysis Gate:**
**Given** generated code contains forbidden imports (`socket`, `subprocess`, `ctypes`, `os.system`)
**When** the static analysis step (`ruff` + custom linter) runs
**Then** the code is rejected with `{status: "rejected", reasons: ["forbidden_import: subprocess"]}`
**And** the backtest job is NOT enqueued

**Dry-Run Gate:**
**Given** generated code passes static analysis
**When** the dry-run (5-trade replay) executes
**Then** if any exception is raised, the job is rejected with `{status: "rejected", reasons: ["dry_run_exception: <error>"]}`

**Sandbox Breach:**
**Given** code attempts to exceed resource limits (CPU > 1 vCPU, RAM > 512 MB, wall-clock > 60s)
**When** the watchdog sidecar detects the breach
**Then** the container is killed, a `vt.security.sandbox_violation` event is logged to the Admin dashboard (FR14)
**And** the SHA-256 hash of the offending `executable_code` is added to the deny-list (subsequent identical submissions are rejected immediately)

**Syntax Error from LLM:**
**Given** the LLM generates syntactically invalid Python/PineScript
**When** compilation is attempted
**Then** the system returns `{status: "rejected", reasons: ["syntax_error: <line>:<col> <message>"]}` to Nowing
**And** Nowing surfaces a user-friendly message prompting to rephrase the request

**Error Path:**
**Given** the Copilot LLM service is unavailable
**When** code generation is requested
**Then** the system returns a graceful error ("Code generation temporarily unavailable") without enqueuing a broken job
