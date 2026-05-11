import pytest
import os
from pathlib import Path
from src.worker import run_backtest_job

@pytest.fixture
def mock_payload():
    return {
        "context_rules": {
            "assets": ["BTC-USDT"],
            "timeframe": "1d",
            "natural_language_rules": "Buy when price crosses above SMA 20, sell when price crosses below SMA 20",
            "executable_code": ""
        },
        "simulation_environment": {
            "exchange": "binance",
            "historical_range": 30,
            "instrument_type": "SPOT",
            "initial_capital": 10000.0
        },
        "risk_management": {
            "leverage": 1.0,
            "max_drawdown_percentage": 0.2
        },
        "execution_flags": {
            "enable_monte_carlo_stress_test": True
        }
    }

def test_headless_e2e_nl_to_code(mock_payload, tmp_path, monkeypatch):
    """Test full headless E2E flow: NL -> Code -> Execution -> Metrics."""
    # Mock RUNS_DIR to a temporary path
    monkeypatch.setenv("RUNS_DIR", str(tmp_path))
    
    # We will mock AgentLoop to prevent actual LLM call and just write a dummy signal_engine.py
    class MockAgentLoop:
        def __init__(self, *args, **kwargs):
            pass
        def run_headless(self, rules, run_dir):
            strategy_path = run_dir / "code" / "signal_engine.py"
            strategy_path.parent.mkdir(parents=True, exist_ok=True)
            with open(strategy_path, "w") as f:
                f.write("class SignalEngine:\\n    pass\\n")
            return {"status": "success", "run_dir": str(run_dir)}

    monkeypatch.setattr("src.agent.loop.AgentLoop", MockAgentLoop)

    # We also mock subprocess.run so we don't actually run the engine, 
    # but we will create the fake artifacts/equity.csv instead.
    import subprocess
    original_run = subprocess.run
    def mock_subprocess_run(cmd, *args, **kwargs):
        if "backtest.runner" in cmd:
            job_dir = Path(cmd[-1])
            artifacts = job_dir / "artifacts"
            artifacts.mkdir(parents=True, exist_ok=True)
            with open(artifacts / "equity.csv", "w") as f:
                f.write("Date,equity\n2023-01-01,10000\n2023-01-02,10100\n")
            
            # Return a mock subprocess.CompletedProcess
            import subprocess
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="Mock engine success", stderr="")
        return original_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    class MockTaskRequest:
        id = "test-headless-job-123"

    # We use .apply() to run the Celery task synchronously
    result_obj = run_backtest_job.apply(args=(mock_payload,), task_id="test-headless-job-123")
    result = result_obj.result
    
    assert result["status"] == "success"
    assert result["job_id"] == "test-headless-job-123"
    
    job_dir = tmp_path / "test-headless-job-123"
    assert (job_dir / "code" / "signal_engine.py").exists()
    assert (job_dir / "config.json").exists()
    assert (job_dir / "metadata.json").exists()
    
    # Check Monte Carlo results
    assert "BTC-USDT" in result["data_summary"]
    assert "monte_carlo" in result["data_summary"]["BTC-USDT"]
