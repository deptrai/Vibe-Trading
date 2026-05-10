---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish']
inputDocuments: ['_bmad-output/project-context.md', 'README.md']
documentCounts: {
  briefCount: 0,
  researchCount: 0,
  brainstormingCount: 0,
  projectDocsCount: 2
}
classification:
  projectType: 'saas_b2b'
  domain: 'fintech'
  complexity: 'high'
  projectContext: 'brownfield'
releaseMode: 'single-release'
workflowType: 'prd'
---

# Product Requirements Document - Vibe-Trading Integration (Nowing)

**Author:** Luisphan
**Date:** 2026-05-05

## Executive Summary
Nowing hướng tới trở thành **Siêu trợ lý AI Crypto-Native** cho nhà đầu tư tiền mã hóa và DeFi chuyên nghiệp. Dự án tích hợp sâu Vibe-Trading vào hệ sinh thái Nowing nhằm tối ưu hóa các chiến lược giao dịch, phân tích thanh khoản, và mô phỏng Perpetual Futures/AMM. Người dùng có thể chuyển hóa ý tưởng giao dịch crypto phức tạp thành báo cáo backtest chi tiết mà không cần kiến thức lập trình.

### Strategic Differentiator: "DeFi-Native & Zero-Technical Friction"
Nowing đóng vai trò "Bộ não", phối hợp với "Cánh tay thực thi" Vibe-Trading để tự động hóa toàn trình: bóc tách dữ liệu thị trường Crypto, xử lý mô phỏng trượt giá/thanh khoản phi tập trung, chạy backtest và trình bày kết quả. Điểm đột phá nằm ở khả năng **mô phỏng chính xác môi trường DeFi/Perps (Gas, Funding Rates)** và **tự tiến hóa chiến lược (RL)** ngay trong luồng chat.

## Success Criteria
*   **User Success:** 100% bước xác nhận chiến lược qua Visual Cards; Phản hồi AI ban đầu < 5 giây; Tỷ lệ hiểu lệnh đúng ngay lần đầu > 80%.
*   **Business Success:** Đạt 40% adoption trong tháng đầu; Tăng 15% tỷ lệ chuyển đổi gói Premium; Priority Queue cho người dùng trả phí (< 5 giây chờ).
*   **Technical Success:** API Reliability > 99%; Cache Hit Rate > 70% (L1/L2 caching); Sai lệch dữ liệu thực thi và hiển thị bằng 0.

## Project Scoping (Phased Release)
Dự án triển khai theo lộ trình từng giai đoạn (Phased Rollout) để tối ưu hóa nguồn lực:
**Phase 1: Crypto-Native Focus (Current)**
*   **Core:** Backtest chuyên biệt Crypto (Spot, Perpetual, On-chain data - 2 năm dữ liệu); Strategy Preview Card.
*   **AI Brain:** Offline Reinforcement Learning (Strategy Tuning); Proactive Knowledge Graph (Crypto News & On-chain Events).

**Phase 2: Multi-Market Expansion (Future)**
*   **Core:** Mở rộng hỗ trợ thị trường chứng khoán truyền thống (VN, US Stocks).
*   **AI Brain:** Mở rộng Knowledge Graph sang tài chính vĩ mô và tin tức doanh nghiệp.
*   **Ecosystem:** Strategy Marketplace; Shadow Account PDF Reports.
*   **Ops:** Redis/Celery Task Queue; Auto-scaling Workers; IP Whitelisting.

## User Journeys
1.  **Alex (Happy Path):** Ra lệnh backtest chiến lược Arbitrage DEX/CEX cho ETH -> Xác nhận Visual Card -> Hệ thống mô phỏng (tính cả Gas/Slippage) -> Nhận kết quả sau 15 giây.
2.  **Alex (Recovery):** Câu lệnh mơ hồ -> AI gợi ý chiến lược MA/RSI mẫu -> Chạy thành công.
3.  **Minh (Admin):** Theo dõi Latency/Cache Dashboard -> Phát hiện nghẽn dữ liệu -> Kích hoạt Fail-over.

