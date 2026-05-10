---
story_id: '3.2'
story_key: '3-2-knowledge-graph-integration-news-to-asset'
epic_num: 3
story_num: 2
title: 'Knowledge Graph Integration (News-to-Asset)'
status: 'in-progress'
---

# Story 3.2: Knowledge Graph Integration (News-to-Asset)

## Epic 3: AI-Driven Strategy Evolution (RL & Graph)
Tối ưu hóa tham số qua RL và kết nối tri thức qua Knowledge Graph.

## User Story
**As a** Long-term Investor,
**I want** Nowing to proactively suggest assets based on crypto news using a Knowledge Graph,
**So that** I don't miss opportunities when significant on-chain or global events occur.

## Acceptance Criteria
1. [ ] **Phase 1 — Crypto-Native Events (in scope):**
   **Given** a crypto-specific news event (e.g., "ETH Shanghai upgrade", "BTC halving", "USDC depeg")
   **When** the Knowledge Graph is queried via `GET /api/v1/kg/suggestions`
   **Then** it returns a list of correlated crypto assets with confidence scores
   **And** Nowing can present these as a "Proactive Insight"
2. [ ] **Given** the KG background sync job runs
   **When** new crypto news is ingested
   **Then** the graph is updated within 5 minutes and `GET /api/v1/kg/suggestions` reflects the new correlations
3. [ ] **Given** the KG service is unavailable or returns empty results
   **When** Nowing queries for suggestions
   **Then** the system returns an empty suggestion list gracefully (no crash)
   **And** logs a warning without surfacing an error to the end user
4. [ ] **Phase 2 — Macro News Expansion (deferred):**
   This AC is explicitly gated behind `ENABLE_MACRO_KG=true` environment flag; default is disabled.
   Not implemented in this story — stub only.

---

## Developer Context

### Architecture Decision: In-Memory Graph + File Persistence (v1)
For Phase 1, use a **lightweight in-memory graph** stored as JSON, NOT a full graph database:
- **Why not Neo4j/ArangoDB:** Heavyweight dependency, requires separate service, overkill for < 1000 nodes
- **Why not NetworkX:** Good option but adds dependency; a simpler adjacency-list dict is sufficient for v1
- **Why JSON adjacency list:** Zero new dependencies, file-based persistence aligns with `runs/` pattern, easy to migrate to a real graph DB in Phase 2

### Graph Schema (Phase 1 — Crypto Only)

```
Node Types:
  - EVENT: { id, title, category, source, timestamp, summary }
  - ASSET: { id, symbol, name, chain? }

Edge Types:
  - IMPACTS: EVENT → ASSET { weight: 0.0-1.0, direction: "bullish"|"bearish"|"neutral", reason: str }
  - CORRELATED_WITH: ASSET → ASSET { weight: 0.0-1.0, category: str }
```

### Data Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ News Sources │────>│  KG Crawler  │────>│  KG Store    │
│ (CryptoNews) │     │ (Celery Task)│     │ (JSON File)  │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                           ┌──────▼───────┐
                                           │  KG Query    │
                                           │  API Endpoint│
                                           └──────────────┘
```

### Technical Requirements

#### 1. Knowledge Graph Store (`agent/src/kg_store.py`)
- In-memory adjacency list with thread-safe read/write
- Persistence to `kg_data/graph.json` (relative to agent dir)
- Auto-load on startup if file exists
- Methods:
  ```python
  class KnowledgeGraphStore:
      def add_event(self, event: KGEvent) -> None
      def add_asset(self, asset: KGAsset) -> None
      def add_impact(self, event_id: str, asset_id: str, weight: float, direction: str, reason: str) -> None
      def add_correlation(self, asset_a: str, asset_b: str, weight: float, category: str) -> None
      def get_suggestions(self, limit: int = 10, min_weight: float = 0.3) -> List[KGSuggestion]
      def get_asset_impacts(self, symbol: str) -> List[dict]
      def get_recent_events(self, hours: int = 24) -> List[KGEvent]
      def save(self) -> None
      def load(self) -> None
      def stats(self) -> dict
  ```

#### 2. KG Crawler / News Ingestion (`agent/src/kg_crawler.py`)
- **Phase 1 Data Source:** Use free crypto news APIs:
  - Primary: CryptoCompare News API (free tier, no key required for basic)
  - Fallback: CoinGecko `/news` endpoint (free)
  - If all APIs fail: Use a hardcoded seed dataset of major crypto events
- **NLP Entity Extraction:** Simple keyword/regex-based extraction (no LLM dependency):
  - Map known crypto symbols (BTC, ETH, SOL, etc.) from news text
  - Categorize events: "upgrade", "hack", "regulation", "listing", "halving", etc.
  - Assign impact weights based on category heuristics
- **Celery Task:** `sync_knowledge_graph` on `kg_sync` queue
  - Scheduled interval: every 5 minutes (configurable via `KG_SYNC_INTERVAL_MINUTES` env var)
  - Idempotent: skip events already in the graph (dedup by event ID/URL hash)

#### 3. Pydantic Models (`agent/src/kg_models.py`)
```python
class KGEvent(BaseModel):
    event_id: str
    title: str
    category: str  # "upgrade", "hack", "regulation", "listing", "halving", "depeg", "partnership"
    source: str
    url: Optional[str] = None
    timestamp: datetime
    summary: Optional[str] = None
    raw_categories: List[str] = Field(default_factory=list)

