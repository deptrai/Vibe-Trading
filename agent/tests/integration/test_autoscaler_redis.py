import pytest
from unittest.mock import patch, MagicMock
from src.autoscaler import WorkerAutoscaler

class TestAutoscalerIntegration:
    """[P0] Integration tests for WorkerAutoscaler"""

    @patch('src.autoscaler.subprocess.Popen')
    @patch('src.autoscaler.redis.Redis.from_url')
    def test_autoscaler_scales_up_on_high_queue(self, mock_redis_from_url, mock_popen):
        """[P0] Should spawn workers when total queue length exceeds threshold"""
        mock_redis = MagicMock()
        mock_redis.llen.side_effect = [15, 0, 0, 0]  # Total = 15
        mock_redis_from_url.return_value = mock_redis
        
        autoscaler = WorkerAutoscaler()
        autoscaler.scale_up_threshold = 10
        autoscaler.max_workers = 2
        
        mock_process = MagicMock()
        mock_process.pid = 9999
        mock_popen.return_value = mock_process
        
        # Manually run one iteration of the check
        autoscaler.check_and_scale()
        
        # Should have spawned one worker
        assert len(autoscaler.current_workers) == 1
        mock_popen.assert_called_once()
        
    @patch('src.autoscaler.subprocess.Popen')
    @patch('src.autoscaler.redis.Redis.from_url')
    def test_autoscaler_scales_down_on_idle(self, mock_redis_from_url, mock_popen):
        """[P0] Should terminate workers after idle checks exceed threshold"""
        mock_redis = MagicMock()
        mock_redis.llen.return_value = 0
        mock_redis_from_url.return_value = mock_redis
        
        autoscaler = WorkerAutoscaler()
        autoscaler.scale_down_idle_checks = 2
        autoscaler.min_workers = 0
        
        # Mock active worker
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process is running
        autoscaler.current_workers["autoscale_1"] = mock_process
        
        # Iteration 1: idle
        autoscaler.check_and_scale()
        assert autoscaler.idle_count == 1
        assert len(autoscaler.current_workers) == 1
        
        # Iteration 2: idle again, triggers scale down
        autoscaler.check_and_scale()
        assert autoscaler.idle_count == 0
        assert len(autoscaler.current_workers) == 0
        mock_process.terminate.assert_called_once()
