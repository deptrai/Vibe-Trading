import os
import json
import logging
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

    def _save_progress(self, current_trial: int, total_trials: int, best_score: float):
        progress_data = {
            "current_trial": current_trial,
            "total_trials": total_trials,
            "best_score_so_far": best_score
        }
        with open(self.progress_file, "w") as f:
            json.dump(progress_data, f)

    def _simulate_backtest(self, params: Dict[str, Any], market_data: Dict[str, pd.DataFrame]) -> Decimal:
        """
        Simplified backtest using historical returns.
        For demonstration, we construct a deterministic synthetic strategy return series.
        """
        all_returns = []
        
        for symbol, df in market_data.items():
            if df.empty:
                continue
                
            columns_lower = {str(c).lower(): c for c in df.columns}
            if 'close' not in columns_lower:
                continue
                
            close_col = columns_lower['close']
            returns = df[close_col].pct_change().replace([np.inf, -np.inf], np.nan).dropna()
            
            if len(returns) == 0:
                continue
            
            rsi_w = params["rsi_period"] / 30.0
            macd_w = (params["macd_fast"] + params["macd_slow"]) / 60.0
            
            # Deterministic pseudo-randomness based on parameters
            np.random.seed(int(params["rsi_period"] + params["ma_period"]))
            
            noise = np.random.normal(0, 1, len(returns)) * float(params["stop_loss_pct"])
            strat_returns = returns * (rsi_w * 0.5 + macd_w * 0.5) + noise
            all_returns.extend(strat_returns.tolist())
            
        if not all_returns:
            return Decimal('0.0')
            
        arr = np.array(all_returns)
        if self.target == "sharpe":
            mean_ret = np.mean(arr)
            std_ret = np.std(arr)
            if std_ret == 0:
                return Decimal('0.0')
            score = (mean_ret / std_ret) * np.sqrt(365) # Annualized
            return Decimal(str(score))
        elif self.target == "pnl":
            score = np.sum(arr)
            return Decimal(str(score))
        elif self.target == "sortino":
            mean_ret = np.mean(arr)
            downside = arr[arr < 0]
            if len(downside) == 0 or np.std(downside) == 0:
                return Decimal('0.0')
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
        pruner = optuna.pruners.MedianPruner()
        sampler = optuna.samplers.TPESampler(seed=42)
        study = optuna.create_study(direction="maximize", pruner=pruner, sampler=sampler)
        
        self._save_progress(0, self.max_trials, self.best_score_so_far)
        
        study.optimize(lambda trial: self.objective(trial, market_data), n_trials=self.max_trials, callbacks=callbacks)
        
        trial_history = []
        for t in study.trials:
            trial_history.append({
                "trial": t.number,
                "params": t.params,
                "score": t.value if t.value is not None else 0.0,
                "state": t.state.name
            })
            
        baseline_score = 0.92 # Dummy baseline for now
        best_score = study.best_value if len(study.trials) > 0 else 0.0
        improvement = ((best_score - baseline_score) / baseline_score * 100) if baseline_score else 0.0
        
        result = {
            "status": "completed",
            "best_params": study.best_params if len(study.trials) > 0 else {},
            "best_score": best_score,
            "optimization_target": self.target,
            "baseline_score": baseline_score,
            "improvement_pct": improvement,
            "total_trials": len(study.trials),
            "trial_history": trial_history,
        }
        
        out_path = os.path.join(self.job_dir, "optimized_params.json")
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)
            
        return result
