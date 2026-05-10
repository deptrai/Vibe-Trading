---
title: Sprint Change Proposal — Planning Artifact Sync (Pre-Epic 3 Continuation)
date: 2026-05-10
author: Luisphan (via BMad Correct Course)
project: Vibe-Trading Integration (Nowing)
scope_classification: Moderate
change_category: Misunderstanding of original requirements + missing architecture coverage
path_forward: Direct Adjustment (Option 1)
---

# Sprint Change Proposal — 2026-05-10

## 1. Issue Summary

Sau khi hoàn tất **Epic 1 (3 stories — done)** và **Epic 2 (6 stories — done)** và khi Story 3.1 đang in-progress, review 3 tài liệu planning (`prd.md`, `architecture.md`, `epics.md`) cùng `sprint-status.yaml` đã lộ ra 4 nhóm **gap/inconsistency** khiến các artifact không còn là single source of truth:

1. `architecture.md` chỉ cover FR1-FR5 ở dạng tổng hợp, **thiếu technical design cho 8 FR** còn lại (FR9, FR10, FR11, FR12, FR13, FR14, FR16, FR19).
2. `sprint-status.yaml` lệch với `epics.md`: thiếu Epic 6, sai slug Story 3.4, có entry lỗi `3-4-generative-strategy-copilot-p2`, sai slug Story 2.2.
3. **FR Coverage Map** trong `epics.md` sai (FR4 bị map vào Epic 2 thay vì Epic 3) và chưa clarify quan hệ FR3↔FR7, FR4↔FR8.
4. 2 **cross-cutting additional requirements** (Symbol Normalization, Data Resilience) không có story trace, dù đã implement trong Story 1.2/2.2.

**Trigger context:** Phát hiện khi user (Luisphan) review proactive trước khi tạo story 3.2. Yêu cầu cứng: chỉ đụng planning artifact, **KHÔNG** đụng source code trong `agent/` và `docs/`, không thay đổi Epic 1-2 đã done và Story 3.1 in-progress.

## 2. Impact Analysis

### 2.1 Epic Impact
- **Epic 1, 2 (done):** Không scope change. Chỉ sync tên story 2.2 trong tracking (`multi-market` → `crypto-first`) để match epics.md Phase 1 intent.
- **Epic 3 (in-progress):** Không scope change. Story 3.1 giữ nguyên; FR Coverage Map giờ ghi rõ Story 3.1 consolidate cả FR3 (user-facing) + FR7 (backend RL). Story 3.4 rename slug về đúng `3-4-walk-forward-analysis-wfa`.
- **Epic 4, 5 (backlog):** Không scope change. `architecture.md` bổ sung design để xóa gap cho FR10-14.
- **Epic 6 (backlog):** **Mới xuất hiện trong tracking** — `sprint-status.yaml` bổ sung `epic-6` + `6-1-generative-strategy-copilot`.

### 2.2 Story Impact
- **KHÔNG có story nào bị add/remove ở tầng requirements.**
- **KHÔNG có story nào đang done/in-progress bị reopen.**
- Tracking-only changes: rename slug 2-2 và 3-4, xóa entry lỗi 3-4-generative-*, thêm entry 6-1.

