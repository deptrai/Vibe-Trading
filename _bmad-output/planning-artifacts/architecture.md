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
- **FR1 (NLP to Schema):** Nowing delegates parsing; Vibe-Trading receives strict `VibeTradingJobPayload` via message queue.
- **FR2 (Preview Card):** Vibe-Trading provides a low-latency synchronous `/preview` endpoint.
- **FR3 (RL Optimization & Generative Strategy):** Handled via isolated RL/Execution Celery workers.
- **FR4 (Knowledge Graph):** Maintained asynchronously, accessible via internal query APIs.
- **FR5 (PDF Reports & Stress Tests):** Vibe-Trading generates metrics & Monte Carlo risk reports; saves to EFS.

**Domain & Non-Functional Requirements:**
- **Precision:** All PnL calculations use `Decimal` (6 decimal places) in Python, avoiding float drift.
- **Security:** Internal IP Whitelisting (Vibe-Trading only accepts traffic from Nowing). Strategies are encrypted (AES-256) at rest.
- **Caching:** L1 (Redis) & L2 (DuckDB/Parquet) implemented to ensure >70% cache hits and reduce external API calls.
- **Data Resilience:** Automated fallbacks programmed in the data loaders prioritizing Crypto (`ccxt` -> RPC nodes for Phase 1; `yfinance`/`akshare` deferred to Phase 2).
- **Retention:** Cron jobs automatically prune the `runs/` artifacts after 7 days or when disk usage hits 80%.
