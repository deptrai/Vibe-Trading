---
project_name: 'Vibe-Trading'
user_name: 'Luisphan'
date: '2026-05-03'
sections_completed:
  ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'quality_rules', 'workflow_rules', 'anti_patterns']
status: 'complete'
rule_count: 25
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

### Backend (Python 3.11+)
- **Core Orchestration:** `langgraph` (~0.2.50), `langchain` (>=0.1.0)
- **API & Server:** `fastapi` (>=0.104.0), `uvicorn`, `fastmcp` (>=2.0.0)
- **Data Science:** `pandas` (>=2.0.0), `numpy` (>=1.24.0), `duckdb` (>=1.2.0), `scikit-learn` (>=1.3.0)
- **Finance Libraries:** `akshare` (>=1.12.0), `yfinance` (>=0.2.30), `ccxt` (>=4.0.0), `tushare` (>=1.2.89)
- **Reporting:** `jinja2`, `weasyprint` (>=60.0), `matplotlib`

### Frontend (React 19)
- **Build Tool:** `Vite` (>=6.0.0)
- **Language:** `TypeScript` (>=5.7.0)
- **UI & Styling:** `Tailwind CSS` (>=3.4.0), `Lucide React`, `ECharts`
- **Routing & State:** `React Router` (>=7.1.0), `Zustand` (>=5.0.0)

---

## Critical Implementation Rules

### Language-Specific Rules

- **Python Type Hinting:** Mandatory use of `from __future__ import annotations`. All functions must have complete type hints for arguments and return values.
- **Async/Await:** Use `async/await` for all I/O bound operations (API calls, DB queries) using `httpx` or native async drivers.
- **Pydantic v2:** Mandatory use of Pydantic for data validation, settings management, and API schemas.
- **TypeScript Strict Mode:** No `any` allowed. Use `interface` for object structures and `type` for unions/primitives.

### Framework-Specific Rules

- **AgentLoop Context:** Do NOT bypass the 5-layer context management (`microcompact`, `context_collapse`, etc.) in `agent/src/agent/loop.py`.
- **Tool Registration:** All agent tools must be registered via `ToolRegistry` with comprehensive Google-style docstrings.
- **React 19 Patterns:** Use `StrictMode`. Prefer Functional Components. Use `Zustand` for global state and avoid prop-drilling (>3 levels).
- **State Persistence:** Use `RunStateStore` for agent session state; avoid global variables for request-scoped data.

### Testing Rules

- **Pytest Markers:** Categorize tests with `@pytest.mark.unit` (no network/IO) or `@pytest.mark.integration`.
- **Mocking Strategy:** Always mock external financial APIs (`akshare`, `yfinance`) and LLM responses in unit tests.
- **Frontend Validation:** All changes must pass `tsc -b` type checking.

### Code Quality & Style Rules

- **Linting:** Python code must pass `ruff check` and `ruff format` (120 char limit).
- **Naming Conventions:** `snake_case` for Python functions/vars, `PascalCase` for classes and React components.
- **Documentation:** Google-style docstrings mandatory for all public API/Hàm. Comments should explain "Why", not "What".

### Development Workflow Rules

- **Conventional Commits:** Use prefixes like `feat:`, `fix:`, `docs:`, `chore:`.
- **Environment Variables:** Never hardcode secrets. Use `.env` files and access via Pydantic `BaseSettings`.
- **Git Flow:** Develop on feature branches; never commit directly to `main`.

### Critical Don't-Miss Rules

- **Token Protection:** Never disable context pruning. Ensure `max_iterations` is set for all agent loops.
- **Security:** Do NOT log or print environment variables or sensitive keys.
- **Data Precision:** Use high-precision types for financial calculations to avoid floating-point drift in backtests.
- **Shadow Account:** Verify all trading logic changes against the `Shadow Account` simulation before deployment.

---

## Usage Guidelines

**For AI Agents:**
- Read this file before implementing any code.
- Follow ALL rules exactly as documented.
- When in doubt, prefer the more restrictive option.
- Update this file if new patterns emerge.

**For Humans:**
- Keep this file lean and focused on agent needs.
- Update when technology stack changes.
- Review quarterly for outdated rules.

Last Updated: 2026-05-03
