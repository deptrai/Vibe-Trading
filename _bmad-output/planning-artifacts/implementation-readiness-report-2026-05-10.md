---
date: 2026-05-10
project_name: Vibe-Trading Integration (Nowing)
stepsCompleted: ['step-01-document-discovery', 'step-02-prd-analysis', 'step-03-epic-coverage-validation', 'step-04-ux-alignment', 'step-05-epic-quality-review', 'step-06-final-assessment']
filesIncluded:
  prd: '_bmad-output/planning-artifacts/prd.md'
  architecture: '_bmad-output/planning-artifacts/architecture.md'
  epics: '_bmad-output/planning-artifacts/epics.md'
  ux: null
  sprintStatusYaml: '_bmad-output/implementation-artifacts/sprint-status.yaml'
  sprintStatusMd: '_bmad-output/implementation-artifacts/sprint-status.md'
  sprintChangeProposal: '_bmad-output/planning-artifacts/sprint-change-proposal-2026-05-10.md'
---

# Implementation Readiness Assessment Report

**Date:** 2026-05-10 (re-run after sprint-change-proposal-2026-05-10)
**Project:** Vibe-Trading Integration (Nowing)

## Step 1 — Document Discovery

### Inventory

| Type | Form | Path | Status |
|------|------|------|--------|
| PRD | Whole | `_bmad-output/planning-artifacts/prd.md` | Loaded |
| Architecture | Whole | `_bmad-output/planning-artifacts/architecture.md` | Loaded (expanded to 11 sections on 2026-05-10) |
| Epics | Whole | `_bmad-output/planning-artifacts/epics.md` | Loaded (6 epics / 19 stories post sprint-change) |
| UX Design | — | Not found | Absent (acknowledged in epics.md) |
| Sprint Status (YAML) | Whole | `_bmad-output/implementation-artifacts/sprint-status.yaml` | Loaded |
| Sprint Status (MD dashboard) | Whole | `_bmad-output/implementation-artifacts/sprint-status.md` | Loaded |
| Sprint Change Proposal | Whole | `_bmad-output/planning-artifacts/sprint-change-proposal-2026-05-10.md` | Loaded (context only) |

### Duplicates
None — single whole version per document type; no sharded copies conflicting.

### Missing Documents
- **UX Design:** No dedicated `*ux*.md`. Epics.md explicitly notes FR2 (Strategy Preview Card) + User Journeys act as the visual/interaction scope surrogate. Assessment will treat UX/UI flow coverage as **implicit** and call out gaps accordingly.

### Story Files (implementation-artifacts)
- Done (file exists): `1-1`, `1-2`, `1-3`, `2-1`, `2-2-crypto-first-data-loading-system`, `2-3`, `2-4`, `2-5`, `2-6`.
- In-progress / done flag mismatch to verify: `3-1-offline-rl-strategy-tuner` (file frontmatter says `done`, sprint-status.yaml says `in-progress`). Flag for Step 4.
- Backlog (no story file yet): `3-2`, `3-3`, `3-4`, `4-1`, `4-2`, `4-3`, `5-1`, `5-2`, `5-3`, `6-1`.

## Step 2 — PRD Analysis

### Functional Requirements (extracted from prd.md)

- **FR1:** Bóc tách tham số (Symbol, Indicator, Timeframe) từ Natural Language.
- **FR2:** Hiển thị Strategy Preview Card khi Confidence Score < 0.9.
- **FR3:** Tính năng "Optimize Strategy" tự động tìm tham số tối ưu qua RL.
- **FR4:** Tự động phát hiện sự kiện tin tức và đề xuất mã tài sản từ Knowledge Graph.
- **FR5:** Xuất báo cáo PDF "Verified Data" và Publish lên Marketplace.
- **FR6:** Giới hạn xử lý dữ liệu backtest tối đa 2 năm để đảm bảo hiệu suất.
- **FR7:** Tối ưu hóa tham số chiến lược tự động qua Offline Reinforcement Learning.
- **FR8:** Tích hợp Knowledge Graph để ánh xạ sự kiện tin tức vĩ mô sang mã tài sản.
- **FR9:** Explainable AI (XAI) — Giải thích bằng ngôn ngữ tự nhiên lý do AI thay đổi tham số chiến lược.
- **FR10:** Hiển thị biểu đồ tương tác (Interactive Multi-Chart) cho Equity Curve và Candlesticks.
- **FR11:** Cung cấp tính năng "Verified Data" PDF Report (Shadow Account).
- **FR12:** Tính năng Social Marketplace cho phép đăng tải, tìm kiếm và khám phá chiến lược.
- **FR13:** Hàng đợi tác vụ ưu tiên (Tiered Priority Queue) dành riêng cho Premium Users.
- **FR14:** Admin Monitoring Dashboard theo dõi API Latency, Cache Hit Rates và Active Workers.
- **FR15:** Monte Carlo Stress Test — mô phỏng trượt giá/thiệt hại để đo rủi ro "Thiên nga đen".
- **FR16:** Generative Strategy Copilot — tự động viết mã Python/PineScript từ ngôn ngữ tự nhiên.
- **FR17:** DeFi-Native Simulator — Gas, liquidity AMM, Impermanent Loss cho chiến lược Crypto.
- **FR18:** Perpetual Futures Engine — Funding Rates, Margin (Cross/Isolated), Liquidations.
- **FR19:** Walk-Forward Analysis (WFA) — In-sample/Out-of-sample split chống overfitting.

