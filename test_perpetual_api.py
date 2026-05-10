import os
import json
from datetime import datetime
import pandas as pd

import agent.api_server as api_server
from agent.src.worker import run_backtest_job

# Mute warnings from pydantic/fastapi if any
import warnings
warnings.filterwarnings('ignore')

print("="*60)
print("🚀 BẮT ĐẦU TEST PERPETUAL FUTURES VỚI DỮ LIỆU THẬT")
print("="*60)

payload = {
    "simulation_environment": {
        "exchange": "binance",
        "instrument_type": "PERPETUAL",
        "initial_capital": "1000",
        "historical_range": 30
    },
    "risk_management": {
        "max_drawdown_percentage": "0.15",
        "position_sizing": "1.0",
        "leverage": "50.0" 
    },
    "context_rules": {
        "assets": ["BTC/USDT"], # Sử dụng định dạng có slash để CCXT dễ nhận diện
        "timeframe": "1h"
    },
    "execution_flags": {
        "enable_monte_carlo_stress_test": True
    }
}

print(f"📦 Đang tạo job với đòn bẩy 50x cho BTC/USDT trong 30 ngày qua...\n")

# Call the unwrapped function directly to run synchronously for testing
worker_func = getattr(run_backtest_job, '__wrapped__', run_backtest_job)
if hasattr(worker_func, '__func__'):
    worker_func = worker_func.__func__

class MockSelf:
    class Request:
        id = f"test_perp_job_{int(datetime.now().timestamp())}"
    request = Request()

try:
    print("⏳ Đang fetch dữ liệu thật từ Binance qua CCXT và chạy mô phỏng Perpetual...\n")
    result = worker_func(MockSelf(), payload)
    
    print(f"✅ Job hoàn thành! Status: {result['status']}")
    print(f"📁 Dữ liệu được lưu tại thư mục: runs/{MockSelf.request.id}/")
    
    # Kiểm tra xem có sinh ra liquidation_events không
    job_dir = os.path.join(os.environ.get("RUNS_DIR", "/tmp/vibe-trading/runs"), MockSelf.request.id)
    mc_path = os.path.join(job_dir, "BTC_USDT_monte_carlo.json")
    
    if os.path.exists(mc_path):
        with open(mc_path, 'r') as f:
            mc_data = json.load(f)
            
        liquidations = mc_data.get("liquidation_events", [])
        funding = mc_data.get("total_funding_fees", 0)
        
        print("\n📊 BÁO CÁO KẾT QUẢ MÔ PHỎNG PERPETUAL (50x Leverage):")
        print(f"   - Tổng số sự kiện thanh lý (Cháy tài khoản): {len(liquidations)}")
        print(f"   - Tổng chi phí/nhận được từ Funding Rate: {funding:.2f} USD")
        
        if liquidations:
            print(f"   🔥 Ví dụ 3 lần thanh lý đầu tiên:")
            for idx, event in enumerate(liquidations[:3]):
                print(f"      [{idx+1}] Thời gian: {event['timestamp']} | Vị thế: {event['position']} | Giá: {event['mark_price']:.2f}")
    else:
        print(f"\n⚠️ Không tìm thấy file kết quả tại {mc_path}. Vui lòng kiểm tra lại log.")

except Exception as e:
    print(f"\n❌ Có lỗi xảy ra trong quá trình chạy: {str(e)}")
