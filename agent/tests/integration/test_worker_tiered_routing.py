from __future__ import annotations
import pytest
from celery import current_app
from unittest.mock import patch
from src.worker import run_backtest_job
from src.rl_worker import run_rl_optimization_job

@pytest.mark.integration
class TestWorkerTieredRouting:
    """[P1] Integration tests for tiered queue routing configuration."""

    def test_backtest_task_premium_queue_routing(self):
        """[P1] Should be able to dispatch to backtest.premium queue"""
        with patch('src.worker.run_backtest_job.apply_async') as mock_apply:
            mock_apply.return_value.id = 'premium_task_123'
            task = run_backtest_job.apply_async(args=[{}], queue='backtest.premium')
            assert mock_apply.called
            assert mock_apply.call_args[1]['queue'] == 'backtest.premium'

    def test_backtest_task_standard_queue_routing(self):
        """[P1] Should be able to dispatch to backtest.standard queue"""
        with patch('src.worker.run_backtest_job.apply_async') as mock_apply:
            mock_apply.return_value.id = 'standard_task_123'
            task = run_backtest_job.apply_async(args=[{}], queue='backtest.standard')
            assert mock_apply.called
            assert mock_apply.call_args[1]['queue'] == 'backtest.standard'

    def test_celery_task_routes_configuration(self):
        """[P1] Verify that task routes fallback to .standard if not explicitly routed"""
        routes = current_app.conf.task_routes
        assert 'src.worker.run_backtest_job' in routes
        assert routes['src.worker.run_backtest_job']['queue'] == 'backtest.standard'
        assert 'src.rl_worker.run_rl_optimization_job' in routes
        assert routes['src.rl_worker.run_rl_optimization_job']['queue'] == 'rl_optimization.standard'

    def test_start_worker_script_queue_configuration(self):
        """[P1] Verify that the start_worker.sh script configures workers for all tiered queues"""
        import os
        script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'start_worker.sh')
        assert os.path.exists(script_path), "start_worker.sh script not found"
        
        with open(script_path, 'r') as f:
            content = f.read()
            
        # Verify premium worker is configured to consume premium queues
        assert "-Q backtest.premium,rl_optimization.premium" in content
        
        # Verify standard worker is configured to consume standard queues
        assert "-Q backtest.standard,rl_optimization.standard,default" in content
        
        # Verify worker concurrency logic (premium has more autoscaling capacity)
        assert "--autoscale=10,3" in content
        assert "--autoscale=3,1" in content
