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
Nowing hướng tới trở thành **Siêu trợ lý AI "All-in-one"** cho nhà đầu tư tài chính chuyên nghiệp. Dự án thực hiện tích hợp sâu Vibe-Trading vào hệ sinh thái Nowing nhằm triệt tiêu rào cản kỹ thuật trong phân tích định lượng. Người dùng có thể chuyển hóa ý tưởng giao dịch từ ngôn ngữ tự nhiên thành báo cáo backtest chi tiết mà không cần kiến thức lập trình.

### Strategic Differentiator: "Zero-Technical Friction"
Nowing đóng vai trò "Bộ não" điều hành, phối hợp với "Cánh tay thực thi" Vibe-Trading để tự động hóa toàn trình: bóc tách dữ liệu, viết mã chiến lược, chạy backtest và trình bày kết quả. Điểm đột phá nằm ở khả năng **tự tiến hóa chiến lược (RL)** và **gợi ý chủ động (Knowledge Graph)** ngay trong luồng chat.

## Success Criteria
*   **User Success:** 100% bước xác nhận chiến lược qua Visual Cards; Phản hồi AI ban đầu < 5 giây; Tỷ lệ hiểu lệnh đúng ngay lần đầu > 80%.
*   **Business Success:** Đạt 40% adoption trong tháng đầu; Tăng 15% tỷ lệ chuyển đổi gói Premium; Priority Queue cho người dùng trả phí (< 5 giây chờ).
*   **Technical Success:** API Reliability > 99%; Cache Hit Rate > 70% (L1/L2 caching); Sai lệch dữ liệu thực thi và hiển thị bằng 0.

## Project Scoping (Unified Release)
Dự án triển khai theo mô hình "Big Bang", ra mắt toàn bộ các tính năng trong một lần duy nhất:
*   **Core:** Backtest VN, US, Crypto (2 năm dữ liệu); Strategy Preview Card.
*   **AI Brain:** Offline Reinforcement Learning (Strategy Tuning); Proactive Knowledge Graph (News-to-Asset).
*   **Ecosystem:** Strategy Marketplace; Shadow Account PDF Reports.
*   **Ops:** Redis/Celery Task Queue; Auto-scaling Workers; IP Whitelisting.

## User Journeys
1.  **Alex (Happy Path):** Ra lệnh backtest RSI BTC -> Xác nhận Visual Card -> Nhận kết quả sau 15 giây.
2.  **Alex (Recovery):** Câu lệnh mơ hồ -> AI gợi ý chiến lược MA/RSI mẫu -> Chạy thành công.
3.  **Minh (Admin):** Theo dõi Latency/Cache Dashboard -> Phát hiện nghẽn dữ liệu -> Kích hoạt Fail-over.

## Domain-Specific Requirements
*   **Compliance:** Tự động gắn Disclaimer tài chính; Mã hóa AES-256 cho chiến lược lưu trữ.
*   **Precision:** Sử dụng Decimal (6 chữ số thập phân) cho mọi tính toán PnL.
*   **Resilience:** Cơ chế fallback tự động giữa yfinance, akshare và ccxt.

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

## Non-Functional Requirements
*   **Performance:** API Latency < 500ms; Tốc độ xử lý backtest 2 năm < 30 giây.
*   **Security:** 100% giao tiếp qua TLS/SSL; IP Whitelisting chỉ nhận traffic từ Nowing Backend.
*   **Reliability:** Uptime 99.9%; Hàng đợi Redis bền vững không mất task khi worker sập.
*   **Scalability:** Tự động mở rộng instance khi hàng đợi > 10 jobs.