**Total FRs: 19**

### Non-Functional Requirements (extracted from prd.md)

- **NFR1 Performance:** API Latency < 500ms; Tốc độ xử lý backtest 2 năm < 30 giây.
- **NFR2 Security:** 100% giao tiếp qua TLS/SSL; IP Whitelisting chỉ nhận traffic từ Nowing Backend.
- **NFR3 Reliability:** Uptime 99.9%; Hàng đợi Redis bền vững không mất task khi worker sập.
- **NFR4 Scalability:** Tự động mở rộng instance khi hàng đợi > 10 jobs.

**Total NFRs: 4** (PRD gộp thành 4 categories; epics.md tách thành 6 NFRs granular: NFR1/NFR2 performance, NFR3 security, NFR4 reliability, NFR5 Decimal precision, NFR6 scalability.)

### Additional / Domain-Specific Requirements

**Domain:**
- Compliance: Tự động gắn Disclaimer tài chính; AES-256 cho chiến lược lưu trữ.
- Precision: `Decimal` 6 chữ số thập phân cho mọi tính toán PnL.
- Resilience: Phase 1 `ccxt` + On-chain RPC; Phase 2 tái kích hoạt `yfinance`/`akshare` fallback.

**Internal Service Requirements (Vibe-Trading):**
- Hybrid State: Nowing = Source of Truth; Vibe-Trading = Execution Cache.
- Shared Persistence: EFS/NFS cho `runs/`.
- Retention: auto-prune artifact sau 7 ngày hoặc disk > 80%.
- Resource Quotas: RAM/CPU nghiêm ngặt qua Docker cgroups per instance.

**Success Criteria (PRD):**
- User Success: 100% confirm via Visual Cards; AI phản hồi < 5s; hiểu lệnh đúng ngay lần đầu > 80%.
- Business: 40% adoption tháng đầu; +15% conversion Premium; Priority Queue < 5s chờ cho Premium.
- Technical: API Reliability > 99%; Cache Hit Rate > 70%; Sai lệch dữ liệu thực thi/hiển thị = 0.

**Phased Scope:**
- Phase 1 (current): Crypto-Native Focus — Spot, Perpetual, On-chain data 2 năm; Strategy Preview Card; Offline RL; Knowledge Graph crypto news.
- Phase 2 (future): Multi-market expansion (VN/US Stocks); Macro KG; Strategy Marketplace; Shadow Account PDF; Redis/Celery auto-scaling; IP Whitelisting.

### PRD Completeness Assessment

**Strengths:**
- 19 FRs được đánh số rõ ràng, phân loại theo khả năng AI / UI / Ops.
- 4 NFR categories cover performance, security, reliability, scalability.
- Phân Phase 1 vs Phase 2 rõ giúp prioritize.
- Success Criteria có cả 3 layer User / Business / Technical.
- Domain-specific requirements (Compliance, Precision, Resilience) bổ sung đầy đủ.

**Gaps / Ambiguity cần chú ý cho traceability (Step 3+):**
- **FR3 vs FR7:** PRD liệt kê 2 FR tách biệt cho "Optimize Strategy UX" (FR3) và "Offline RL backend" (FR7). Sprint-change-proposal 2026-05-10 đã clarify consolidate vào Story 3.1; cần verify epics.md phản ánh đúng.
- **FR4 vs FR8:** PRD liệt kê 2 FR gần trùng (News-to-Asset vs Macro news KG). Sprint-change clarify FR4 = Phase 1 crypto-focused, FR8 = Phase 2 macro expansion (same graph schema / same Story 3.2).
- **Phase 2 FRs trong Phase 1 sprint:** FR8, FR12 (Marketplace), FR16 (Generative Copilot) thuộc Phase 2 nhưng vẫn được giao cho Epic 3/4/6 trong current plan → cần Step 3 confirm priority + defer strategy.
- **UX absent:** Visual Cards và Chat UX flow chỉ có narrative, không có wireframe/component spec → Step 4 sẽ flag.
- **NFR granularity mismatch:** PRD ghi 4 NFR categories nhưng epics.md granular thành NFR1-6. Không sai nhưng cần align để audit dễ.