## Domain-Specific Requirements
*   **Compliance:** Tự động gắn Disclaimer tài chính; Mã hóa AES-256 cho chiến lược lưu trữ.
*   **Precision:** Sử dụng Decimal (6 chữ số thập phân) cho mọi tính toán PnL.
*   **Resilience:** Thiết kế kiến trúc data loader mở. Phase 1 ưu tiên `ccxt` làm nòng cốt và tích hợp On-chain RPC nodes cho Crypto. Phase 2 sẽ tái kích hoạt `yfinance` và `akshare` làm fallback cho chứng khoán.

## Internal Service Specific Requirements (Vibe-Trading)
*   **Hybrid State:** Nowing giữ "Source of Truth"; Vibe-Trading giữ "Execution Cache".
*   **Shared Persistence:** Dùng Shared File System (EFS/NFS) cho thư mục `runs/`.
*   **Retention:** Tự động dọn dẹp artifact sau 7 ngày hoặc khi đĩa đầy 80%.
*   **Resource Quotas:** Giới hạn RAM/CPU nghiêm ngặt qua Docker cgroups per instance.

## Functional Requirements
*   **FR1:** Bóc tách tham số (Symbol, Indicator, Timeframe) từ Natural Language.
*   **FR2:** Hiển thị Strategy Preview Card khi Confidence Score < 0.9.
*   **FR3:** Tính năng "Optimize Strategy" tự động tìm tham số tối ưu qua RL.
*   **FR4:** Tự động phát hiện sự kiện tin tức và đề xuất mã tài sản từ Knowledge Graph.
*   **FR5:** Xuất báo cáo PDF "Verified Data" và Publish lên Marketplace.
*   **FR6:** Giới hạn xử lý dữ liệu backtest tối đa 2 năm để đảm bảo hiệu suất.
*   **FR7:** Tối ưu hóa tham số chiến lược tự động qua Offline Reinforcement Learning.
*   **FR8:** Tích hợp Knowledge Graph để ánh xạ sự kiện tin tức vĩ mô sang mã tài sản.
*   **FR9:** Explainable AI (XAI) - Giải thích bằng ngôn ngữ tự nhiên lý do AI thay đổi tham số chiến lược.
*   **FR10:** Hiển thị biểu đồ tương tác (Interactive Multi-Chart) cho Equity Curve và Candlesticks.
*   **FR11:** Cung cấp tính năng "Verified Data" PDF Report (Shadow Account).
*   **FR12:** Tính năng Social Marketplace cho phép đăng tải, tìm kiếm và khám phá chiến lược.
*   **FR13:** Hàng đợi tác vụ ưu tiên (Tiered Priority Queue) dành riêng cho Premium Users.
*   **FR14:** Admin Monitoring Dashboard để theo dõi API Latency, Cache Hit Rates và Active Workers.
*   **FR15:** Monte Carlo Stress Test - mô phỏng trượt giá/thiệt hại để đo rủi ro "Thiên nga đen".
*   **FR16:** Generative Strategy Copilot - Tự động viết mã Python/PineScript dựa trên yêu cầu ngôn ngữ tự nhiên.
*   **FR17:** DeFi-Native Simulator - Mô phỏng chi phí Gas, thanh khoản AMM và Impermanent Loss cho chiến lược Crypto.
*   **FR18:** Perpetual Futures Engine - Mô phỏng Funding Rates, Margin (Cross/Isolated), và cơ chế Liquidations.
*   **FR19:** Walk-Forward Analysis (WFA) - Cơ chế chia dữ liệu In-sample/Out-of-sample để kiểm thử độ bền bỉ của chiến lược.

## Non-Functional Requirements
*   **Performance:** API Latency < 500ms; Tốc độ xử lý backtest 2 năm < 30 giây.
*   **Security:** 100% giao tiếp qua TLS/SSL; IP Whitelisting chỉ nhận traffic từ Nowing Backend.
*   **Reliability:** Uptime 99.9%; Hàng đợi Redis bền vững không mất task khi worker sập.
*   **Scalability:** Tự động mở rộng instance khi hàng đợi > 10 jobs.
