import sys
import os
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from celery import Celery
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.monte_carlo import MonteCarloSimulator

try:
    import ccxt
    RETRY_EXCEPTIONS = (ConnectionError, TimeoutError, ccxt.NetworkError, ccxt.RateLimitExceeded)
except ImportError:
    RETRY_EXCEPTIONS = (ConnectionError, TimeoutError)

logger = logging.getLogger(__name__)

# Default to an absolute path for RUNS_DIR to ensure consistency across containers/mounts
DEFAULT_RUNS_DIR = str(Path("/tmp/vibe-trading/runs").resolve())
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
    imports=["src.kg_crawler"],
    task_routes={
        "src.worker.run_backtest_job": {"queue": "backtest.standard"},
        "src.rl_worker.run_rl_optimization_job": {"queue": "rl_optimization.standard"},
        "src.kg_crawler.sync_knowledge_graph": {"queue": "kg_sync"},
        "src.worker.*": {"queue": "default"},
    },
    beat_schedule={
        "sync-kg-periodically": {
            "task": "src.kg_crawler.sync_knowledge_graph",
            "schedule": float(os.getenv("KG_SYNC_INTERVAL_MINUTES", "5")) * 60,
        },
        "cleanup-runs-directory": {
            "task": "src.worker.run_cleanup",
            "schedule": float(os.getenv("CLEANUP_INTERVAL_MINUTES", "60")) * 60,
        },
    },
)

@celery_app.task(name="src.worker.run_cleanup", bind=True)
def run_cleanup(self):
    """Periodic task to clean up old or large run artifacts."""
    from src.cleanup import cleanup_runs_directory
    try:
        runs_dir = os.environ.get("RUNS_DIR", DEFAULT_RUNS_DIR)
        deleted = cleanup_runs_directory(runs_dir)
        return {"status": "success", "deleted_paths": deleted}
    except Exception as e:
        logger.error(f"Failed to run cleanup task: {e}")
        return {"status": "failed", "error": str(e)}