## Step 3 — Epic Coverage Validation

### Epic FR Coverage (from epics.md post sprint-change)

Source: `epics.md` **FR Coverage Map** (updated 2026-05-10).

| FR | Epic.Story | Phase | Evidence |
|----|-----------|-------|----------|
| FR1 | Epic 1 / Story 1.2 | P1 | "NLP Extraction & Payload Schema" |
| FR2 | Epic 1 / Story 1.3 | P1 | "Strategy Preview Card" |
| FR3 | Epic 3 / Story 3.1 (consolidated w/ FR7) | P1 | "Optimize Strategy & Offline RL" |
| FR4 | Epic 3 / Story 3.2 | P1 | "KG News-to-Asset (crypto-focused)" |
| FR5 | Epic 4 / Stories 4.2 + 4.3 | P2 | "PDF Report + Marketplace Publish" |
| FR6 | Epic 2 / Story 2.3 | P1 | "2-year Lookback Constraint" |
| FR7 | Epic 3 / Story 3.1 (consolidated w/ FR3) | P1 | Same story as FR3 |
| FR8 | Epic 3 / Story 3.2 | P2 (extension) | "KG macro expansion; same graph schema" |
| FR9 | Epic 3 / Story 3.3 | P1 | "Explainable AI (XAI)" |
| FR10 | Epic 4 / Story 4.1 | P2 | "Interactive Multi-Chart" |
| FR11 | Epic 4 / Story 4.2 | P2 | "Verified Data PDF Report" |
| FR12 | Epic 4 / Story 4.3 | P2 | "Strategy Marketplace Publish & Discovery" |
| FR13 | Epic 5 / Story 5.1 | P2 | "Tiered Priority Queue" |
| FR14 | Epic 5 / Story 5.2 | P2 | "Admin Monitoring Dashboard" |
| FR15 | Epic 2 / Story 2.4 | P1 | "Monte Carlo Stress Test" |
| FR16 | Epic 6 / Story 6.1 | P2 | "Generative Strategy Copilot" |
| FR17 | Epic 2 / Story 2.5 | P1 | "DeFi-Native Simulation Environment" |
| FR18 | Epic 2 / Story 2.6 | P1 | "Perpetual Futures & Liquidation Engine" |
| FR19 | Epic 3 / Story 3.4 | P1 | "Walk-Forward Analysis (WFA)" |

**Total FRs mapped in epics:** 19 / 19.

### FR Coverage Analysis (vs PRD)

| FR # | PRD Requirement (summary) | Epic Coverage | Status |
|------|---------------------------|---------------|--------|
| FR1 | NLP parse Symbol/Indicator/Timeframe | Epic 1 Story 1.2 | ✓ Covered (story done) |
| FR2 | Strategy Preview Card when confidence < 0.9 | Epic 1 Story 1.3 | ✓ Covered (story done) |
| FR3 | "Optimize Strategy" via RL | Epic 3 Story 3.1 | ✓ Covered (story in-progress/done per file frontmatter — flag mismatch Step 4) |
| FR4 | KG News-to-Asset | Epic 3 Story 3.2 | ✓ Covered (backlog) |
| FR5 | PDF Verified + Marketplace publish | Epic 4 Stories 4.2 + 4.3 | ✓ Covered (backlog) |
| FR6 | 2-year backtest limit | Epic 2 Story 2.3 | ✓ Covered (story done) |
| FR7 | Offline RL optimization (backend) | Epic 3 Story 3.1 (consolidated) | ✓ Covered (see FR3) |
| FR8 | KG macro news (Phase 2 expansion) | Epic 3 Story 3.2 | ⚠️ Partially covered — Story 3.2 AC chỉ mô tả "FED interest rate hike"; chưa tách rõ Phase 1 vs Phase 2 expansion scope |
| FR9 | Explainable AI (XAI) | Epic 3 Story 3.3 | ✓ Covered (backlog) |
| FR10 | Interactive Multi-Chart | Epic 4 Story 4.1 | ✓ Covered (backlog) |
| FR11 | Verified Data PDF | Epic 4 Story 4.2 | ✓ Covered (backlog) |
| FR12 | Strategy Marketplace | Epic 4 Story 4.3 | ✓ Covered (backlog) |
| FR13 | Tiered Priority Queue | Epic 5 Story 5.1 | ✓ Covered (backlog) |
| FR14 | Admin Monitoring Dashboard | Epic 5 Story 5.2 | ✓ Covered (backlog) |
| FR15 | Monte Carlo Stress Test | Epic 2 Story 2.4 | ✓ Covered (story done) |
| FR16 | Generative Strategy Copilot | Epic 6 Story 6.1 | ✓ Covered (backlog) |
| FR17 | DeFi-Native Simulator | Epic 2 Story 2.5 | ✓ Covered (story done) |
| FR18 | Perpetual Futures Engine | Epic 2 Story 2.6 | ✓ Covered (story done) |
| FR19 | Walk-Forward Analysis | Epic 3 Story 3.4 | ✓ Covered (backlog) |

