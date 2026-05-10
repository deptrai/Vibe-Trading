import numpy as np
import pandas as pd
from typing import Dict, Any

class MonteCarloSimulator:
    """
    Monte Carlo Stress Test Engine.
    Runs 10,000+ resampled paths on historical trade series to calculate risk metrics.
    """
    
    def __init__(self, iterations: int = 10000, risk_of_ruin_threshold: float = 0.5):
        """
        Args:
            iterations: Number of resampled paths to generate.
            risk_of_ruin_threshold: The fraction of initial capital considered as "ruin". 
                                   E.g., 0.5 means losing 50% of the initial capital.
        """
        self.iterations = max(1, iterations)
        self.risk_of_ruin_threshold = risk_of_ruin_threshold

    def run_simulation(self, trade_returns: pd.Series, initial_capital: float = 10000.0) -> Dict[str, Any]:
        """
        Runs the Monte Carlo simulation.
        
        Args:
            trade_returns: A pandas Series of trade returns (e.g., 0.05 for 5% gain).
            initial_capital: The starting capital for the simulation.
            
        Returns:
            A dictionary containing the calculated metrics.
        """
        if trade_returns is None or len(trade_returns) == 0:
            return {
                "error": "No trade returns provided for simulation.",
                "status": "skipped"
            }
            
        returns_array = trade_returns.replace([np.inf, -np.inf], np.nan).dropna().values.astype(np.float64)
        if len(returns_array) == 0:
            return {
                "error": "No valid trade returns after cleaning.",
                "status": "skipped"
            }
            
        n_trades = len(returns_array)
        
        # Batch simulation to prevent OOM
        BATCH_SIZE = 1000
        n_batches = int(np.ceil(self.iterations / BATCH_SIZE))
        
        final_capitals_list = []
        max_drawdowns_list = []
        ruin_events_list = []
        
        for _ in range(n_batches):
            current_batch = min(BATCH_SIZE, self.iterations - len(final_capitals_list))
            simulated_returns = np.random.choice(returns_array, size=(current_batch, n_trades), replace=True)
            
            # Floor multipliers at 0 to prevent negative equity
            multipliers = np.maximum(1.0 + simulated_returns, 0.0)
            equity_paths = initial_capital * np.cumprod(multipliers, axis=1)
            
            final_capitals_list.extend(equity_paths[:, -1])
            
            running_max = np.maximum.accumulate(equity_paths, axis=1)
            running_max = np.where(running_max == 0, 1e-9, running_max)
            drawdowns = (running_max - equity_paths) / running_max
            max_drawdowns_list.extend(np.max(drawdowns, axis=1))
            
            ruin_level = initial_capital * self.risk_of_ruin_threshold
            ruin_events_list.extend(np.any(equity_paths < ruin_level, axis=1))
        
        final_capitals = np.array(final_capitals_list)
        max_drawdowns = np.array(max_drawdowns_list)
        ruin_events = np.array(ruin_events_list)
        
        risk_of_ruin_prob = np.mean(ruin_events)
        mdd_95_ci = np.percentile(max_drawdowns, 95)
        
        cap_mean = np.mean(final_capitals)
        cap_median = np.median(final_capitals)
        cap_5th = np.percentile(final_capitals, 5)
        cap_95th = np.percentile(final_capitals, 95)
        
        # Distribution graph data (Histogram)
        hist_counts, hist_bins = np.histogram(final_capitals, bins=50)
        
        return {
            "status": "success",
            "iterations": self.iterations,
            "metrics": {
                "max_drawdown_95_ci": float(mdd_95_ci),
                "risk_of_ruin_probability": float(risk_of_ruin_prob),
                "final_capital": {
                    "mean": float(cap_mean),
                    "median": float(cap_median),
                    "5th_percentile": float(cap_5th),
                    "95th_percentile": float(cap_95th)
                }
            },
            "distribution_graph": {
                "counts": hist_counts.tolist(),
                "bins": hist_bins.tolist()
            }
        }
