import os
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from celery import Celery
import pandas as pd
import numpy as np
from src.monte_carlo import MonteCarloSimulator

try:
    import ccxt
    RETRY_EXCEPTIONS = (ConnectionError, TimeoutError, ccxt.NetworkError, ccxt.RateLimitExceeded)
except ImportError:
    RETRY_EXCEPTIONS = (ConnectionError, TimeoutError)

logger = logging.getLogger(__name__)

# Default to localhost Redis if not provided in environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "vibe_trading_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,  # Results expire in 1 hour to prevent Redis OOM
    task_routes={
        "src.worker.run_backtest_job": {"queue": "backtest"},
        "src.worker.*": {"queue": "default"},
    },
)

@celery_app.task(
    name="src.worker.run_backtest_job", 
    bind=True, 
    autoretry_for=RETRY_EXCEPTIONS, 
    retry_backoff=True, 
    max_retries=3
)
def run_backtest_job(self, payload: dict) -> dict:
    """
    Background task to run a backtest job.
    Accepts the serialized VibeTradingJobPayload as a dictionary.
    """
    from src.api_models import VibeTradingJobPayload
    from backtest.loaders.registry import get_loader_cls_with_fallback

    try:
        # 1. Parse payload
        job_payload = VibeTradingJobPayload(**payload)
        
        assets = job_payload.context_rules.assets or []
        timeframe = job_payload.context_rules.timeframe
        historical_range = job_payload.simulation_environment.historical_range
        exchange = job_payload.simulation_environment.exchange

        # 2-Year Lookback Constraint
        MAX_DAYS = 730
        effective_range = historical_range
        if historical_range > MAX_DAYS:
            logger.warning(f"Requested historical range ({historical_range} days) exceeds 2-year limit. Truncating to {MAX_DAYS} days.")
            effective_range = MAX_DAYS

        # 2. Symbol Validation (Crypto-first, reject non-crypto like stocks)
        valid_crypto_assets = []
        rejected_assets = []
        for asset in assets:
            asset_upper = asset.upper()
            # Simple heuristic to identify crypto assets
            if "-" in asset_upper or "/" in asset_upper or asset_upper.endswith(("USDT", "USD", "BTC", "ETH", "USDC")):
                valid_crypto_assets.append(asset_upper)
            else:
                rejected_assets.append(asset)
                
        if not valid_crypto_assets:
            return {
                "status": "error",
                "job_id": self.request.id,
                "message": "No valid crypto assets provided. Non-crypto symbols are rejected.",
                "payload_received": payload
            }

        # 3. Data Loading via CCXT loader
        original_exchange = os.environ.get("CCXT_EXCHANGE")
        if exchange is not None:
            os.environ["CCXT_EXCHANGE"] = str(exchange)
            
        try:
            loader_cls = get_loader_cls_with_fallback("ccxt")
            loader = loader_cls()
        finally:
            if original_exchange is not None:
                os.environ["CCXT_EXCHANGE"] = original_exchange
            elif "CCXT_EXCHANGE" in os.environ:
                del os.environ["CCXT_EXCHANGE"]
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=effective_range)
        
        start_date_str = start_date.isoformat()
        end_date_str = end_date.isoformat()

        logger.info(f"Loading data for {valid_crypto_assets} from {exchange} via ccxt...")
        market_data = loader.fetch(
            codes=valid_crypto_assets,
            start_date=start_date_str,
            end_date=end_date_str,
            interval=timeframe
        )
            
        import json
        runs_dir = os.environ.get("RUNS_DIR", "./runs")
        job_dir = os.path.join(runs_dir, str(self.request.id))
        os.makedirs(job_dir, exist_ok=True)
            
        # Serialize pandas DataFrame to a summary for the response
        # (returning full DataFrames via Celery broker is bad practice)
        data_summary = {}
        if market_data:
            for symbol, df in market_data.items():
                if df is not None and hasattr(df, "empty") and not df.empty and hasattr(df, "index"):
                    # Save results to persistent storage
                    safe_symbol = symbol.replace("/", "_").replace("-", "_")
                    csv_path = os.path.join(job_dir, f"{safe_symbol}.csv")
                    if hasattr(df, "to_csv"):
                        df.to_csv(csv_path)
                    
                    data_summary[symbol] = {
                        "rows_fetched": len(df),
                        "first_date": getattr(df.index.min(), "isoformat", lambda: str(df.index.min()))(),
                        "last_date": getattr(df.index.max(), "isoformat", lambda: str(df.index.max()))(),
                        "saved_to": csv_path
                    }
                    
                    if getattr(job_payload.execution_flags, "enable_monte_carlo_stress_test", False):
                        try:
                            # Safely extract initial capital
                            init_cap_raw = getattr(job_payload.simulation_environment, "initial_capital", 10000.0)
                            try:
                                initial_cap = float(init_cap_raw)
                                if initial_cap <= 0:
                                    initial_cap = 10000.0
                            except (ValueError, TypeError):
                                initial_cap = 10000.0

                            # Lowercase columns to find 'close' safely
                            columns_lower = {str(c).lower(): c for c in df.columns} if hasattr(df, "columns") else {}
                            if "close" in columns_lower:
                                close_col = columns_lower["close"]
                                
                                # TODO: Replace asset returns with actual strategy execution trade returns 
                                # once the backtest engine is fully integrated.
                                # For now, we simulate a strategy's trade returns by sampling and modifying asset returns
                                asset_returns = df[close_col].pct_change().replace([np.inf, -np.inf], np.nan).dropna()
                                if len(asset_returns) > 0:
                                    # Simulate strategy returns (e.g. holding 50% of the time, capturing some asset movement)
                                    simulated_trade_returns = asset_returns * np.random.choice([0, 1, -1], size=len(asset_returns), p=[0.5, 0.3, 0.2])
                                    
                                    mc_sim = MonteCarloSimulator(iterations=10000, risk_of_ruin_threshold=0.5)
                                    mc_results = mc_sim.run_simulation(
                                        trade_returns=simulated_trade_returns,
                                        initial_capital=initial_cap
                                    )
                                    
                                    if mc_results.get("status") == "success":
                                        data_summary[symbol]["monte_carlo"] = mc_results
                                        
                                        # Also write to dedicated json file
                                        mc_path = os.path.join(job_dir, f"{safe_symbol}_monte_carlo.json")
                                        with open(mc_path, "w") as f:
                                            json.dump(mc_results, f, indent=2)
                        except Exception as loop_e:
                            logger.error(f"Error during Monte Carlo simulation for {symbol}: {loop_e}", exc_info=True)

        # Save a metadata summary file
        meta_path = os.path.join(job_dir, "metadata.json")
        with open(meta_path, "w") as f:
            json.dump({
                "job_id": str(self.request.id),
                "requested_range_days": historical_range,
                "effective_range_days": effective_range,
                "exchange": exchange,
                "rejected_assets": rejected_assets,
                "data_summary": data_summary,
            }, f, indent=2)

        return {
            "status": "success",
            "job_id": self.request.id,
            "message": "Backtest data loaded successfully",
            "rejected_assets": rejected_assets,
            "data_summary": data_summary,
            "payload_received": payload
        }
    except RETRY_EXCEPTIONS as e:
        logger.warning(f"Transient error processing backtest job {self.request.id}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Error processing backtest job {self.request.id}")
        raise
