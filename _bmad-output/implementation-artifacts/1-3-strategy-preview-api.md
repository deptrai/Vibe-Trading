---
story_id: '1.3'
story_key: '1-3-strategy-preview-api'
epic_num: 1
story_num: 3
title: 'Strategy Preview API'
status: 'in-progress'
---

# Story 1.3: Strategy Preview API

## User Story
**As a** Frontend Developer,
**I want** a lightweight API endpoint to generate preview data for the Strategy Card,
**So that** I can show the user what the AI understood before running a heavy backtest.

## Acceptance Criteria
1. **Given** extracted parameters from Story 1.2
   **When** Nowing calls the `/preview` endpoint with a valid `VibeTradingJobPayload`
   **Then** Vibe-Trading returns a `PreviewResponse` containing a summary of the strategy and a "Confidence Score".
2. **Given** the preview request
   **When** processing the payload
   **Then** the response latency must be < 500ms.
3. **Given** a confidence threshold
   **When** the confidence score is below 0.9
   **Then** Nowing will use this data to display the Strategy Preview Card for user confirmation.

## Tasks / Subtasks

- [ ] Task 1: Implement the `/preview` endpoint (AC: 1, 2)
  - [ ] Subtask 1.1: Define `PreviewResponse` Pydantic model in `agent/src/api_models.py`.
  - [ ] Subtask 1.2: Add a `POST /preview` route in `agent/api_server.py`.
  - [ ] Subtask 1.3: Implement logic to generate a human-readable summary from the `VibeTradingJobPayload`.
- [ ] Task 2: Implement confidence score logic (AC: 1, 3)
  - [ ] Subtask 2.1: Implement a placeholder logic to calculate/return a `confidence_score`.
  - [ ] Subtask 2.2: Ensure the endpoint uses the `require_auth` dependency.
- [ ] Task 3: Testing and Validation (AC: 1, 2)
  - [ ] Subtask 3.1: Write integration tests in `agent/tests/test_strategy_preview.py`.
  - [ ] Subtask 3.2: Verify response time is consistently under 500ms.

## Dev Notes

### 🔬 Exhaustive Analysis & Guardrails

- **Performance:** This is a synchronous, high-priority endpoint. Avoid any heavy computations or external API calls during preview generation.
- **Validation:** Reuse the `VibeTradingJobPayload` defined in Story 1.2.
- **Summary Logic:** The summary should be concise but descriptive enough for a "Strategy Card" (e.g., "Long RSI Strategy on BTC-USDT (1h)").

### Project Structure Notes
- Endpoint should be added to `agent/api_server.py`.
- Models should stay in `agent/src/api_models.py`.

### References
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.3: Strategy Preview API]
- [Source: _bmad-output/planning-artifacts/architecture.md#1. Technical Components & Data Flow]

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
- [x] [Review][Patch] Explicit Percentage Formatting & Empty Assets Fallback [agent/api_server.py:1193]
- [x] [Review][Patch] Missing Auth Headers in Test Request [agent/tests/test_strategy_preview.py]
- [x] [Review][Patch] Missing Response Latency Verification Test [agent/tests/test_strategy_preview.py]
- [x] [Review][Patch] Inadequate Strategy Summary Generation [agent/api_server.py:1195]
