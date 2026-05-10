import json
from fastapi.testclient import TestClient
from agent.api_server import app, _is_local_client

# Mock authentication so we focus only on payload validation
import agent.api_server as api_server
api_server._is_local_client = lambda r: True
api_server._API_KEY = ""

client = TestClient(app)

print("="*60)
print("🧪 BẮT ĐẦU KIỂM CHỨNG API ENDPOINT /jobs")
print("="*60)

# 1. TEST HỢP LỆ
print("\n[TEST 1] Gửi payload hoàn toàn hợp lệ...")
valid_payload = {
    "simulation_environment": {
        "exchange": "binance",
        "instrument_type": "SPOT",
        "initial_capital": "15000",
        "historical_range": 365
    },
    "risk_management": {
        "max_drawdown_percentage": "0.15",
        "position_sizing": "0.2"
    },
    "context_rules": {
        "assets": ["BTC-USDT", "ETH-USDT"],
        "timeframe": "4h"
    },
    "execution_flags": {
        "enable_monte_carlo_stress_test": True
    }
}
response = client.post("/jobs", json=valid_payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
print("✅ Thành công!" if response.status_code == 200 else "❌ Thất bại!")


# 2. TEST LỖI LOGIC: SPOT nhưng dùng đòn bẩy
print("\n[TEST 2] Cố tình dùng đòn bẩy (Leverage = 10) cho giao dịch SPOT...")
spot_leverage_payload = valid_payload.copy()
spot_leverage_payload["risk_management"] = {
    "max_drawdown_percentage": "0.15",
    "position_sizing": "0.2",
    "leverage": "10.0" # Invalid for SPOT
}
response = client.post("/jobs", json=spot_leverage_payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
print("✅ Pydantic đã chặn đúng lỗi logic!" if response.status_code == 422 else "❌ Pydantic chặn sai!")


# 3. TEST LỖI FORMAT: Khung thời gian (Timeframe) sai định dạng
print("\n[TEST 3] Nhập sai định dạng timeframe (VD: '1century' thay vì '1h', '1d')...")
bad_timeframe_payload = valid_payload.copy()
bad_timeframe_payload["risk_management"] = {
    "max_drawdown_percentage": "0.15",
    "position_sizing": "0.2"
}
bad_timeframe_payload["context_rules"] = {
    "assets": ["BTC-USDT"],
    "timeframe": "1century" # Invalid regex
}
response = client.post("/jobs", json=bad_timeframe_payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
print("✅ Pydantic Regex đã chặn đúng!" if response.status_code == 422 else "❌ Pydantic chặn sai!")


# 4. TEST LỖI DỮ LIỆU: Thiếu tham số bắt buộc
print("\n[TEST 4] Gửi thiếu tham số bắt buộc (Thiếu danh sách assets)...")
missing_assets_payload = valid_payload.copy()
missing_assets_payload["context_rules"] = {
    "timeframe": "1h"
    # Thiếu assets
}
response = client.post("/jobs", json=missing_assets_payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
print("✅ Pydantic Required Field đã chặn đúng!" if response.status_code == 422 else "❌ Pydantic chặn sai!")

print("\n" + "="*60)
print("🎉 KIỂM CHỨNG HOÀN TẤT")
print("="*60)
