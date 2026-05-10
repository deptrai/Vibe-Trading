# Story 1.3: Strategy Preview API

## 1. Story Foundation
**User Story:** 
As a Frontend Developer,
I want a lightweight API endpoint to generate preview data for the Strategy Card,
So that I can show the user what the AI understood before running a heavy backtest.

**Acceptance Criteria:**
* **Given** extracted parameters from Story 1.2
* **When** Nowing calls the `/preview` endpoint
* **Then** Vibe-Trading returns a summary of the strategy and a "Confidence Score"
* **And** the latency for this response is < 500ms

**Business Value:**
Provides immediate visual feedback to the user, confirming that the AI has correctly interpreted their natural language prompt before initiating a computationally expensive backtest. This is crucial for the "Zero-Technical Friction" differentiator.

## 2. Developer Context
**Current State & Motivation:**
Nowing parses natural language into a strict JSON payload. We need a fast API on the Vibe-Trading execution engine side to receive this payload and return a "Strategy Preview Card" summary, including a confidence score, so Nowing can display it to the user.

**Specific Modifications Required:**
* Create a new lightweight, synchronous REST API endpoint (`/preview`) in the Vibe-Trading backend (likely FastAPI/Python or similar based on existing architecture, though architecture mentions FastAPI for APIs).
* This endpoint must accept the `VibeTradingJobPayload` schema (or a subset of it).
* The endpoint logic needs to analyze the input and calculate/return a "Confidence Score" (e.g., indicating how fully the parameters were resolved) alongside a summary of the strategy to be executed.
* The endpoint must be optimized to return within 500ms.

**What Must Be Preserved:**
* Existing authentication and security middleware (IP Whitelisting, AES-256 for storage if applicable here, TLS/SSL) must apply to this new endpoint.

## 3. Technical Requirements

### Architecture Compliance
* **Integration Pattern:** Adhere to the "Microservice Specialist Worker" pattern. Nowing calls this API synchronously; it does *not* enqueue a job for Celery.
* **Payload Schema:** The input must conform to the `VibeTradingJobPayload` structure discussed in the Architecture document (Simulation Environment, Risk Management, Context Rules).
* **API Pattern:** Must be a synchronous, low-latency REST endpoint.

### Library & Framework Requirements
* Use the existing web framework established for Vibe-Trading APIs (e.g., FastAPI, Flask, Express - check existing codebase).
* Response parsing/validation should utilize the standard schema validation library (e.g., Pydantic if Python/FastAPI, Zod if TypeScript).

### File Structure Requirements
* Place the new route handler in the appropriate API routes directory.
* Place the confidence scoring logic in an appropriate service or utility module.

### Testing Requirements
* Unit tests for the confidence scoring logic.
* Integration/API tests for the `/preview` endpoint verifying successful responses (200 OK) with valid payloads.
* Tests verifying the < 500ms latency requirement (performance tests).
* Tests verifying authentication/authorization (401 Unauthorized for invalid keys/IPs).

## 4. Project Context Reference
* [PRD](../planning-artifacts/prd.md) - Section: Functional Requirements (FR2), Success Criteria.
* [Architecture](../planning-artifacts/architecture.md) - Section 1: Technical Components & Data Flow, Section 5: Fulfillment of PRD Requirements.
* [Epics](../planning-artifacts/epics.md) - Epic 1, Story 1.3.

## 5. Story Completion Status
**Status:** ready-for-dev
**Note:** Ultimate context engine analysis completed - comprehensive developer guide created.