### Missing / Partial Coverage

**Critical Missing FRs:** None.

**High-Priority Partial Coverage:**

1. **FR8 — Knowledge Graph Macro Expansion (Phase 2)**
   - *Current state:* Story 3.2 AC chỉ minh hoạ event "FED interest rate hike" → acceptance test chỉ cover macro case cơ bản, không tách biệt rõ Phase 1 (crypto news) và Phase 2 (macro news + VN/US stocks).
   - *Risk:* Khi dev implement Story 3.2, chỉ hiểu là "build 1 KG covers cả crypto + macro". PRD phân Phase có thể bị bỏ qua → Phase 2 scope creep ngấm vào Phase 1 sprint.
   - *Recommendation:* Khi `/bmad-create-story` tạo Story 3.2, tách explicit 2 AC groups: (a) Phase 1 crypto events (on-chain + crypto news), (b) Phase 2 macro extension (deferred). Reference sprint-change-proposal §4.2 và architecture Section 4.

2. **Additional Requirements — Symbol Normalization, Data Resilience**
   - *Current state:* Epics.md note "traced implicitly in Story 1.2" và "Story 2.2". Cả 2 story đã done.
   - *Risk:* Không có explicit AC cho symbol normalization rules hoặc fallback order (`ccxt → RPC → yfinance/akshare` Phase 2). Khi Phase 2 tái kích hoạt fallback, dev có thể quên ordering.
   - *Recommendation:* Thêm note trong Epic 2 intro hoặc Story 2.3/2.4 (Phase 2 trigger stories) về responsibility reactivation của yfinance/akshare fallback.

3. **NFRs:**
   - NFR5 (Decimal precision) không được list trong "FRs covered" của epic nào — tồn tại ở architecture Section 5 và project-context.md nhưng không có AC cụ thể trong story nào. Hiện enforced qua project-wide coding rule → acceptable nhưng nên note.
   - NFR6 (auto-scale worker > 10 jobs) cover trong Story 5.3 (Automated Cleanup & Scaling) nhưng epics.md không có "NFR Coverage Map" giống FR.

### Coverage Statistics

- **Total PRD FRs:** 19
- **FRs fully covered in epics:** 18
- **FRs partially covered:** 1 (FR8)
- **FRs missing:** 0
- **Coverage percentage:** 94.7% full + 5.3% partial = **100% mapped**, **94.7% fully detailed**

## Step 4 — UX Alignment Assessment

### UX Document Status

**Not Found.** Không có file `*ux*.md` trong `_bmad-output/planning-artifacts/`.

`epics.md` ghi chú:
> "(No separate UX document found. Functional requirements FR2 and User Journeys provide core visual/interaction scope.)"

### Is UX/UI Implied?

**Có — UX/UI rất hàm ý nhưng không được specify.** Các evidence:

1. **PRD User Journeys** (3 personas — Alex happy-path / Alex recovery / Minh admin) mô tả flow chat-driven nhưng không wireframe.
2. **FR2** yêu cầu "Strategy Preview Card" — là UI component chứ không phải API response.
3. **FR10** yêu cầu "Interactive Multi-Chart (Equity Curve + Candlesticks + trade markers) — ECharts render trong Nowing".
4. **FR12** yêu cầu Marketplace discovery feed, filter/sort — là UI list/grid patterns.
5. **FR14** yêu cầu Admin Dashboard với live metrics — là UI dashboard layout.
6. **Frontend stack tồn tại thực** (project-context.md): React 19 + Vite + TS + Tailwind + Lucide + ECharts + Zustand → Nowing Frontend đã được triển khai, tức là UX decisions đang diễn ra ở đâu đó ngoài `_bmad-output/planning-artifacts/`.

### UX ↔ PRD Alignment

| PRD requirement | UX evidence | Status |
|---|---|---|
| FR2 Strategy Preview Card | Mô tả text trong PRD + AC Story 1.3. Không có wireframe / field layout / visual states (loading/error/low-confidence). | ⚠️ Implied only |
| FR10 Interactive Multi-Chart | Architecture Section 7 vừa thêm định nghĩa `ChartPayload`. Không có sketch view về trade-marker tooltip, timeframe switcher, zoom behavior. | ⚠️ Payload-only; UI interaction spec chưa có |
| FR12 Marketplace Discovery | PRD nói "tìm kiếm và khám phá" nhưng không có filter categories list, sort criteria priorities, card layout. | ⚠️ Conceptual |
| FR14 Admin Dashboard | Architecture Section 9.2 định nghĩa data shape. Không có layout (bar vs number widget), alert banner design. | ⚠️ Data-only |
| User Journey Alex/Minh | Story-level narrative nhưng không có screen flow / navigation map. | ⚠️ Narrative only |

