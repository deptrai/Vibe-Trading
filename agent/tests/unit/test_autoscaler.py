import os
from unittest import mock
import pytest
from src.autoscaler import WorkerAutoscaler

@mock.patch("redis.Redis.from_url")
def test_autoscaler_initialization(mock_redis):
    autoscaler = WorkerAutoscaler()
    assert autoscaler.max_workers == 3
    assert autoscaler.min_workers == 1
    assert autoscaler.scale_up_threshold == 10
    
@mock.patch("redis.Redis.from_url")
@mock.patch("subprocess.Popen")
def test_autoscaler_scale_up(mock_popen, mock_redis):
    autoscaler = WorkerAutoscaler()
    
    def create_mock_process(*args, **kwargs):
        mock_process = mock.Mock()
        mock_process.pid = len(autoscaler.current_workers) + 1000
        return mock_process
        
    mock_popen.side_effect = create_mock_process
    
    # Assert initial state
    assert len(autoscaler.current_workers) == 0
    
    # Start up to min workers
    autoscaler.start_worker()
    assert len(autoscaler.current_workers) == 1
    
    # Scale up manually
    autoscaler.start_worker()
    assert len(autoscaler.current_workers) == 2
    
    # Max workers
    autoscaler.start_worker()
    assert len(autoscaler.current_workers) == 3
    
    # Exceed max workers should not start a new one
    autoscaler.start_worker()
    assert len(autoscaler.current_workers) == 3
    
@mock.patch("redis.Redis.from_url")
@mock.patch("subprocess.Popen")
def test_autoscaler_scale_down(mock_popen, mock_redis):
    autoscaler = WorkerAutoscaler()
    autoscaler.min_workers = 1
    
    # Create two mocked processes
    p1 = mock.Mock()
    p1.pid = 111
    
    p2 = mock.Mock()
    p2.pid = 222
    
    mock_popen.side_effect = [p1, p2]
    
    autoscaler.start_worker()
    autoscaler.start_worker()
    
    assert len(autoscaler.current_workers) == 2
    
    autoscaler.stop_worker()
    assert len(autoscaler.current_workers) == 1
    p2.terminate.assert_called_once()
    
    # Minimum workers constraint
    autoscaler.stop_worker()
    assert len(autoscaler.current_workers) == 1
    p1.terminate.assert_not_called()
    
@mock.patch("redis.Redis.from_url")
def test_autoscaler_queue_length(mock_redis):
    # Setup mock redis client
    mock_client = mock.Mock()
    mock_client.llen.side_effect = lambda q: 5 if "premium" in q else 10
    
    mock_redis.return_value = mock_client
    
    autoscaler = WorkerAutoscaler()
    
    # 2 premium queues * 5 = 10, 2 standard queues * 10 = 20 -> 30 total
    assert autoscaler.get_total_queue_length() == 30
    
    mock_client.llen.assert_has_calls([
        mock.call("backtest.standard"),
        mock.call("backtest.premium"),
        mock.call("rl_optimization.standard"),
        mock.call("rl_optimization.premium")
    ])
