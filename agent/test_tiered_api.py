import os
import jwt
import requests
import json
import time

API_URL = "http://127.0.0.1:8000/jobs"
JWT_SECRET = os.environ.get("JWT_SECRET", "test_secret_for_local_dev")

def generate_token(tier="standard"):
    """Tạo JWT token fake tương ứng với tier (premium hoặc standard)"""
    payload = {
        "sub": "user123",
        "user_tier": tier,
        "exp": int(time.time()) + 3600
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token

def create_payload(enable_rl=False):
    """Tạo một payload thật hợp lệ để gửi cho API"""
    return {
        "context_rules": {
            "timeframe": "1d",
            "assets": ["ETH/USDT", "BTC/USDT"]
        },
        "simulation_environment": {
            "historical_range": 30,
            "exchange": "binance",
            "instrument_type": "SPOT",
            "initial_capital": 10000.0
        },
        "risk_management": {
            "max_drawdown_percentage": 0.2,
            "position_sizing": 0.1,
            "leverage": 1.0
        },
        "execution_flags": {
            "enable_monte_carlo_stress_test": False,
            "enable_rl_optimization": enable_rl
        }
    }

def send_request(tier, enable_rl=False):
    """Gửi request lên API với token tương ứng"""
    print(f"\n--- GỬI REQUEST VỚI TIER: {tier.upper()} | RL_OPTIMIZATION: {enable_rl} ---")
    token = generate_token(tier)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = create_payload(enable_rl)
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
    except requests.exceptions.ConnectionError:
        print(f"❌ LỖI KẾT NỐI: Không thể kết nối tới {API_URL}.")
        print("Vui lòng đảm bảo bạn đã khởi động API server: 'uvicorn agent.api_server:app --port 8000'")

if __name__ == "__main__":
    print("Bắt đầu test API Phân cấp hàng đợi (Tiered Priority Queue)...")
    
    # Test 1: Premium Backtest
    send_request("premium", enable_rl=False)
    
    # Test 2: Standard Backtest
    send_request("standard", enable_rl=False)
    
    # Test 3: Premium RL Optimization
    send_request("premium", enable_rl=True)
