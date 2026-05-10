---
story_id: '1.2'
story_key: '1-2-standardized-payload-schema-natural-language-parameter-extraction'
epic_num: 1
story_num: 2
title: 'Standardized Payload Schema & Natural Language Parameter Extraction'
status: 'done'
---

# Story 1.2: Standardized Payload Schema & Natural Language Parameter Extraction

## User Story
**As a** Trader (Alex),
**I want** my trading parameters (Symbol, RSI, Timeframe) to be accurately extracted and formatted into a strict `VibeTradingJobPayload`,
**So that** I don't have to manually fill out forms and the execution engine receives reliable, standardized data.

## Acceptance Criteria
1. **Given** the system needs to define an execution contract
   **When** Nowing dispatches a job to Vibe-Trading
   **Then** Vibe-Trading must validate the incoming payload against a strict `VibeTradingJobPayload` Pydantic v2 schema.
2. **Given** the schema definition
   **When** defining the `VibeTradingJobPayload`
   **Then** it must include nested models for:
   - `SimulationEnvironment` (exchange, instrument_type, initial_capital, trading_fees, slippage_tolerance, historical_range, gas_fee_model, track_impermanent_loss)
   - `RiskManagement` (max_drawdown_percentage, stop_loss, take_profit, position_sizing, leverage)
   - `ContextRules` (assets, timeframe, indicators, natural_language_rules, executable_code)
   - `ExecutionFlags` (enable_monte_carlo_stress_test, enable_rl_optimization, wfa_config)
3. **Given** Nowing's role as Orchestrator
   **When** defining this schema
   **Then** default values and validators must be strictly implemented to handle missing or optional parameters gracefully.

## Tasks / Subtasks

- [ ] Task 1: Define the `VibeTradingJobPayload` schema (AC: 1, 2)
  - [ ] Subtask 1.1: Create nested Pydantic v2 models (`SimulationEnvironment`, `RiskManagement`, `ContextRules`, `ExecutionFlags`).
  - [ ] Subtask 1.2: Assemble `VibeTradingJobPayload` using the nested models.
  - [ ] Subtask 1.3: Apply strict type hints, validations (e.g. constraints on leverage or drawdown), and sensible defaults.
- [ ] Task 2: Integrate schema into Vibe-Trading API (AC: 1, 3)
  - [ ] Subtask 2.1: Expose the schema in a relevant API endpoint (e.g. a placeholder `/jobs` or `/preview` route) to enforce validation of incoming requests.
  - [ ] Subtask 2.2: Write unit tests to verify that valid JSON payloads parse correctly and invalid payloads trigger Pydantic validation errors.

## Dev Notes

### 🔬 Exhaustive Analysis & Guardrails

- **Architecture Constraints:**
  - *Microservice Specialist Worker Pattern:* Nowing acts as the orchestrator and is strictly responsible for parsing NLP intent into this JSON payload. Vibe-Trading is the execution engine and its primary responsibility here is **defining the strict API contract** (the schema) and validating incoming data.
  - Do not implement the NLP text-parsing logic within Vibe-Trading for this story; focus on the schema definition that Nowing will target.
- **Framework Rules:** 
  - Use **Pydantic v2** (`BaseModel`, `Field`, `model_validator`).
  - Enforce Python 3.11+ type hinting (e.g., `from __future__ import annotations`).
  - Keep types precise (e.g., use `Decimal` for financial values to prevent floating-point drift, use `Enum` for instrument types like SPOT/PERPETUAL).
- **Previous Learnings (Story 1.1):**
  - Security boundaries are in place (IP Whitelisting & API Key). This schema will be the core data structure passing through that secure bridge.

### Project Structure Notes
- **Suggested Location:** Create or update a models file, such as `agent/src/api_models.py` or inside `agent/api_server.py` depending on existing patterns. (Currently `agent/api_server.py` has API models, but a dedicated file like `agent/src/models.py` or `agent/src/swarm/api_models.py` might be better for complex nested schemas).

### References
- [Source: _bmad-output/planning-artifacts/architecture.md#2. Standardized Payload Schema (The Contract)]
- [Source: _bmad-output/project-context.md#Language-Specific Rules]

## Dev Agent Record

### Agent Model Used
(To be filled by dev agent)

### Debug Log References
(To be filled by dev agent)

### Completion Notes List
(To be filled by dev agent)

### File List
(To be filled by dev agent)

### Change Log
(To be filled by dev agent)

---
**Status:** done

### Review Findings
- [x] [Review][Patch] WFA Config Schema — `wfa_config` is an unconstrained dict, which poses risks. Define a strict schema now or defer?
- [x] [Review][Patch] Leverage on SPOT — Should we add a validator to reject leverage > 1.0 when instrument_type is SPOT?
- [x] [Review][Patch] Backtest Duration Limit — `historical_range` is capped at 1095 days (3 years). Increase the limit or keep as is?
- [x] [Review][Patch] Missing `uuid` Import [agent/api_server.py:1187]
- [x] [Review][Patch] Fragile/Inconsistent Module Imports [agent/api_server.py, agent/tests/test_payload_validation.py]
- [x] [Review][Patch] False Positive & Extraneous Fields in Tests [agent/tests/test_payload_validation.py]
- [x] [Review][Patch] Float/Int Defaults for Decimal Fields [agent/src/api_models.py]
- [x] [Review][Patch] Zero Initial Capital Permits Invalid States [agent/src/api_models.py:14]
- [x] [Review][Patch] Unbounded `stop_loss` and `take_profit` Values [agent/src/api_models.py:23-24]
- [x] [Review][Patch] Empty Assets List Allowed [agent/src/api_models.py:29]
- [x] [Review][Patch] Unvalidated Timeframe Format [agent/src/api_models.py:30]
- [x] [Review][Patch] Unbounded Strings Pose memory DoS Risk [agent/src/api_models.py:32-33]
- [x] [Review][Patch] FastAPI Auth Dependency Blocks Test Client [agent/tests/test_payload_validation.py]
- [x] [Review][Patch] Field Name Mismatch (`historical_range_days` vs AC `historical_range`) [agent/src/api_models.py:17]
- [x] [Review][Patch] Missing Implementation of `model_validator` [agent/src/api_models.py]
- [x] [Review][Patch] Incomplete Dev Agent Record [story file]