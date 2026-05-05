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

## 2. Redis/Celery Implementation

**Architecture Details:**
- **Broker & State Backend:** Redis is used for high-throughput, reliable task queueing. It ensures jobs are not lost if an execution worker crashes mid-task.
- **Workers:** Auto-scaling Celery workers picking up asynchronous jobs.
- **Task Types:** Separated into queues (e.g., `backtest`, `rl_optimization`, `knowledge_graph_sync`).

**Scalability & Reliability (NFRs):**
- **Auto-scaling:** Workers scale automatically when the Redis queue length exceeds 10 jobs.
- **Latency:** Ensures the main API latency stays < 500ms, as the API only queues the job and returns a `job_id`. Backtests process asynchronously in < 30s.

## 3. Knowledge Graph & RL Worker Isolation

**Proactive Knowledge Graph (News-to-Asset Correlation) (FR4):**
- **Data Sync:** Independent background Celery beat tasks crawl financial news and update the internal Knowledge Graph.
- **Integration:** Exposes an API endpoint `GET /api/v1/kg/suggestions` for Nowing to query proactively when users ask open-ended questions.

**Offline Reinforcement Learning (Strategy Tuning) (FR3):**
- **Worker Isolation:** RL tasks are extremely compute-intensive. They are routed to a dedicated `vibe-trading-rl-worker` queue.
- **Resource Quotas:** The RL workers are deployed in strictly isolated Docker containers (cgroups enforced limits) to prevent them from starving the core Backtest workers of CPU/RAM.

## 4. Fulfillment of PRD Requirements

**Functional Requirements:**
- **FR1 (NLP to Params):** Nowing delegates parsing; Vibe-Trading receives strict JSON payloads via internal API.
- **FR2 (Preview Card):** Vibe-Trading provides a low-latency synchronous `/preview` endpoint.
- **FR3 (RL Optimization):** Handled via isolated RL Celery workers.
- **FR4 (Knowledge Graph):** Maintained asynchronously, accessible via internal query APIs.
- **FR5 (PDF Reports):** Vibe-Trading generates PDF using `weasyprint` and saves to EFS; Nowing serves the file URL.

**Domain & Non-Functional Requirements:**
- **Precision:** All PnL calculations use `Decimal` (6 decimal places) in Python, avoiding float drift.
- **Security:** Internal IP Whitelisting (Vibe-Trading only accepts traffic from Nowing). Strategies are encrypted (AES-256) at rest.
- **Caching:** L1 (Redis) & L2 (DuckDB/Parquet) implemented to ensure >70% cache hits and reduce external API calls.
- **Data Resilience:** Automated fallbacks programmed in the data loaders (`yfinance` -> `akshare` -> `ccxt`).
- **Retention:** Cron jobs automatically prune the `runs/` artifacts after 7 days or when disk usage hits 80%.