### 2.3 Artifact Conflicts
| Artifact | Conflict | Resolution |
|----------|----------|------------|
| `prd.md` | Không có conflict thực; FR3/FR7 và FR4/FR8 chỉ ambiguous về trách nhiệm mapping. | Giữ nguyên PRD; clarify trong epics.md FR Coverage Map (FR3+FR7 consolidated trong Story 3.1; FR4 Phase 1 và FR8 Phase 2 cùng Story 3.2 / graph schema). |
| `architecture.md` | Thiếu design cho 8 FR. | Thêm Section 6 (XAI), 7 (ECharts Payload), 8 (Verified PDF + Marketplace), 9 (Priority Queue + Admin Observability), 10 (Copilot Sandbox), 11 (WFA). Refresh Section 5 FR mapping. |
| `epics.md` | FR Coverage Map sai + cross-cutting không trace. | Fix Map (FR4→Epic 3, FR5→Stories 4.2+4.3), đánh dấu FR3+FR7 consolidated, FR8 Phase 2 của Story 3.2. Thêm trace Symbol Normalization→Story 1.2, Data Resilience→Story 2.2. Điều chỉnh "FRs covered" của Epic 2 (bỏ FR4) và Epic 3 (thêm FR4). |
| `sprint-status.yaml` | Thiếu Epic 6, slug sai. | Rename 2-2, rename 3-4 (từ 3-5-walk-forward-analysis-wfa), xóa 3-4-generative-strategy-copilot-p2, thêm epic-6 + 6-1-generative-strategy-copilot. |
| `sprint-status.md` | Dashboard lệch với reality (count cũ = 5 epics, 15 stories, 0 completed). | Rewrite dashboard thành 6 epics, 19 stories, Epic 1+2 done, Epic 3 in-progress. |
| File `2-2-multi-market-data-loading-system.md` | Tên file lệch story name. | `git mv` → `2-2-crypto-first-data-loading-system.md`. Update `story_key` trong frontmatter. Update reference trong `deferred-work.md`. |

### 2.4 Technical / Code Impact
**KHÔNG** — scope hoàn toàn nằm trong planning artifacts. Source code trong `agent/` và `docs/` không chạm. Tất cả implementation của Epic 1-2 đã phù hợp với planning mới (rename chỉ là naming hygiene, không đổi behavior).

## 3. Recommended Approach

**Selected path: Option 1 — Direct Adjustment**

- **Effort:** Low-Medium (sync documents, ~30 phút editing + review).
- **Risk:** Low. Không đụng code, không đụng story done/in-progress.
- **Timeline impact:** Zero — các edit hoàn thành trước khi tạo story 3.2/3.3/3.4, không chặn sprint đang chạy.

**Lý do chọn:**
- Gap thuộc về **documentation drift** và **tracking sync**, không phải thay đổi requirements hoặc architecture fundamentals.
- Rollback (Option 2) không áp dụng — không có code nào cần revert.
- MVP Review (Option 3) dư thừa — PRD giữ nguyên, Phase 1 crypto-only vẫn đúng intent.

## 4. Detailed Change Proposals (Applied)

### 4.1 `architecture.md` (5 sections → 11 sections)

Đã thêm:
- **Section 6 — Explainable AI (XAI) Narrative Engine (FR9):** trace schema `xai_trace.json`, LLM prompt template với citation guard, confidence derived from WFA decay.
- **Section 7 — Interactive Multi-Chart Payload (FR10):** `ChartPayload` schema (candles/equity_curve/trade_markers/overlays), Decimal-as-string precision rule, LTTB downsampling.
- **Section 8 — Verified PDF + Marketplace (FR11, FR12):** SHA-256 + Ed25519 signing chain, revocation flag, ownership model, publish snapshot API, protection cho `executable_code`.
- **Section 9 — Priority Queue + Admin Observability (FR13, FR14):** queue topology (premium/standard), JWT-based routing, worker reservation, fairness token-bucket, `/admin/stats` schema, alert rules, separate `VT_ADMIN_KEY`.
- **Section 10 — Copilot Sandbox (FR16):** Docker read-only + cgroups, RestrictedPython + PineScript AST, `/tmp/run` tmpfs, static analysis + dry-run + watchdog, security event logging.
- **Section 11 — Walk-Forward Analysis (FR19):** window generator (rolling/anchored), per-window train/test loop, aggregation metrics, overfit warning gate, parallel Celery chord execution.
- Refresh **Section 5 FR Mapping** để link sang các section mới.

### 4.2 `epics.md`

