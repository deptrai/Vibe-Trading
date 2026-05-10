import os
import logging
import psutil
import time
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from optuna.exceptions import TrialPruned

from src.worker import celery_app, DEFAULT_RUNS_DIR, RETRY_EXCEPTIONS

logger = logging.getLogger(__name__)

class RLProgressCallback:
    def __init__(self, task, total_trials):
        self.task = task
        self.total_trials = total_trials

    def __call__(self, study, trial):
        # Memory Guard
        vm = psutil.virtual_memory()
        # Abort if < 500MB free (524288000 bytes)
        if vm.available < 524288000:
            logger.warning(f"Memory guard triggered! Available memory: {vm.available}. Aborting trial.")
            raise TrialPruned("System memory limit reached")
            
        # Update Celery State
        self.task.update_state(
            state='PROGRESS',
            meta={
                'current_trial': len(study.trials),
                'total_trials': self.total_trials,
                'best_score_so_far': study.best_value if len(study.trials) > 0 else 0.0
            }
        )

@celery_app.task(
    name="src.rl_worker.run_rl_optimization_job",
    bind=True,
    soft_time_limit=1800,   # 30 min soft limit
    time_limit=2100,        # 35 min hard kill
    max_retries=1,
    acks_late=True,
    autoretry_for=RETRY_EXCEPTIONS
)
def run_rl_optimization_job(self, payload: dict) -> dict:
    from src.api_models import VibeTradingJobPayload
    from backtest.loaders.registry import get_loader_cls_with_fallback
    from src.rl_optimizer import RLOptimizer
    
    start_time = time.time()
    try:
        job_payload = VibeTradingJobPayload(**payload)
        
        assets = job_payload.context_rules.assets or []
        timeframe = job_payload.context_rules.timeframe
        historical_range = job_payload.simulation_environment.historical_range
        exchange = job_payload.simulation_environment.exchange
        
        # Date logic
        now = datetime.now(timezone.utc)
        two_years_ago = now - relativedelta(years=2)
        requested_start_date = now - timedelta(days=historical_range)
        
        effective_start_date = requested_start_date
        if requested_start_date < two_years_ago:
            effective_start_date = two_years_ago

        valid_crypto_assets = []
        for asset in assets:
            asset_upper = asset.upper()
            if "-" in asset_upper or "/" in asset_upper or asset_upper.endswith(("USDT", "USD", "BTC", "ETH", "USDC")):
                valid_crypto_assets.append(asset_upper)
                
        if not valid_crypto_assets:
            return {"status": "error", "message": "No valid crypto assets provided."}

        # CCXT loading - Pass exchange name directly to constructor for thread-safety
        try:
            loader_cls = get_loader_cls_with_fallback("ccxt")
            # If loader_cls supports exchange param in init, use it. Otherwise fallback to env if necessary
            # For this project, CCXT loader is usually configured via env, but passing to fetch is safer
            loader = loader_cls()
        except Exception as e:
            logger.error(f"Failed to initialize data loader: {e}")
            return {"status": "error", "message": "Data service unavailable."}
                
        market_data = loader.fetch(
            codes=valid_crypto_assets,
            start_date=effective_start_date.isoformat(),
            end_date=now.isoformat(),
            interval=timeframe
        )
        
        if not market_data:
             return {"status": "error", "message": "No market data retrieved."}

        runs_dir = os.environ.get("RUNS_DIR", DEFAULT_RUNS_DIR)
        job_id_str = str(self.request.id) if self.request and self.request.id else "local_test_job"
        job_dir = os.path.join(runs_dir, job_id_str)
        os.makedirs(job_dir, exist_ok=True)
        
        max_trials = getattr(job_payload.execution_flags, "rl_max_trials", 50)
        target = getattr(job_payload.execution_flags, "rl_optimization_target", "sharpe")
        
        optimizer = RLOptimizer(job_dir=job_dir, target=target, max_trials=max_trials)
        callback = RLProgressCallback(self, max_trials)
        
        result = optimizer.optimize(market_data=market_data, callbacks=[callback])
        
        return result
        
    except Exception as e:
        logger.exception("RL Optimization failed")
        job_id_str = str(self.request.id) if self.request and self.request.id else "local_test_job"
        return {
            "status": "error", 
            "message": "Internal error during optimization. Check logs for details.", 
            "job_id": job_id_str
        }