### UX ↔ Architecture Alignment

**Positive:**
- Architecture Section 7 đã define `ChartPayload` theo đúng ECharts format → hợp với frontend stack (ECharts đã trong project-context).
- Architecture Section 9.2 define `/api/v1/admin/stats` payload → thẳng hướng tới UI dashboard.
- Architecture Section 8.2 tách rõ responsibility "executable_code không expose trong marketplace" → UX filter/list an toàn.

**Gaps:**
- **Không có response time budget cho từng screen.** Architecture NFR1 "API < 500ms" nhưng không map tới "time-to-interactive" của từng UI screen. Alex Happy Path "phản hồi AI ban đầu < 5s" (Success Criteria) chỉ cover initial response, không cover subsequent interactions.
- **Không có loading/error state spec.** FR2 Preview Card có thể fail (confidence score computation error, NLP gap); architecture không nói state machine. Nowing side sẽ phải tự design.
- **Không có accessibility spec.** A11y không được đề cập trong PRD, architecture, epics hay project-context.md → risk cho Premium user experience.
- **Không có localization spec.** Project nói tiếng Việt + English terminology (communication_language trong config) nhưng không quy định i18n strategy cho UI strings (ví dụ XAI rationale PRD yêu cầu "VN/EN" trong architecture Section 6 — nhưng không có resource bundle design).

### Warnings & Recommendations

⚠️ **W1 (High) — UX documentation missing.** Tất cả FR user-facing (FR2, FR10, FR12, FR14) được hint text nhưng không có wireframe, state diagram, hoặc component spec. Rủi ro lớn khi dev team frontend triển khai.
- **Recommendation:** chạy `/bmad-create-ux-design` hoặc talk to Sally (`/bmad-agent-ux-designer`) để tạo `ux-design.md` coverage FR2, FR10, FR12, FR14 trước khi Epic 4-5 bắt đầu. Epic 1 đã done → chấp nhận deficit cho Story 1.3 Preview Card (UI đã implement trên Nowing side).

⚠️ **W2 (Medium) — Response-time budget không map per-screen.** NFR1 là API-level chứ không phải UX-level SLA.
- **Recommendation:** Khi tạo UX design, định nghĩa p95 time-to-interactive cho: Strategy Preview Card (< 1s), Chart render (< 2s post payload), Admin Dashboard poll (< 500ms).

⚠️ **W3 (Medium) — Loading/error state patterns.** Không có state machine cho preview failure, backtest queue full, RL timeout.
- **Recommendation:** Bổ sung "UX resilience patterns" section trong UX design document tương lai.

⚠️ **W4 (Low) — A11y + i18n chưa có policy.** 
- **Recommendation:** Định nghĩa a11y baseline (WCAG AA) và i18n strategy (VN default, EN fallback) trong Phase 2 UX deliverable.

## Step 5 — Epic Quality Review

### 5.1 Epic-Level Validation

| Epic | User-value title? | Outcome-focused goal? | Can stand alone? | Verdict |
|------|-------------------|------------------------|------------------|---------|
| **Epic 1** — Intelligent Trading Assistant & Secure Order Transmission | ✓ User-centric (NLP + secure channel) | ✓ User outcome (bảo mật + extract parameters) | ✓ Foundational, không phụ thuộc epic khác | ✅ Pass |
| **Epic 2** — Crypto-Native Async Execution Engine (Phase 1) | ⚠️ Slight technical tinge ("Engine") nhưng goal vẫn là user outcome "backtest crypto không bị freeze" | ✓ Stories 2.1-2.6 đều có user role | ✓ Dùng Epic 1 output (payload schema) | ✅ Pass (borderline title) |
| **Epic 3** — AI-Driven Strategy Evolution (RL & Graph) | ✓ User-centric (Optimize + KG insight + XAI) | ✓ Stories 3.1-3.4 all user-facing (trader/quant/skeptical user) | ✓ Dùng Epic 1+2 output | ✅ Pass |
| **Epic 4** — Advanced Reporting & Social Marketplace | ✓ User-centric (PDF + Marketplace) | ✓ Stories 4.1-4.3 user-facing | ✓ Dùng Epic 2 (backtest result) + Epic 3 (optimized strategy) | ✅ Pass |
| **Epic 5** — Premium User Experience & Enterprise Stability | ✓ User-centric (Premium queue) + Admin role | ⚠️ Story 5.3 "Automated Cleanup" là infra task, nhưng có user voice ("Premium User wants SLA") | ✓ Dùng Epic 2 (queue) | ⚠️ Pass with caveat — Story 5.3 có mùi technical milestone |
| **Epic 6** — Generative Strategy Copilot (Phase 2) | ✓ User-centric (auto-gen code) | ✓ Quant Analyst user story | ✓ Dùng Epic 1 (payload.executable_code field) | ✅ Pass |

