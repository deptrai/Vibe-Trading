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

FR1: Bóc tách các tham số (Mã tài sản, Chỉ báo, Tham số, Khung thời gian) từ câu lệnh ngôn ngữ tự nhiên.
FR2: Hiển thị Strategy Preview Card để xác nhận thông số khi độ tự tin của AI dưới 0.9.
FR3: Tính năng "Optimize Strategy" tự động tìm bộ tham số tốt nhất qua Reinforcement Learning.
FR4: Tự động phát hiện sự kiện tin tức và đề xuất mã tài sản/chiến lược liên quan từ Knowledge Graph.
FR5: Xuất báo cáo PDF "Verified Data" (Shadow Account Report) và tính năng chia sẻ lên Marketplace.

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
- **Symbol Normalization**: Nowing chịu trách nhiệm chuẩn hóa mã tài sản trước khi gọi Vibe-Trading.
- **Hybrid State Model**: Nowing giữ Source of Truth; Vibe-Trading giữ Execution Cache.
- **Data Resilience**: Tích hợp cơ chế fallback tự động (yfinance -> akshare -> ccxt).

### UX Design Requirements

(No separate UX document found. Functional requirements FR2 and User Journeys provide core visual/interaction scope.)

### FR Coverage Map

FR1: Epic 1 - Bóc tách tham số NLP
FR2: Epic 1 - Strategy Preview Card
FR3: Epic 3 - Optimize Strategy RL
FR4: Epic 2 - Multi-market Backtest
FR5: Epic 4 - PDF/Marketplace
FR6: Epic 2 - 2-year Limit
FR7: Epic 3 - RL Optimization
FR8: Epic 3 - Knowledge Graph
FR9: Epic 3 - Explainable AI
FR10: Epic 4 - Interactive Charts
FR11: Epic 4 - Shadow PDF
FR12: Epic 4 - Marketplace Social
FR13: Epic 5 - Task Queue/Priority
FR14: Epic 5 - Admin Dashboard

## Epic List

### Epic 1: Internal Service Bridge & NLP Interface
Thiết lập kết nối bảo mật và bóc tách lệnh từ ngôn ngữ tự nhiên.
**FRs covered:** FR1, FR2.

### Epic 2: Multi-Market Async Execution Engine
Xây dựng hệ thống hàng đợi Redis/Celery cho backtest đa thị trường.
**FRs covered:** FR4, FR6.

### Epic 3: AI-Driven Strategy Evolution (RL & Graph)
Tối ưu hóa tham số qua RL và kết nối tri thức qua Knowledge Graph.
**FRs covered:** FR3, FR7, FR8, FR9.

### Epic 4: Advanced Reporting & Social Marketplace
Hoàn thiện báo cáo PDF và hệ sinh thái chia sẻ chiến lược.
**FRs covered:** FR5, FR10, FR11, FR12.

### Epic 5: Governance & Scaling Infrastructure
Quản trị Admin, Auto-scaling và Bảo mật nâng cao.
**FRs covered:** FR13, FR14.

## Epic 1: Internal Service Bridge & NLP Interface
Thiết lập kết nối bảo mật giữa Nowing và Vibe-Trading, đồng thời xây dựng khả năng bóc tách lệnh từ ngôn ngữ tự nhiên.

### Story 1.1: Secure Service-to-Service Bridge
As a System Admin,
I want to establish a secure connection between Nowing and Vibe-Trading using Bearer Token and IP Whitelisting,
So that only Nowing can access the execution engine.

**Acceptance Criteria:**
**Given** Vibe-Trading API server is running
**When** Nowing sends a request with the correct `API_AUTH_KEY` and from a whitelisted IP
**Then** Vibe-Trading returns a 200 OK response
**And** any request without a valid key or from an unknown IP returns 401 Unauthorized

### Story 1.2: Natural Language Parameter Extraction
As a Trader (Alex),
I want Nowing to extract trading parameters (Symbol, RSI, Timeframe) from my text prompt,
So that I don't have to manually fill out a form.

**Acceptance Criteria:**
**Given** a user prompt "Backtest RSI < 30 for BTC-USDT on 1H for 1 year"
**When** the NLP engine processes the text
**Then** it returns a JSON object with: `symbol: "BTC-USDT"`, `indicator: "RSI"`, `threshold: 30`, `timeframe: "1H"`, `period: "1y"`
**And** it handles basic variations in natural language

### Story 1.3: Strategy Preview API
As a Frontend Developer,
I want a lightweight API endpoint to generate preview data for the Strategy Card,
So that I can show the user what the AI understood before running a heavy backtest.

**Acceptance Criteria:**
**Given** extracted parameters from Story 1.2
**When** Nowing calls the `/preview` endpoint
**Then** Vibe-Trading returns a summary of the strategy and a "Confidence Score"
**And** the latency for this response is < 500ms

## Epic 2: Multi-Market Async Execution Engine
Xây dựng hệ thống hàng đợi Redis/Celery cho backtest đa thị trường.

### Story 2.1: Async Job Queue with Redis/Celery
As a System Architect,
I want to implement a Redis-backed Celery queue for executing backtest jobs asynchronously,
So that the main API server remains responsive while heavy computations run in the background.

**Acceptance Criteria:**
**Given** a backtest request from Nowing
**When** the API receives the request
**Then** it enqueues a job to Redis and returns a unique `job_id` immediately
**And** a background Celery worker picks up the job for execution

