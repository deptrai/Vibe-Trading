import os
import json
import logging
import time
from decimal import Decimal
import pandas as pd
import numpy as np
import optuna
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RLOptimizer:
    def __init__(self, job_dir: str, target: str = "sharpe", max_trials: int = 50):
        self.job_dir = job_dir
        self.target = target
        self.max_trials = max_trials
        self.progress_file = os.path.join(job_dir, "progress.json")
        self.best_score_so_far = -float('inf')
        self.start_time = time.time()

    def _save_progress(self, current_trial: int, total_trials: int, best_score: float, force: bool = False):
        # I/O Optimization: Throttle progress file writes (every 5 trials or if forced)
        if not force and current_trial > 0 and current_trial % 5 != 0 and current_trial != total_trials:
            return

        progress_data = {
            "current_trial": current_trial,
            "total_trials": total_trials,
            "best_score_so_far": best_score,
            "elapsed_seconds": round(time.time() - self.start_time, 2)
        }
        try:
            with open(self.progress_file, "w") as f:
                json.dump(progress_data, f)
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")

    def _simulate_backtest(self, params: Dict[str, Any], market_data: Dict[str, pd.DataFrame]) -> Decimal:
        """
        Simplified backtest using historical returns.
        Constructs a deterministic strategy return series based on indicators and risk rules.
        """
        all_returns = []
        
        for symbol, df in market_data.items():
            if df is None or (hasattr(df, "empty") and df.empty):
                continue
                
            columns_lower = {str(c).lower(): c for c in df.columns}
            if 'close' not in columns_lower:
                continue
                
            close_col = columns_lower['close']
            returns = df[close_col].pct_change().replace([np.inf, -np.inf], np.nan).dropna()
            
            if len(returns) == 0:
                continue
            
            # Simplified Logic: RSI + MACD + MA influence
            # Higher MA period -> smoother trend following
            # RSI period -> sensitivity
            # stop_loss_pct -> noise reduction / downside protection
            
            rsi_w = params.get("rsi_period", 14) / 30.0
            ma_w = params.get("ma_period", 50) / 200.0
            
            # Deterministic pseudo-randomness based on parameters to simulate trade execution
            state = np.random.RandomState(int(params.get("rsi_period", 14) + params.get("ma_period", 50)))
            
            # Simulate a "signal strength" multiplier (0.5 to 1.5)
            signal_quality = (rsi_w * 0.4 + ma_w * 0.6) + 0.5
            
            # Apply stop loss "protection" by clipping negative returns
            sl = float(params.get("stop_loss_pct", 0.05))
            protected_returns = returns.clip(lower=-sl)
            
            strat_returns = protected_returns * signal_quality
            all_returns.extend(strat_returns.tolist())
            
        if not all_returns:
            return Decimal('0.0')
            
        arr = np.array(all_returns)
        
        # Calculate metric based on target
        if self.target == "sharpe":
            mean_ret = np.mean(arr)
            std_ret = np.std(arr)
            if std_ret == 0:
                return Decimal('0.0')
            # Annualized (Daily returns assumed, adjust if timeframe is different)
            score = (mean_ret / std_ret) * np.sqrt(365)
            return Decimal(str(score))
        elif self.target == "pnl":
            # Total cumulative return
            score = np.sum(arr)
            return Decimal(str(score))
        elif self.target == "sortino":
            mean_ret = np.mean(arr)
            downside = arr[arr < 0]
            if len(downside) == 0 or np.std(downside) == 0:
                # If no downside, use Sharpe logic or return high score
                std_ret = np.std(arr)
                if std_ret == 0: return Decimal('0.0')
                score = (mean_ret / std_ret) * np.sqrt(365)
            else:
                score = (mean_ret / np.std(downside)) * np.sqrt(365)
            return Decimal(str(score))
            
        return Decimal('0.0')

    def objective(self, trial: optuna.Trial, market_data: Dict[str, pd.DataFrame]) -> float:
        params = {
            "rsi_period": trial.suggest_int("rsi_period", 5, 30),
            "macd_fast": trial.suggest_int("macd_fast", 8, 20),
            "macd_slow": trial.suggest_int("macd_slow", 20, 40),
            "macd_signal": trial.suggest_int("macd_signal", 5, 15),
            "ma_period": trial.suggest_int("ma_period", 10, 200),
            "stop_loss_pct": trial.suggest_float("stop_loss_pct", 0.01, 0.10),
            "take_profit_pct": trial.suggest_float("take_profit_pct", 0.02, 0.20),
        }
        
        score_dec = self._simulate_backtest(params, market_data)
        score = float(score_dec)
        
        if np.isnan(score) or np.isinf(score):
            score = 0.0
            
        if score > self.best_score_so_far:
            self.best_score_so_far = score
            
        self._save_progress(trial.number + 1, self.max_trials, self.best_score_so_far)
        return score

    def optimize(self, market_data: Dict[str, pd.DataFrame], callbacks: list = None) -> Dict[str, Any]:
        # Data Validation
        if not market_data or all(df is None or (hasattr(df, "empty") and df.empty) for df in market_data.values()):
            logger.warning("Optimization started with empty market data")
            return {
                "status": "error",
                "message": "Market data is empty or invalid",
                "job_id": os.path.basename(self.job_dir)
            }

        self.start_time = time.time()
        pruner = optuna.pruners.MedianPruner()
        sampler = optuna.samplers.TPESampler(seed=42)
        study = optuna.create_study(direction="maximize", pruner=pruner, sampler=sampler)
        
        self._save_progress(0, self.max_trials, self.best_score_so_far, force=True)
        
        study.optimize(lambda trial: self.objective(trial, market_data), n_trials=self.max_trials, callbacks=callbacks)
        
        trial_history = []
        for t in study.trials:
            trial_history.append({
                "trial": t.number,
                "params": t.params,
                "score": t.value if t.value is not None else 0.0,
                "state": t.state.name
            })
            
        # Real Baseline: Calculate score using default parameters
        default_params = {
            "rsi_period": 14,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "ma_period": 50,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.10
        }
        baseline_score_dec = self._simulate_backtest(default_params, market_data)
        baseline_score = float(baseline_score_dec)
        
        best_score = study.best_value if len(study.trials) > 0 else 0.0
        improvement = ((best_score - baseline_score) / abs(baseline_score) * 100) if baseline_score != 0 else 0.0
        
        elapsed = round(time.time() - self.start_time, 2)
        
        result = {
            "status": "completed",
            "best_params": study.best_params if len(study.trials) > 0 else {},
            "best_score": best_score,
            "optimization_target": self.target,
            "baseline_score": baseline_score,
            "improvement_pct": improvement,
            "total_trials": len(study.trials),
            "trial_history": trial_history,
            "elapsed_seconds": elapsed
        }
        
        out_path = os.path.join(self.job_dir, "optimized_params.json")
        try:
            with open(out_path, "w") as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save optimized params: {e}")
            
        self._save_progress(len(study.trials), self.max_trials, best_score, force=True)
        return result