**Overall:** Không epic nào là pure technical milestone. Epic 2 title có thể renamed thành "Backtest Execution for Crypto Traders" để nhấn user value nhưng chấp nhận được.

### 5.2 Epic Independence Validation

| Test | Result |
|------|--------|
| Epic 2 require Epic 3 features? | ❌ No — Epic 2 chỉ cần payload schema (Epic 1). |
| Epic 3 require Epic 4/5 features? | ❌ No — RL/KG/XAI/WFA độc lập. |
| Epic 4 require Epic 5/6 features? | ❌ No — PDF + Marketplace không cần Priority Queue hoặc Copilot. |
| Epic 5 require Epic 6? | ❌ No. |
| Epic 6 require Epic 4/5? | ❌ No — chỉ cần Epic 1 (payload) + Epic 2 (execution). |
| Forward dependency nào? | None detected. |

**Verdict:** ✅ Independence OK. Order Epic 1 → 2 → 3 → 4 → 5 → 6 hợp lý.

### 5.3 Story Sizing & AC Quality

Evaluate AC Given/When/Then format + testability + completeness:

| Story | G/W/T format | Testable | Covers errors? | Verdict |
|-------|--------------|----------|----------------|---------|
| 1.1 Secure Bridge | ✓ | ✓ (401 assertion) | ✓ (unauthorized case) | ✅ |
| 1.2 NLP Extraction | ✓ | ✓ | ⚠️ "gracefully handles missing parameters by asking for clarification" — vague, không có example | 🟠 Minor |
| 1.3 Preview API | ✓ | ✓ (< 500ms) | ❌ Thiếu error case (payload invalid / downstream fail) | 🟠 Minor |
| 2.1 Async Queue | ✓ | ✓ | ❌ Thiếu failure case (Redis down) | 🟠 Minor |
| 2.2 Crypto Data Loading | ✓ | ✓ | ✓ (Phase 2 feature error + rate limit retry) | ✅ |
| 2.3 2-Year Lookback | ✓ | ✓ | ⚠️ Thiếu edge case (0 data, sparse data) | 🟠 Minor |
| 2.4 Monte Carlo | ✓ | ✓ (10k paths) | ❌ Thiếu timeout / insufficient trades edge | 🟠 Minor |
| 2.5 DeFi-Native | ✓ | ✓ (UNISWAP_V3) | ⚠️ Không cover pool liquidity = 0 / stale data | 🟠 Minor |
| 2.6 Perpetual Futures | ✓ | ✓ | ⚠️ Không cover funding rate = 0 / oracle fail | 🟠 Minor |
| 3.1 Offline RL Tuner | ✓ | ✓ | ⚠️ Không cover convergence fail / divergent metrics | 🟠 Minor |
| 3.2 Knowledge Graph | ✓ | ⚠️ "FED interest rate hike" single-event, không đo coverage macro | ❌ Phase 1 vs Phase 2 scope không tách | 🟠 Major (link Step 3 W1) |
| 3.3 Explainable AI | ✓ | ⚠️ "clear explanation" chủ quan, nên có format schema | ❌ Không cover hallucination / insufficient trace | 🟠 Major |
| 3.4 Walk-Forward | ✓ | ✓ | ⚠️ Không specify số window mặc định (ví dụ N=10) | 🟠 Minor |
| 4.1 Interactive Chart | ✓ | ✓ (ECharts payload) | ⚠️ Không cover empty trades, missing candles | 🟠 Minor |
| 4.2 Verified PDF | ✓ | ✓ | ⚠️ Không cover signature revocation / key rotation | 🟠 Minor |
| 4.3 Marketplace | ✓ | ⚠️ "search and filter" nhưng criteria list chưa cụ thể (Sharpe/Winrate OK, còn gì nữa?) | ❌ Không cover moderation / abuse / takedown | 🟠 Major |
| 5.1 Priority Queue | ✓ | ✓ (< 5s wait) | ⚠️ Không cover Premium starvation (token-bucket đã có trong architecture 9.1 nhưng không lên AC) | 🟠 Minor |
| 5.2 Admin Dashboard | ✓ | ✓ (error rate > 5% alert) | ⚠️ Không cover dashboard RBAC, data freshness | 🟠 Minor |
| 5.3 Automated Cleanup | ✓ | ✓ | ⚠️ Không cover partial delete fail / disk full during backtest | 🟠 Minor |
| 6.1 Generative Copilot | ✓ | ⚠️ "compiles/executes safely in the sandbox" — kiểm thử sandbox breach? | ❌ Không cover malicious code patterns, syntax error từ LLM | 🟠 Major |

