# Story 3.1: Offline RL Strategy Tuner - Completed

## Quyết định kiến trúc & Gotchas:
- **Optuna Integration**: Đã tích hợp thành công Optuna để thực hiện Reinforcement Learning-based offline optimization cho Vibe-Trading. Sử dụng `Decimal` để đảm bảo độ chính xác (precision) cao nhất cho các phép tính tài chính.
- **Celery Worker**: Task `run_rl_optimization_job` được route tới queue riêng biệt `rl_optimization`. Cấu hình resource guardrails bằng `psutil` để ngắt khi memory < 500MB, và áp dụng soft_time_limit (30 mins). Đã configure rõ queue trong `docker-compose.yml`.
- **Testing Celery Tasks with `bind=True`**: Celery decorator bind task methods thành `bound method` khi dùng `__wrapped__`. Trong Unit tests (pytest), để mock và chạy trực tiếp, phải gọi qua `__wrapped__.__func__(mock_self, payload)`. Tránh lỗi "takes 2 positional arguments but 3 were given".
- **Schema Validation**: Khi test payload, chú ý `rl_max_trials` đã được enforce minimum giá trị là 10 (`ge=10`) qua Pydantic schema nên test payloads cũ sẽ fail nếu config sai.