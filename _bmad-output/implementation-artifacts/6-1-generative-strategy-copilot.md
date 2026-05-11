---
story_id: "6.1"
story_key: "6-1-generative-strategy-copilot"
epic_id: "6"
title: "Generative Strategy Copilot (Hybrid Headless Execution)"
status: "ready-for-dev"
version: "1.0"
---

# User Story
**As a** Quantitative Analyst using the Headless API,
**I want** Vibe-Trading to automatically generate and execute trading code from my natural language rules,
**So that** I can receive real, verified backtest results (not mocks) through the job queue.

# Acceptance Criteria

### AC 1: Headless Code Generation
- **Given** a `VibeTradingJobPayload` containing `natural_language_rules` but NO `executable_code`.
- **When** the worker processes the job.
- **Then** it must invoke `AgentLoop` in a "One-shot Headless Mode" to translate the rules into a valid `strategy.py`.
- **And** it must handle LLM errors or empty code generation gracefully (return structured error).

### AC 2: Direct Execution (Bypass)
- **Given** a payload that ALREADY has `executable_code`.
- **When** the worker processes the job.
- **Then** it must bypass the LLM step and directly save the code to the run directory for execution.

### AC 3: Real Engine Execution
- **Given** the generated (or provided) strategy code.
- **When** the execution starts.
- **Then** it must use `src.core.runner.Runner` to execute the code against real market data (loaded via ccxt).
- **And** it must produce standard artifacts in the `artifacts/` folder: `equity.csv`, `metrics.csv`, `trades.csv`.

### AC 4: Simulator Integration (Enrichment)
- **Given** the actual trade returns from the engine.
- **When** enrichment is triggered.
- **Then** it must pass these returns through `PerpetualSimulator` (for funding/liquidation) and `DeFiSimulator` (for gas/IL) if applicable.
- **And** it must run the `MonteCarloSimulator` (10,000 iterations) on the ACTUAL trade series.

### AC 5: Standardized Run State
- **Given** the job completes.
- **When** the API queries `GET /runs/{id}`.
- **Then** it must return a valid `state.json` with status `success`, including real performance metrics and file paths.

# Developer Context & Guardrails

## 🏗️ Architecture Compliance
- **Microcompact Guard:** MUST NOT bypass the 5-layer context management in `AgentLoop` if using LLM.
- **Runs Directory Structure:** Every job must have a clean structure:
  ```
  runs/{job_id}/
  ├── code/
  │   └── strategy.py
  ├── artifacts/
  │   ├── equity.csv
  │   ├── metrics.csv
  │   └── trades.csv
  ├── logs/
  │   └── runner_stdout.txt
  └── state.json
  ```
- **Concurrency:** Ensure `ThreadPoolExecutor` (max 4) is respected to prevent OOM.

## 📂 Files to Modify
- `agent/src/worker.py`: Primary target. Replace random/mock logic with the Hybrid flow.
- `agent/src/agent/loop.py`: Verify if a `run_headless` method exists or needs to be exposed.
- `agent/src/api_models.py`: Ensure `VibeTradingJobPayload` correctly handles both `natural_language_rules` and `executable_code`.

## ⚠️ Critical Avoidance (Anti-patterns)
- **DO NOT** use `np.random.choice` for simulated returns anymore.
- **DO NOT** hardcode paths. Use the environment variable `RUNS_DIR` or the default from `worker.py`.
- **DO NOT** return success if the `Runner` fails (exit code != 0). Capture `stderr` into the job result.

## 🧪 Testing Requirements
- **Integration Test:** Create `agent/tests/test_headless_e2e.py`.
- **Scenario 1:** Submit NL rules -> Verify code is generated -> Verify metrics are non-zero.
- **Scenario 2:** Submit direct code -> Verify LLM is skipped -> Verify output artifacts exist.

# Project Context Reference
- **Technology:** Python 3.11, FastAPI, Celery, CCXT.
- **Precision:** Use `Decimal` for all financial logic (Simulators).
- **Security:** Ensure sandboxed execution for `executable_code` (no `os.system`, etc.).

# Status
- **Ready for Dev:** Yes
- **Context Analysis:** Complete (Winston approved)