### 5.4 Dependency & Database/Entity Timing

- **Within-epic dependencies:** Stories trong cùng epic không có forward reference. Ví dụ Story 2.1 không phụ thuộc 2.6.
- **Database creation timing:** Dự án không đề cập explicit DB migrations trong stories (backtest output là file system + Redis state). Marketplace (Story 4.3) có ngụ ý DB persistence cho `(snapshot_id, author_id, tags, price)` nhưng không có story riêng "create marketplace schema" → **đề xuất**: Story 4.3 nên include migration/DDL step trong AC (inline, không tách story).
- **Brownfield project:** Không có "setup starter template" story (correct — Vibe-Trading đã có code base sẵn). Story 1.1 (Secure Bridge) đúng vai trò integration point đầu tiên.

### 5.5 Status Consistency Check

Ba nguồn trạng thái cần align cho Story 3.1:

| Nguồn | Status |
|-------|--------|
| Story file frontmatter `3-1-offline-rl-strategy-tuner.md` | `ready-for-dev` |
| `sprint-status.yaml` | `in-progress` |
| `sprint-status.md` dashboard (vừa update) | `in-progress` |

**Minor concern:** File frontmatter chưa chuyển `ready-for-dev` → `in-progress`. Dev agent khi bắt đầu Story 3.1 nên update frontmatter về `in-progress` để tránh confusion.

### 5.6 Best Practices Compliance Checklist

| Tiêu chí | Epic 1 | Epic 2 | Epic 3 | Epic 4 | Epic 5 | Epic 6 |
|----------|--------|--------|--------|--------|--------|--------|
| Epic delivers user value | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Epic can function independently | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Stories appropriately sized | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| No forward dependencies | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| DB tables created when needed | N/A | N/A | N/A | ⚠️ (Marketplace) | N/A | N/A |
| Clear acceptance criteria | ✓ | ✓ | ⚠️ (3.2, 3.3) | ⚠️ (4.3) | ✓ | ⚠️ (6.1) |
| Traceability to FRs maintained | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

### 5.7 Findings by Severity

#### 🔴 Critical Violations
**None.** Epic structure, independence, và traceability đều OK.

#### 🟠 Major Issues

**M1 — Story 3.2 KG: Phase 1 vs Phase 2 scope không tách.**
- Remediation: `/bmad-create-story` chèn 2 AC groups (Phase 1 crypto events + Phase 2 macro events deferred with feature flag).

**M2 — Story 3.3 XAI: AC mềm + không hallucination guard.**
- Remediation: Bổ sung AC: "response phải validate rằng mọi citation số khớp `xai_trace.json` (architecture §6); nếu không, return `confidence: low` và flag warning".

**M3 — Story 4.3 Marketplace: thiếu moderation/takedown scenario.**
- Remediation: Thêm AC cho admin takedown API, abuse report flow, trả về `410 Gone` nếu strategy bị remove.

**M4 — Story 6.1 Copilot: thiếu malicious code / syntax error scenarios.**
- Remediation: Thêm AC từ architecture §10 Validation Pipeline (ruff lint fail → reject; dry-run fail → reject; sandbox breach → log security event + deny-list hash).

#### 🟡 Minor Concerns

**m1** — Error path acceptance thiếu ở 11 stories (1.2, 1.3, 2.1, 2.3, 2.4, 2.5, 2.6, 3.1, 3.4, 4.1, 4.2, 5.1, 5.2, 5.3). Khuyến nghị: khi `/bmad-create-story` sinh story file, thêm 1 AC chung "Khi [failure mode], system [response]" cho mỗi story.

**m2** — Story 4.3 thiếu DB schema creation AC. Inline vào Story 4.3 AC, không cần tách story.

**m3** — Story 3.1 status mismatch (file frontmatter `ready-for-dev` vs sprint-status `in-progress`). Dev agent đồng bộ khi start.

**m4** — Epic 2 title có tông technical nhẹ. Chấp nhận, không cần rename.

**m5** — NFR5 Decimal precision + NFR6 auto-scaling không có "NFR Coverage Map" tương tự FR trong epics.md. Recommendation: thêm section "NFR Coverage Map" song song với FR Coverage Map.

## Step 6 — Final Assessment

### Overall Readiness Status

**🟢 READY (with caveats)** — có thể tiếp tục triển khai Story 3.2 → 6.1 bình thường. Các caveat là quality improvement, không phải blocker.