### Story 2.2: Multi-Market Data Loading System
As a Trader,
I want the system to automatically fetch data from yfinance (US), AKShare (VN), or CCXT (Crypto) based on the asset symbol,
So that I can backtest any strategy across different global markets.

**Acceptance Criteria:**
**Given** a valid symbol (e.g., "VNM", "AAPL", "BTC-USDT")
**When** the execution engine runs
**Then** it correctly routes the request to the appropriate data provider
**And** it handles API rate limits using the built-in retry mechanism

### Story 2.3: 2-Year Lookback Constraint & Results Persistence
As a DevOps Engineer,
I want the execution engine to enforce a maximum 2-year lookback period and save results to a shared volume,
So that I can control resource usage and ensure Nowing can retrieve the results later.

**Acceptance Criteria:**
**Given** a backtest request for "5 years" of data
**When** the job starts
**Then** it automatically truncates the period to the last 2 years
**And** the output (CSV/JSON/Plots) is saved to the shared `/runs/` directory for retrieval

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

### Story 3.2: Knowledge Graph Integration (News-to-Asset)
As a Long-term Investor,
I want Nowing to proactively suggest assets based on macro news using a Knowledge Graph,
So that I don't miss opportunities when significant global events occur.

**Acceptance Criteria:**
**Given** a news event "FED interest rate hike"
**When** the Knowledge Graph is queried
**Then** it returns a list of correlated assets (e.g., Gold, DXY, Tech Stocks) based on historical impact
**And** Nowing presents these as a "Proactive Insight" in the chat

### Story 3.3: Explainable AI (XAI) for Strategy Changes
As a Skeptical User,
I want the AI to explain the reasoning behind its suggested strategy modifications in natural language,
So that I can trust the AI and understand the "Why" before I trade.

**Acceptance Criteria:**
**Given** an optimized strategy from Story 3.1
**When** the user asks "Why these parameters?"
**Then** the Agent provides a clear explanation (e.g., "I reduced the timeframe because recent volatility suggests a shorter holding period is safer")
**And** it cites specific metrics (Sharpe improvement, Max Drawdown reduction)

## Epic 4: Advanced Reporting & Social Marketplace
Hoàn thiện báo cáo PDF và hệ sinh thái chia sẻ chiến lược.

### Story 4.1: Interactive Multi-Chart Visualization
As a Trader (Alex),
I want to see an interactive Equity Curve and Candlestick chart with trade markers in Nowing,
So that I can visually inspect where my strategy bought and sold.

**Acceptance Criteria:**
**Given** a successful backtest run
**When** Nowing receives the `price_series` and `trade_markers`
**Then** it renders an interactive ECharts dashboard
**And** users can hover over markers to see trade details (Price, PnL, Date)

### Story 4.2: "Verified Data" PDF Report Generation
As a Professional Investor,
I want to export a comprehensive PDF report of my backtest with a "Verified Data" trust badge,
So that I can share my results with partners knowing the data has been cross-checked.

**Acceptance Criteria:**
**Given** a completed run in Vibe-Trading
**When** I click "Export PDF"
**Then** the system generates a multi-page PDF including stats, equity curve, and the "Verified" watermark
**And** it performs a data checksum validation before signing the report

### Story 4.3: Strategy Marketplace: Publish & Discovery
As a Strategy Creator,
I want to publish my successful backtest results to the Nowing Marketplace,
So that other users can discover, follow, or (optionally) subscribe to my strategy.

**Acceptance Criteria:**
**Given** a private strategy with high performance
**When** I select "Publish to Marketplace"
**Then** the strategy and its verified metrics are added to the public discovery feed
**And** other users can search and filter strategies by Sharpe ratio or Win rate

## Epic 5: Governance & Scaling Infrastructure
Quản trị Admin, Auto-scaling và Bảo mật nâng cao.

### Story 5.1: Tiered Priority Queue for Premium Users
As a Business Owner (Victor),
I want to implement a priority-based task queue where Premium users jump to the front of the line,
So that I can monetize the platform effectively and provide better service to paying customers.

**Acceptance Criteria:**
**Given** multiple backtest jobs in the Redis queue
**When** a job from a Premium user is submitted
**Then** it is placed in a high-priority queue and processed before standard jobs
**And** the system maintains a maximum wait time of < 5s for these users

### Story 5.2: Admin Monitoring Dashboard
As a System Admin (Minh),
I want a real-time dashboard to monitor API latency, cache hit rates, and worker health,
So that I can proactively identify and resolve performance bottlenecks.

**Acceptance Criteria:**
**Given** the Nowing Admin panel
**When** I navigate to the "Infrastructure" tab
**Then** I see live metrics for Vibe-Trading: `avg_latency`, `cache_hit_rate`, and `active_workers`
**And** the system sends an alert if the error rate exceeds 5%

### Story 5.3: Automated Cleanup & Scaling Policy
As a DevOps Engineer,
I want the system to automatically prune old artifacts and scale worker instances based on queue length,
So that I can optimize infrastructure costs and prevent disk exhaustion.

**Acceptance Criteria:**
**Given** a disk usage threshold of 80% or artifacts older than 7 days
**When** the cleanup cron job runs
**Then** it deletes old files from the shared `/runs/` directory
**And** additional Celery worker containers are spun up automatically when the queue length > 10