class KGAsset(BaseModel):
    asset_id: str  # e.g., "BTC", "ETH"
    symbol: str
    name: str
    chain: Optional[str] = None

class KGImpact(BaseModel):
    event_id: str
    asset_id: str
    weight: float = Field(..., ge=0.0, le=1.0)
    direction: str = Field(..., pattern=r"^(bullish|bearish|neutral)$")
    reason: str

class KGSuggestion(BaseModel):
    asset_symbol: str
    asset_name: str
    events: List[dict]  # [{event_title, weight, direction, reason, timestamp}]
    aggregate_score: float  # sum of weights, capped at 1.0
    suggested_action: str  # "monitor", "consider_long", "consider_short", "high_alert"

class KGSuggestionsResponse(BaseModel):
    suggestions: List[KGSuggestion]
    last_sync: Optional[datetime] = None
    total_events: int = 0
    total_assets: int = 0
```

#### 4. API Endpoints (in `api_server.py`)
- `GET /api/v1/kg/suggestions` — Main query endpoint
  - Query params: `limit` (default 10), `min_weight` (default 0.3)
  - Returns: `KGSuggestionsResponse`
  - Auth: `require_auth`
- `GET /api/v1/kg/events` — List recent events
  - Query params: `hours` (default 24, max 168)
  - Returns: List of events with linked assets
  - Auth: `require_auth`
- `GET /api/v1/kg/stats` — Graph statistics
  - Returns: node/edge counts, last sync time
  - Auth: `require_auth`
- `POST /api/v1/kg/sync` — Trigger manual sync
  - Auth: `require_auth`
  - Returns: `{status: "triggered", message: ...}`

#### 5. Celery Worker Configuration
- Add task route in `worker.py`:
  ```python
  "src.kg_crawler.sync_knowledge_graph": {"queue": "kg_sync"},
  ```
- Add `kg-worker` service in `docker-compose.yml`:
  ```yaml
  kg-worker:
    build: .
    command: celery -A src.worker worker -Q kg_sync -c 1 -B --schedule=/tmp/celerybeat-schedule
    env_file:
      - agent/.env
    environment:
      - REDIS_URL=redis://redis:6379/0
      - KG_SYNC_INTERVAL_MINUTES=5
    volumes:
      - vibe-runs:/app/agent/runs
      - kg-data:/app/agent/kg_data
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
    restart: unless-stopped
    depends_on:
      - redis
  ```
- The `-B` flag enables Celery Beat for periodic task scheduling

#### 6. Seed Data (Bootstrap)
- Include a hardcoded seed dataset in `agent/src/kg_seed_data.py`:
  - Top 20 crypto assets (BTC, ETH, SOL, BNB, ADA, etc.)
  - 10 historical major events with known impacts
  - Pre-built correlations (BTC↔ETH high, L1s correlated, stablecoins correlated)
- Seed data loads automatically if the graph is empty on startup

### Resource Limits & Guardrails

| Guardrail | Value | Rationale |
|-----------|-------|-----------|
| `KG_SYNC_INTERVAL_MINUTES` | 5 (default) | Balance freshness vs API rate limits |
| Max events in graph | 1000 | Prevent unbounded memory growth |
| Max assets in graph | 200 | Crypto-only scope for Phase 1 |
| News fetch timeout | 10s | Don't block worker on slow API |
| Graph file max size | 10MB | Alert if graph exceeds reasonable size |
| `ENABLE_MACRO_KG` | false (default) | Phase 2 feature gate |

### Architecture Compliance
- **Microservice Specialist Worker:** KG sync runs as an isolated Celery task, not inline in the API server.
- **Worker Isolation:** Uses dedicated `kg_sync` queue to avoid blocking backtest/RL workers.
- **Error Resilience:** All news API calls wrapped in try/except; graph query returns empty list on failure.
- **Data Precision:** Impact weights use float (0.0-1.0) — acceptable since these are heuristic scores, not financial calculations.

---

## Tasks / Subtasks

- [ ] Task 1: Create KG Data Models
  - [ ] Subtask 1.1: Create `agent/src/kg_models.py` with Pydantic models (KGEvent, KGAsset, KGImpact, KGSuggestion, KGSuggestionsResponse)
  - [ ] Subtask 1.2: Add `ENABLE_MACRO_KG` env var stub and Phase 2 feature flag check

- [ ] Task 2: Create Knowledge Graph Store
  - [ ] Subtask 2.1: Create `agent/src/kg_store.py` with `KnowledgeGraphStore` class
  - [ ] Subtask 2.2: Implement thread-safe in-memory adjacency list (nodes + edges dicts)
  - [ ] Subtask 2.3: Implement `save()` / `load()` for JSON persistence to `kg_data/graph.json`
  - [ ] Subtask 2.4: Implement `get_suggestions()` — aggregate impact weights per asset, rank, return top-N
  - [ ] Subtask 2.5: Implement `stats()` method for monitoring

- [ ] Task 3: Create Seed Data
  - [ ] Subtask 3.1: Create `agent/src/kg_seed_data.py` with top 20 crypto assets
  - [ ] Subtask 3.2: Add 10 historical crypto events with known impact mappings
  - [ ] Subtask 3.3: Add pre-built asset correlations (BTC-ETH, L1 basket, stablecoins)
  - [ ] Subtask 3.4: Implement auto-seed on empty graph startup

- [ ] Task 4: Create KG Crawler
  - [ ] Subtask 4.1: Create `agent/src/kg_crawler.py` with news fetching logic
  - [ ] Subtask 4.2: Implement CryptoCompare News API integration (primary source)
  - [ ] Subtask 4.3: Implement CoinGecko News fallback
  - [ ] Subtask 4.4: Implement keyword-based entity extraction (symbol mapping from news text)
  - [ ] Subtask 4.5: Implement event categorization and impact weight assignment
  - [ ] Subtask 4.6: Create `sync_knowledge_graph` Celery task with dedup logic
  - [ ] Subtask 4.7: Configure Celery Beat periodic schedule (every 5 min)

- [ ] Task 5: API Endpoints
  - [ ] Subtask 5.1: Add `GET /api/v1/kg/suggestions` endpoint to `api_server.py`
  - [ ] Subtask 5.2: Add `GET /api/v1/kg/events` endpoint
  - [ ] Subtask 5.3: Add `GET /api/v1/kg/stats` endpoint
  - [ ] Subtask 5.4: Add `POST /api/v1/kg/sync` manual trigger endpoint
  - [ ] Subtask 5.5: Wire KG store singleton initialization in API server startup

- [ ] Task 6: Infrastructure
  - [ ] Subtask 6.1: Add `kg_sync` queue route to `worker.py`
  - [ ] Subtask 6.2: Add `kg-worker` service to `docker-compose.yml` with Celery Beat
  - [ ] Subtask 6.3: Add `kg-data` Docker volume for persistence

- [ ] Task 7: Testing & Validation
  - [ ] Subtask 7.1: Unit test `KnowledgeGraphStore` — add/query/persistence round-trip
  - [ ] Subtask 7.2: Unit test `get_suggestions()` — ranking, min_weight filtering, limit
  - [ ] Subtask 7.3: Unit test entity extraction — known symbols from news titles
  - [ ] Subtask 7.4: Unit test seed data loading — verify graph is non-empty after seed
  - [ ] Subtask 7.5: Unit test API endpoints — suggestions returns valid schema on empty graph
  - [ ] Subtask 7.6: Unit test error handling — API unavailable returns empty list gracefully
  - [ ] Subtask 7.7: Integration test: manual sync trigger → graph updated → suggestions reflect new data

---

## File List

| File | Status | Description |
|------|--------|-------------|
| `agent/src/kg_models.py` | CREATED | Pydantic models for KG entities |
| `agent/src/kg_store.py` | CREATED | In-memory graph store with JSON persistence |
| `agent/src/kg_seed_data.py` | CREATED | Bootstrap data for crypto assets and events |
| `agent/src/kg_crawler.py` | CREATED | News crawler + Celery task for KG sync |
| `agent/src/worker.py` | MODIFIED | Added `kg_sync` queue route |
| `agent/api_server.py` | MODIFIED | Added KG API endpoints (`/api/v1/kg/*`) |
| `docker-compose.yml` | MODIFIED | Added `kg-worker` service and `kg-data` volume |
| `agent/tests/unit/test_kg_store.py` | CREATED | Unit tests for graph store |
| `agent/tests/unit/test_kg_crawler.py` | CREATED | Unit tests for crawler and entity extraction |
| `agent/tests/unit/test_kg_api.py` | CREATED | Unit tests for KG API endpoints |

---

## Change Log

- **2026-05-11:** Story created with full developer context for Phase 1 (Crypto-Native KG).

## Dev Agent Record (Debug Log / Implementation Plan)

### Implementation Plan
1. **Task 1 (Models):** Define Pydantic schemas first — these are the contract between all components.
2. **Task 2 (Store):** Build the graph store with full test coverage before moving to crawler.
3. **Task 3 (Seed):** Ensure the graph is usable immediately with seed data (no API dependency).
4. **Task 4 (Crawler):** Implement news fetching with graceful fallback chain.
5. **Task 5 (API):** Wire endpoints to the store singleton.
6. **Task 6 (Infra):** Docker/Celery configuration last (depends on all code being ready).
7. **Task 7 (Tests):** Tests written alongside each task, final integration test at the end.
