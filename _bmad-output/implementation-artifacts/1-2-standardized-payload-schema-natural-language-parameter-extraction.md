---
story_id: '1.2'
story_key: '1-2-standardized-payload-schema-natural-language-parameter-extraction'
epic_num: 1
story_num: 2
title: 'Standardized Payload Schema & Natural Language Parameter Extraction'
status: 'ready-for-dev'
---

# Story 1.2: Standardized Payload Schema & Natural Language Parameter Extraction

## User Story
**As a** Trader (Alex),
**I want** Nowing to extract trading parameters (Symbol, RSI, Timeframe) from my text prompt or uploaded documents,
**So that** I don't have to manually fill out a form, and the data is formatted into a strict `VibeTradingJobPayload`.

## Acceptance Criteria
- **Given** a user prompt or uploaded strategy document
- **When** the Nowing NLP engine processes the text
- **Then** it returns a validated JSON object conforming to `VibeTradingJobPayload` (SimulationEnvironment, RiskManagement, ContextRules)
- **And** it gracefully handles missing parameters by assigning defaults or asking for clarification

## Dev Notes

### 🔬 Exhaustive Analysis & Guardrails

#### Current State
- The `agent` is currently using LangGraph and LangChain orchestration to handle user chat operations (per `project-context.md`).
- We have an existing schema approach (e.g. `BacktestConfigSchema`) using Pydantic, but we need the unified `VibeTradingJobPayload` structure that Nowing will construct and Vibe-Trading will execute against.

#### Technical Requirements
- **NLP Parameter Extraction:** Implement a tool or LangChain Chain that takes user text and uses the LLM to populate the schema.
- **Pydantic v2 Schema (`VibeTradingJobPayload`):** Create the primary contract schema exactly as architected:
  - `SimulationEnvironment`: `exchange`, `instrument_type` (SPOT/PERPETUAL), `initial_capital`, `trading_fees`, `slippage_tolerance`, `historical_range`, `gas_fee_model`, `track_impermanent_loss`.
  - `RiskManagement`: `max_drawdown_percentage`, `stop_loss`, `take_profit`, `position_sizing`, `leverage`.
  - `ContextRules`: `assets` (normalized list of strings), `timeframe`, `indicators`, `natural_language_rules`, `executable_code`.
  - `ExecutionFlags`: `enable_monte_carlo_stress_test`, `enable_rl_optimization`, `wfa_config`.
- **Defaulting/Fallback Logic:** The extraction mechanism must fill missing fields with sensible defaults (e.g., initial_capital = 10000, timeframe = '1d') OR explicitly mark them as `None` for the orchestration loop to request clarification from the user.

#### Architecture Compliance
- **Microservice Specialist Worker Pattern:** Nowing acts as the orchestrator to perform NLP extraction and symbol normalization. This means this extraction step happens _before_ a job is sent to Vibe-Trading.
- **Strict Pydantic Validation:** Absolutely required. Use `Field(description="...")` to help the LLM extract the fields accurately.

#### Library & Framework Requirements
- **LangChain/LangGraph:** Utilize structured output parsing (`with_structured_output(VibeTradingJobPayload)`).
- **Python:** Use `from __future__ import annotations`.

### 📂 Files to Modify

| File | Change Description |
|------|--------------------|
| `agent/src/core/schemas.py` | (Create or Update) Define the `VibeTradingJobPayload` and sub-schemas using Pydantic. |
| `agent/src/agent/tools/extractor.py` | (Create or Update) Create the LangChain structured extraction tool/chain to parse natural language into the schema. |

### 🧪 Testing Requirements
- **Unit Test:** Create a test with a mock natural language string ("Backtest AAPL on daily using RSI 14 and MACD with 5000 capital") and verify it correctly parses into the `VibeTradingJobPayload` with the correct assets `["AAPL"]`, `timeframe="1d"`, etc.
- **Validation Test:** Ensure validation fails if mutually exclusive or completely invalid parameters are provided (e.g., leverage=100 on SPOT).

### 📜 Project Context Reference
- **No Global State:** Do not use global state for request-scoped parsing.
- **Typing:** No `any` allowed. Complete type hints required.
- **Data Precision:** Use Decimal for PnL/Capital inputs where appropriate.

---

### Previous Story Learnings (from Story 1.1)
- The previous story set up secure internal bridging. Nowing will use the payload schema we build here to construct the request bodies that hit the endpoints protected by Story 1.1.

**Status:** ready-for-dev
**Note:** Ultimate context engine analysis completed - comprehensive developer guide created.
