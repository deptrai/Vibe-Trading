import pytest
import pandas as pd
import numpy as np
from src.monte_carlo import MonteCarloSimulator

def test_monte_carlo_empty_returns():
    mc = MonteCarloSimulator(iterations=100)
    result = mc.run_simulation(pd.Series(dtype=float))
    
    assert result["status"] == "skipped"
    assert "error" in result

def test_monte_carlo_success():
    mc = MonteCarloSimulator(iterations=1000)
    # Simulate a strategy with small positive expectation
    np.random.seed(42)
    returns = np.random.normal(loc=0.001, scale=0.01, size=100)
    trade_returns = pd.Series(returns)
    
    initial_cap = 1000.0
    result = mc.run_simulation(trade_returns, initial_capital=initial_cap)
    
    assert result["status"] == "success"
    assert result["iterations"] == 1000
    
    metrics = result["metrics"]
    assert "max_drawdown_95_ci" in metrics
    assert "risk_of_ruin_probability" in metrics
    assert "final_capital" in metrics
    
    # Check types and basic bounds
    assert 0.0 <= metrics["max_drawdown_95_ci"] <= 1.0
    assert 0.0 <= metrics["risk_of_ruin_probability"] <= 1.0
    assert metrics["final_capital"]["mean"] > 0
    assert metrics["final_capital"]["95th_percentile"] >= metrics["final_capital"]["5th_percentile"]

def test_monte_carlo_risk_of_ruin():
    mc = MonteCarloSimulator(iterations=1000, risk_of_ruin_threshold=0.8)
    # Simulate a terrible strategy
    returns = np.array([-0.1, -0.1, -0.1, -0.1])
    trade_returns = pd.Series(returns)
    
    result = mc.run_simulation(trade_returns, initial_capital=100.0)
    
    # 4 losses of 10% each -> equity drops to 100 * 0.9^4 = 65.61
    # Threshold is 0.8 * 100 = 80. Since 65.61 < 80, all paths should hit ruin.
    metrics = result["metrics"]
    assert metrics["risk_of_ruin_probability"] == 1.0