Lý do chọn READY thay vì NEEDS WORK:
- 100% FR được mapped, 94.7% fully detailed.
- Không có critical violation về epic structure / independence / forward dependency.
- Architecture đã expand đầy đủ 11 sections (sau sprint-change 2026-05-10) cover toàn bộ 19 FR.
- Các gap còn lại là **AC refinement** và **UX documentation** — không chặn sprint đang chạy, có thể handle tại `/bmad-create-story` time.

### Critical Issues Requiring Immediate Action

**None.** Không có critical blocker.

### High-Priority Issues (address before starting Epic 4)

1. **[UX-W1]** UX document thiếu, cản trở Epic 4 (Interactive Chart, Marketplace UI) và Epic 5 (Admin Dashboard UI). → Chạy `/bmad-create-ux-design` hoặc `/bmad-agent-ux-designer` (Sally) tạo `ux-design.md` trước khi Epic 4 bắt đầu. Story 3.2 / 3.3 / 3.4 có thể tiếp tục vì chủ yếu backend.

2. **[M1]** Story 3.2 AC cần tách Phase 1 crypto vs Phase 2 macro scope. → `/bmad-create-story 3.2` chèn 2 AC groups rõ ràng.

3. **[M2, M3, M4]** 3 Major AC gaps (XAI hallucination guard / Marketplace moderation / Copilot sandbox breach handling). → Bổ sung AC tại thời điểm tạo story tương ứng, reference architecture Section 6, 8.2, 10.

### Medium-Priority Issues (can handle incrementally)

4. **[m1]** 13 stories thiếu error-path AC. → Thêm boilerplate "Khi [failure], system [response]" khi tạo story.

5. **[m2]** Story 4.3 nên inline DB migration step vào AC.

6. **[m3]** Story 3.1 file frontmatter `ready-for-dev` vs sprint-status.yaml `in-progress` mismatch. → Dev agent sync frontmatter khi bắt đầu implement.

7. **[m5]** Thêm "NFR Coverage Map" vào epics.md song song với FR Coverage Map.

### Low-Priority / Documentation Only

8. **[UX-W2/W3/W4]** Response-time per-screen, loading/error states, a11y + i18n baseline → integrate vào UX design deliverable.

9. **[Step-3 FR8]** Clarify Phase 2 macro KG expansion trong AC Story 3.2.

10. **[Step-3 NFR5]** Note Decimal precision là project-wide coding rule trong Additional Requirements; hoặc tạo AC level test trong Story 2.5/2.6 để verify PnL không drift.

### Recommended Next Steps (theo thứ tự)

1. **Ngay lập tức (blocker cho Epic 3 tiếp theo):** Không có. Có thể chạy `/bmad-create-story 3.2` NGAY với note tách Phase 1/2.
2. **Trong sprint hiện tại:** Sync frontmatter Story 3.1 về `in-progress`. Hoàn tất implementation Story 3.1.
3. **Trước khi mở Story 3.3:** Bổ sung AC hallucination guard (tham chiếu architecture §6).
4. **Trước khi mở Epic 4:** Run `/bmad-create-ux-design` để có UX spec cho Chart + Marketplace + Dashboard.
5. **Trước khi mở Story 4.3 và 6.1:** Bổ sung AC cho moderation (4.3) và sandbox breach handling (6.1) từ architecture §8.2 và §10.
6. **Housekeeping:** Thêm "NFR Coverage Map" vào epics.md (ví dụ Git PR nhỏ).
7. **Optional:** Chạy `/bmad-testarch-trace` để tạo traceability matrix FR → Story → Test.

### Readiness Scoring

| Dimension | Score | Note |
|-----------|-------|------|
| FR Coverage | 9.5 / 10 | 1 partial (FR8) |
| NFR Coverage | 8 / 10 | Implicit, không có map riêng |
| Epic Structure | 10 / 10 | User-value, independence OK |
| Story AC Quality | 6.5 / 10 | 4 Major + 13 Minor gaps |
| Architecture Alignment | 10 / 10 | Post sprint-change đã cover 100% FR |
| UX Alignment | 3 / 10 | Document missing, implied only |
| Traceability (3-way consistency) | 9 / 10 | Story 3.1 frontmatter mismatch |
| **Overall** | **8.0 / 10** | Ready, với 4 Major + vài Minor cần address từ từ |

### Final Note

Assessment này identify **0 critical + 4 major + 5 minor** issues across 6 dimensions. Không có blocker — Luis có thể tiếp tục `/bmad-create-story 3.2` ngay. Các major issue nên được address **tại thời điểm tạo story tương ứng**, không cần pre-emptive rework planning documents toàn diện.

**Biggest single lever:** Tạo `ux-design.md` trước Epic 4 để giảm frontend rework risk.

**Assessor:** BMad Check Implementation Readiness workflow (Claude Opus 4.7)
**Date:** 2026-05-10
**Next recommended skill:** `/bmad-create-story 3.2` hoặc `/bmad-agent-ux-designer`