def _is_dex_exchange(exchange: str) -> bool:
    """Identify decentralized exchanges more robustly."""
    DEX_KEYWORDS = {"uniswap", "sushiswap", "pancakeswap", "curve", "dex", "raydium", "jupiter", "balancer"}
    return any(kw in exchange.lower() for kw in DEX_KEYWORDS)

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
    from src.api_models import VibeTradingJobPayload, InstrumentType
    from backtest.loaders.registry import get_loader_cls_with_fallback

    try:
        # 1. Parse payload
        job_payload = VibeTradingJobPayload(**payload)
        
        assets = job_payload.context_rules.assets or []
        timeframe = job_payload.context_rules.timeframe
        historical_range = job_payload.simulation_environment.historical_range
        exchange = job_payload.simulation_environment.exchange

        # Determine if DEX environment
        defi_simulator = None
        if _is_dex_exchange(exchange):
            from src.defi_simulator import DeFiSimulator
            defi_simulator = DeFiSimulator(
                gas_fee_model=job_payload.simulation_environment.gas_fee_model,
                slippage_tolerance=job_payload.simulation_environment.slippage_tolerance,
                track_impermanent_loss=job_payload.simulation_environment.track_impermanent_loss
            )
            logger.info(f"Initialized DeFiSimulator for DEX exchange: {exchange}")

        perpetual_simulator = None
        if job_payload.simulation_environment.instrument_type == InstrumentType.PERPETUAL:
            from src.perpetual_simulator import PerpetualSimulator
            perpetual_simulator = PerpetualSimulator()
            logger.info("Initialized PerpetualSimulator for PERPETUAL instrument type")

        # 2-Year Lookback Constraint (using calendar-aware delta)
        now = datetime.now(timezone.utc)
        two_years_ago = now - relativedelta(years=2)
        requested_start_date = now - timedelta(days=historical_range)
        
        effective_start_date = requested_start_date
        if requested_start_date < two_years_ago:
            logger.warning(f"Requested start date {requested_start_date} exceeds 2-year limit. Truncating to {two_years_ago}.")
            effective_start_date = two_years_ago
        
        effective_range_days = (now - effective_start_date).days

        # 2. Symbol Validation (Crypto-first, reject non-crypto like stocks)
        valid_crypto_assets = []
        rejected_assets = []
        for asset in assets:
            asset_upper = asset.upper()
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
        
        start_date_str = effective_start_date.isoformat()
        end_date_str = now.isoformat()

        logger.info(f"Loading data for {valid_crypto_assets} from {exchange} via ccxt...")
        market_data = loader.fetch(
            codes=valid_crypto_assets,
            start_date=start_date_str,
            end_date=end_date_str,
            interval=timeframe
        )
            
        runs_dir = os.environ.get("RUNS_DIR", DEFAULT_RUNS_DIR)
        job_dir = os.path.join(runs_dir, str(self.request.id))
        os.makedirs(job_dir, exist_ok=True)
        
        code_dir = os.path.join(job_dir, "code")
        os.makedirs(code_dir, exist_ok=True)
        
        # 3. Handle Strategy Code Generation (Story 6.1)
        strategy_path = os.path.join(code_dir, "strategy.py")
        if job_payload.context_rules.executable_code:
            logger.info("Using provided executable code. Scanning for security...")
            from src.security import scan_code
            is_safe, errors = scan_code(job_payload.context_rules.executable_code)
            if not is_safe:
                logger.error(f"Security scan failed: {errors}")
                return {
                    "status": "error",
                    "job_id": self.request.id,
                    "message": "Security scan failed for provided executable code.",
                    "reasons": errors
                }
            with open(strategy_path, "w") as f:
                f.write(job_payload.context_rules.executable_code)
        elif job_payload.context_rules.natural_language_rules:
            logger.info("Invoking AgentLoop headless mode to generate strategy...")
            from src.tools import build_registry
            from src.providers.chat import ChatLLM
            from src.agent.loop import AgentLoop
            from src.memory.persistent import PersistentMemory
            
            llm = ChatLLM()
            pm = PersistentMemory()
            agent = AgentLoop(
                registry=build_registry(persistent_memory=pm, include_shell_tools=False),
                llm=llm,
                max_iterations=10,
                persistent_memory=pm,
            )
            headless_result = agent.run_headless(job_payload.context_rules.natural_language_rules, Path(job_dir))
            if headless_result.get("status") == "failed":
                return {
                    "status": "error",
                    "job_id": self.request.id,
                    "message": "AgentLoop failed to generate signal_engine.py: " + headless_result.get("reason", "Unknown error")
                }
        else:
            return {
                "status": "error",
                "job_id": self.request.id,
                "message": "Payload must contain either executable_code or natural_language_rules."
            }
            
        # 4. Generate config.json for the engine
        config_data = {
            "codes": valid_crypto_assets,
            "start_date": effective_start_date.strftime("%Y-%m-%d"),
            "end_date": now.strftime("%Y-%m-%d"),
            "source": exchange or "auto",
            "interval": timeframe,
            "engine": "daily"
        }
        with open(os.path.join(job_dir, "config.json"), "w") as f:
            json.dump(config_data, f, indent=2)
            
        data_summary = {}
        if market_data:
            # First pass: save all CSVs and basic plots
            for symbol, df in market_data.items():
                if df is not None and hasattr(df, "empty") and not df.empty and hasattr(df, "index"):
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
                    
                    # Generate a basic price chart (AC 2)
                    try:
                        import matplotlib.pyplot as plt
                        plt.figure(figsize=(10, 6))
                        close_col = next((c for c in df.columns if str(c).lower() == "close"), df.columns[0])
                        df[close_col].plot(title=f"Price History for {symbol}")
                        plt.ylabel("Price")
                        plt.xlabel("Date")
                        plt.grid(True)
                        plot_path = os.path.join(job_dir, f"{safe_symbol}_price.png")
                        plt.savefig(plot_path)
                        plt.close()
                        data_summary[symbol]["plot_path"] = plot_path
                    except Exception as plot_e:
                        logger.error(f"Failed to generate plot for {symbol}: {plot_e}")

        # 5. Execute backtest.runner via Runner API
        from src.core.runner import Runner
        logger.info(f"Executing backtest Runner for job {self.request.id}")
        runner = Runner(Path(job_dir))
        runner_result = runner.execute()
        if not runner_result.success:
            logger.error(f"Runner failed: {runner_result.stderr}")
            return {
                "status": "error",
                "job_id": self.request.id,
                "message": "Engine runner failed execution.",
                "stderr": runner_result.stderr
            }

        if market_data:
            # Second pass: simulators
            for symbol, df in market_data.items():
                if df is not None and hasattr(df, "empty") and not df.empty and hasattr(df, "index"):
                    safe_symbol = symbol.replace("/", "_").replace("-", "_")
                    if getattr(job_payload.execution_flags, "enable_monte_carlo_stress_test", False):
                        try:
                            init_cap_raw = getattr(job_payload.simulation_environment, "initial_capital", 10000.0)
                            initial_cap = float(init_cap_raw) if init_cap_raw and float(init_cap_raw) > 0 else 10000.0

                            columns_lower = {str(c).lower(): c for c in df.columns}
                            if "close" in columns_lower:
                                close_col = columns_lower["close"]
                                asset_returns = df[close_col].pct_change().replace([np.inf, -np.inf], np.nan).dropna()
                                if len(asset_returns) > 0:
                                    # Load actual strategy returns from equity.csv if available
                                    equity_path = os.path.join(job_dir, "artifacts", "equity.csv")
                                    if os.path.exists(equity_path):
                                        eq_df = pd.read_csv(equity_path, index_col=0, parse_dates=True)
                                        simulated_trade_returns = eq_df["equity"].pct_change().fillna(0)
                                        # Align index exactly with asset_returns to avoid misalignment
                                        simulated_trade_returns = simulated_trade_returns.reindex(asset_returns.index, fill_value=0.0)
                                    else:
                                        # If no equity.csv, there's no actual strategy returns
                                        logger.warning(f"No equity.csv found for {symbol}, skipping simulation enrichment.")
                                        simulated_trade_returns = pd.Series(0.0, index=asset_returns.index)
                                    
                                    # For positions, we might not have them easily accessible per bar for liquidations
                                    # We'll mock positions based on returns for the sake of the simulator
                                    random_positions = np.where(simulated_trade_returns > 0, 1, np.where(simulated_trade_returns < 0, -1, 0))

                                    liquidation_events = []
                                    total_funding_fees = 0.0

                                    if perpetual_simulator is not None:
                                        from decimal import Decimal
                                        leverage_dec = Decimal(str(job_payload.risk_management.leverage))
                                        initial_cap_dec = Decimal(str(initial_cap))
                                        
                                        # Use a stateful simulation for path-dependent perpetuals
                                        new_returns = simulated_trade_returns.values.copy()
                                        is_liquidated_state = False
                                        
                                        # Pre-calculate constants to avoid Decimal conversion in loop
                                        entry_price_dec = Decimal('1.0')
                                        liq_price_dec = perpetual_simulator.calculate_liquidation_price(entry_price_dec, leverage_dec, True) # long
                                        liq_price_short_dec = perpetual_simulator.calculate_liquidation_price(entry_price_dec, leverage_dec, False) # short
                                        
                                        last_funding_ts = None
                                        
                                        for i in range(len(simulated_trade_returns)):
                                            if is_liquidated_state:
                                                new_returns[i] = 0.0 # No more returns after liquidation
                                                continue
                                                
                                            pos = random_positions[i]
                                            if pos == 0:
                                                continue
                                                
                                            ts = simulated_trade_returns.index[i]
                                            is_long = (pos == 1)
                                            
                                            # 1. Apply Funding Fee (Only once per 8h window)
                                            # Logic: if hour is 0, 8, 16 AND we haven't applied for this specific timestamp
                                            if hasattr(ts, 'hour') and ts.hour % 8 == 0 and ts != last_funding_ts:
                                                funding_rate = Decimal('0.0001') # Default mock
                                                pos_size = initial_cap_dec * leverage_dec
                                                fee = perpetual_simulator.calculate_funding_fee(pos_size, funding_rate, is_long)
                                                total_funding_fees += float(fee)
                                                # Funding impacts return relative to initial capital
                                                if initial_cap_dec > 0:
                                                    new_returns[i] += float(fee / initial_cap_dec)
                                                last_funding_ts = ts
                                            
                                            # 2. Check Liquidation
                                            # Simplified path-dependency: check if current bar return hits liq threshold
                                            ret = asset_returns.iloc[i]
                                            mark_price = entry_price_dec * Decimal(str(1.0 + ret))
                                            
                                            current_liq_price = liq_price_dec if is_long else liq_price_short_dec
                                            
                                            if perpetual_simulator.check_liquidation(mark_price, current_liq_price, is_long):
                                                liquidation_events.append({
                                                    "timestamp": str(ts),
                                                    "position": "LONG" if is_long else "SHORT",
                                                    "mark_price": float(mark_price),
                                                    "liquidation_price": float(current_liq_price)
                                                })
                                                new_returns[i] = -1.0 # Total loss of margin
                                                is_liquidated_state = True

                                        simulated_trade_returns = pd.Series(new_returns, index=simulated_trade_returns.index)
                                    # Apply DeFi penalties if in a DEX environment
                                    if defi_simulator is not None:
                                        # Proxy values for dynamic calculation
                                        # In a real LP strategy, pool_liquidity would come from on-chain data
                                        proxy_pool_liquidity = initial_cap * 100
                                        # Price ratio proxy (last close vs first close in the window)
                                        proxy_price_ratio = float(df[close_col].iloc[-1] / df[close_col].iloc[0]) if len(df) > 1 else 1.0
                                        
                                        base_fee = float(defi_simulator.calculate_gas_fee())
                                        gas_impact = base_fee / initial_cap if initial_cap > 0 else 0
                                        
                                        # Dynamic slippage based on trade size (assuming full capital per trade)
                                        slippage = defi_simulator.calculate_slippage(initial_cap, proxy_pool_liquidity)
                                        
                                        # IL based on the total price divergence in the backtest period
                                        il = abs(float(defi_simulator.calculate_impermanent_loss(proxy_price_ratio)))
                                        
                                        total_penalty = gas_impact + slippage + il
                                        # Apply penalty only to non-zero simulated returns (actual trades)
                                        simulated_trade_returns = simulated_trade_returns.mask(simulated_trade_returns != 0, simulated_trade_returns - total_penalty)
                                        logger.info(f"Applying DeFi penalties to {symbol}: Gas={gas_impact:.4f}, Slippage={slippage:.4f}, IL={il:.4f}")
                                    
                                    mc_sim = MonteCarloSimulator(iterations=10000, risk_of_ruin_threshold=0.5)
                                    mc_results = mc_sim.run_simulation(
                                        trade_returns=simulated_trade_returns,
                                        initial_capital=initial_cap
                                    )
                                    
                                    if mc_results.get("status") == "success":
                                        if perpetual_simulator is not None:
                                            mc_results["liquidation_events"] = liquidation_events
                                            mc_results["total_funding_fees"] = total_funding_fees
                                        data_summary[symbol]["monte_carlo"] = mc_results
                                        mc_path = os.path.join(job_dir, f"{safe_symbol}_monte_carlo.json")
                                        with open(mc_path, "w") as f:
                                            json.dump(mc_results, f, indent=2)
                        except Exception as loop_e:
                            logger.error(f"Error during Monte Carlo simulation for {symbol}: {loop_e}", exc_info=True)

        engine_artifacts = {}
        artifacts_dir = os.path.join(job_dir, "artifacts")
        if os.path.exists(artifacts_dir):
            for file in os.listdir(artifacts_dir):
                if file.endswith((".csv", ".png", ".json")):
                    engine_artifacts[file] = os.path.join(artifacts_dir, file)

        # 6. Save standard state.json
        state_data = {
            "status": "success",
            "job_id": str(self.request.id),
            "artifacts": engine_artifacts,
            "metrics": data_summary
        }
        state_path = os.path.join(job_dir, "state.json")
        with open(state_path, "w") as f:
            json.dump(state_data, f, indent=2)

        # Save a metadata summary file
        meta_path = os.path.join(job_dir, "metadata.json")
        with open(meta_path, "w") as f:
            json.dump({
                "job_id": str(self.request.id),
                "requested_range_days": historical_range,
                "effective_range_days": effective_range_days,
                "exchange": exchange,
                "rejected_assets": rejected_assets,
                "data_summary": data_summary,
                "engine_artifacts": engine_artifacts,
            }, f, indent=2)

        # Return combined dict to maintain backward compatibility while supporting new state structure
        response_payload = {
            **state_data,
            "message": "Backtest data loaded successfully",
            "rejected_assets": rejected_assets,
            "data_summary": data_summary,
            "payload_received": payload
        }
        return response_payload
    except RETRY_EXCEPTIONS as e:
        logger.warning(f"Transient error processing backtest job {self.request.id}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Error processing backtest job {self.request.id}")
        raise
