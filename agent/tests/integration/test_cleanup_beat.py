import pytest
from unittest.mock import patch
from celery.schedules import crontab
from src.worker import celery_app, run_cleanup

class TestCleanupBeatIntegration:
    """[P1] Integration tests for Cleanup task via Celery Beat"""

    def test_celery_beat_schedule_configured(self):
        """[P1] Should have run_cleanup scheduled in beat_schedule"""
        schedule = celery_app.conf.beat_schedule
        assert "run-cleanup-every-night" in schedule
        task_config = schedule["run-cleanup-every-night"]
        assert task_config["task"] == "src.worker.run_cleanup"
        assert isinstance(task_config["schedule"], crontab)
        assert task_config["schedule"].hour == {0}  # midnight
        assert task_config["schedule"].minute == {0}

    @patch('src.worker.cleanup_runs_directory')
    def test_run_cleanup_task_execution(self, mock_cleanup):
        """[P1] Should execute cleanup_runs_directory when task is called"""
        run_cleanup.apply()
        mock_cleanup.assert_called_once()
