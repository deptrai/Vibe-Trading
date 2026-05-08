---
stepsCompleted: ['step-01-preflight-and-context', 'step-02-identify-targets']
lastStep: 'step-02-identify-targets'
lastSaved: '2026-05-08'
inputDocuments:
  - '_bmad-output/project-context.md'
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
  - '_bmad-output/planning-artifacts/epics.md'
  - '_bmad-output/implementation-artifacts/1-1-secure-service-to-service-bridge.md'
  - 'agent/tests/conftest.py'
  - 'agent/tests/'
  - 'playwright-utils: core'
---

# Test Automation Expansion Summary - Vibe-Trading

## Step 1: Preflight & Context Loading
... (Giữ nguyên nội dung cũ)

## Step 2: Identify Automation Targets

### Target Mapping (BMad-Integrated)
Dựa trên Epics và Stories, các mục tiêu kiểm thử trọng tâm bao gồm:

1.  **Secure Service Bridge (Story 1.1)**: Kiểm tra xác thực Bearer Token và Whitelisting IP tại `agent/api_server.py`.
2.  **Standardized Payload Schema (Story 1.2)**: Xác thực tính đúng đắn của dữ liệu sau khi NLP bóc tách.
3.  **Multi-Market Loaders (Story 2.2)**: Kiểm tra khả năng lấy dữ liệu và cơ chế fallback (AkShare, yfinance, CCXT).
4.  **Async Job Queue (Story 2.1)**: Kiểm tra độ tin cậy của hàng đợi Redis/Celery.

### Coverage Plan

| Mục tiêu (Target) | Cấp độ (Level) | Ưu tiên (Priority) | Lý do (Justification) |
| :--- | :--- | :--- | :--- |
| **Security Bridge** | API / Integration | P0 | Bảo mật hệ thống là bắt buộc (Mandate). |
| **Session API (`/sessions`)** | API | P0 | Luồng khởi đầu quan trọng cho mọi tương tác người dùng. |
| **Data Loaders (Mocked)** | Unit | P1 | Đảm bảo tính ổn định khi lấy dữ liệu từ các thị trường khác nhau. |
| **Payload Validation** | Unit | P1 | Tránh lỗi dữ liệu trôi nổi (FR1). |
| **Backtest Runner** | Integration | P0 | Chức năng cốt lõi của Vibe-Trading. |
| **Health Endpoint** | API | P0 | Kiểm tra tính sẵn sàng của hệ thống. |

### Justification
Kế hoạch tập trung vào **đường dẫn tới hạn (Critical Paths)** và **bảo mật (Security)** trước tiên để đảm bảo hệ thống có thể tích hợp an toàn vào Nowing. Các tính năng nâng cao như RL và Knowledge Graph sẽ được mở rộng ở các bước tiếp theo.
