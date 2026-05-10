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
- **Symbol Normalization**: Nowing chịu trách nhiệm chuẩn hóa mã tài sản trước khi gọi Vibe-Trading.
- **Hybrid State Model**: Nowing giữ Source of Truth; Vibe-Trading giữ Execution Cache.
- **Data Resilience**: Tích hợp cơ chế fallback tự động ưu tiên Crypto: ccxt -> RPC nodes (Phase 1), yfinance/akshare (Phase 2).

### UX Design Requirements

(No separate UX document found. Functional requirements FR2 and User Journeys provide core visual/interaction scope.)

### FR Coverage Map

FR1: Epic 1 - Bóc tách tham số NLP & Payload Schema
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
FR15: Epic 2 - Monte Carlo Stress Test
FR16: Epic 6 - Generative Strategy Copilot
FR17: Epic 2 - DeFi-Native Simulator
FR18: Epic 2 - Perpetual Futures Engine
FR19: Epic 3 - Walk-Forward Analysis

## Epic List

### Epic 1: Intelligent Trading Assistant & Secure Order Transmission
Thiết lập kết nối bảo mật và bóc tách lệnh từ ngôn ngữ tự nhiên, bảo vệ chiến lược của người dùng.
**FRs covered:** FR1, FR2.

### Epic 2: Crypto-Native Async Execution Engine (Phase 1)
Xây dựng hệ thống hàng đợi Redis/Celery cho backtest chuyên biệt Crypto (Mở rộng đa thị trường ở Phase 2).
**FRs covered:** FR4, FR6, FR15, FR17, FR18.

### Epic 3: AI-Driven Strategy Evolution (RL & Graph)
Tối ưu hóa tham số qua RL và kết nối tri thức qua Knowledge Graph.
**FRs covered:** FR3, FR7, FR8, FR9, FR19.

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

### Story 1.3: Strategy Preview API
As a Frontend Developer,
I want a lightweight API endpoint to generate preview data for the Strategy Card,
So that I can show the user what the AI understood before running a heavy backtest.

**Acceptance Criteria:**
**Given** extracted parameters from Story 1.2
**When** Nowing calls the `/preview` endpoint
**Then** Vibe-Trading returns a summary of the strategy and a "Confidence Score"
**And** the latency for this response is < 500ms

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

### Story 2.4: Monte Carlo Stress Test
As a Risk-Averse Trader,
I want the engine to run Monte Carlo simulations (resampling) on my backtest results,
So that I can see the probability of "Black Swan" events and extreme drawdowns.

**Acceptance Criteria:**
**Given** a successfully completed backtest job with `enable_monte_carlo_stress_test=true`
**When** the worker processes the flag
**Then** it runs 10,000+ resampled paths on the historical trade series
**And** it outputs a risk distribution graph and 95% Confidence Interval metrics

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

### Story 2.6: Perpetual Futures & Liquidation Engine
As a Derivatives Trader,
I want the backtest engine to simulate Perpetual Futures mechanics including Funding Rates and Margin Liquidations,
So that I can accurately backtest high-leverage strategies.

**Acceptance Criteria:**
**Given** a backtest job trading Perpetual Futures with leverage > 1x
**When** the simulation executes
**Then** it deducts/adds Funding Rate payments based on simulated 8-hour intervals
**And** it accurately triggers liquidation if the margin ratio drops below the maintenance threshold

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

### Story 3.4: Walk-Forward Analysis (WFA)
As a Quant Analyst,
I want the system to perform Walk-Forward Analysis during strategy optimization,
So that I can ensure my strategy works on unseen data and isn't overfitted to the past.

**Acceptance Criteria:**
**Given** a request to optimize a strategy via RL
**When** the optimization job runs
**Then** it splits the historical data into rolling In-sample (train) and Out-of-sample (test) windows
**And** it compares performance between the two sets and reports the "Out-of-sample decay rate"

## Epic 4: Advanced Reporting & Social Marketplace
Hoàn thiện báo cáo PDF và hệ sinh thái chia sẻ chiến lược.

### Story 4.1: Interactive Multi-Chart Visualization
As a Trader (Alex),
I want to see an interactive Equity Curve and Candlestick chart with trade markers in Nowing,
So that I can visually inspect where my strategy bought and sold.

**Acceptance Criteria:**
**Given** a successful backtest run
**When** Nowing receives the `price_series` and `trade_markers`
**Then** it returns a specific JSON payload structured for the ECharts UI component (including datasets for candlesticks, equity curve line, and scatter points for markers)
**And** Nowing renders an interactive ECharts dashboard
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
As a Premium User,
I want the execution platform to automatically scale up its processing power during high traffic,
So that my complex backtests and Monte Carlo simulations always complete within the SLA timeframe regardless of system load.

**Acceptance Criteria:**
**Given** a disk usage threshold of 80% or artifacts older than 7 days
**When** the cleanup cron job runs
**Then** it deletes old files from the shared `/runs/` directory
**And** additional Celery worker containers are spun up automatically when the queue length > 10

## Epic 6: Generative Strategy Copilot (Phase 2)
Tự động tạo mã thực thi chiến lược giao dịch từ yêu cầu ngôn ngữ tự nhiên.

### Story 6.1: Generative Strategy Copilot (P2)
As a Quantitative Analyst,
I want Nowing to auto-generate Python/PineScript execution code based on my natural language description,
So that Vibe-Trading can run custom, complex logic directly without me writing the code.

**Acceptance Criteria:**
**Given** a natural language rule ("Buy when RSI < 30 and MACD crosses over")
**When** Nowing processes the intent
**Then** it generates valid execution code (e.g., Python `def next(self):`)
**And** populates the `executable_code` field in the payload
**And** Vibe-Trading correctly compiles/executes this code safely in the sandbox