- **Additional Requirements:** bổ sung trace note cho Symbol Normalization (→ Story 1.2) và Data Resilience (→ Story 2.2).
- **FR Coverage Map** (re-written):
  - FR3 + FR7 → Story 3.1 consolidated.
  - FR4 → Story 3.2 (Phase 1 crypto-focused).
  - FR8 → Story 3.2 (Phase 2 macro expansion, same graph schema).
  - FR5 → Stories 4.2 + 4.3.
  - Mọi FR còn lại point chính xác về `Epic.Story`.
- **Epic List:**
  - Epic 2 "FRs covered" bỏ FR4 (không thuộc Epic 2).
  - Epic 3 "FRs covered" thêm FR4.

### 4.3 `sprint-status.yaml`

- `2-2-multi-market-data-loading-system` → `2-2-crypto-first-data-loading-system`.
- `3-4-generative-strategy-copilot-p2`: **removed**.
- `3-5-walk-forward-analysis-wfa` → `3-4-walk-forward-analysis-wfa`.
- Thêm block `epic-6: backlog` + `6-1-generative-strategy-copilot: backlog` + `epic-6-retrospective: optional`.

### 4.4 `sprint-status.md` (dashboard)

Rewrite sang 6 epics / 19 stories, reflect Epic 1+2 done, Story 3.1 in-progress, Epic 6 backlog mới xuất hiện.

### 4.5 Implementation artifact rename

- `git mv _bmad-output/implementation-artifacts/2-2-multi-market-data-loading-system.md → 2-2-crypto-first-data-loading-system.md`.
- Update frontmatter `story_key` trong file đó.
- Update reference trong `_bmad-output/implementation-artifacts/deferred-work.md`.

## 5. MVP Impact & Action Plan

**MVP Impact:** Không. Phase 1 Crypto-Native scope và Success Criteria trong PRD không đổi.

**Action items trước khi tiếp tục Epic 3:**
1. ✅ Cập nhật `architecture.md` — done.
2. ✅ Cập nhật `epics.md` — done.
3. ✅ Cập nhật `sprint-status.yaml` + `sprint-status.md` — done.
4. ✅ Rename implementation artifact + fix references — done.
5. **Next step (user action):** tạo Story 3.2 bằng `/bmad-create-story` với context FR4 (Phase 1 crypto-focused, FR8 Phase 2 defer same story or split).
6. **Recommended:** chạy `/bmad-check-implementation-readiness` sau merge để verify planning artifact consistency mới.

## 6. Agent Handoff Plan

| Role | Responsibility | Deliverable |
|------|----------------|-------------|
| **Product Owner / Scrum Master (Luisphan)** | Review + merge proposal; approve tiếp tục Epic 3. | Merge commit các planning artifact. |
| **Dev Agent (Amelia / `/bmad-dev-story`)** | Consume updated `architecture.md` khi triển khai Story 3.2, 3.3, 3.4, Epic 4-6. | Source code tuân theo Section 6-11 mới. |
| **Scrum Master (Bob / `/bmad-create-story`)** | Tạo Story 3.2 tiếp theo với FR Coverage Map đã fix. | File `3-2-knowledge-graph-integration-news-to-asset.md`. |
| **Architect (Winston)** | (Optional) Review Section 6-11 để confirm design không conflict ngầm. | Architecture sign-off. |

**Success criteria cho handoff:**
- `architecture.md` có 11 sections và cover 19 FR.
- `epics.md` FR Coverage Map consistent 100% với `prd.md`.
- `sprint-status.yaml` reflect 6 epics / 19 stories, trạng thái Epic 1-2 done / Epic 3 in-progress / Epic 4-6 backlog.
- Không file story nào có slug không khớp `sprint-status.yaml`.

## 7. Scope Classification

**Moderate** — yêu cầu backlog reorganization ở cấp tracking (add Epic 6, rename slug) và architecture expansion (Section 6-11). Không đạt mức Major vì không có replan strategic.

---

**Approved by:** Luisphan (confirmed via incremental approval flow during session 2026-05-10)
**Applied by:** BMad Correct Course workflow
**Commit path suggested:** `chore(planning): sync planning artifacts (architecture sections 6-11, epics FR map, sprint status)`
