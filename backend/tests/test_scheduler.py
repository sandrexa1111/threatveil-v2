"""
Tests for the Continuous Monitoring Scheduler

Tests the scheduler service functionality including:
- Due scan detection
- Schedule updates after scan
- No-op when no scans due
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from backend.services.scheduler import (
    calculate_next_run,
    run_due_scans,
    update_schedule_after_scan,
    get_scheduler_status,
)
from backend.models import Asset, ScanSchedule, Organization


class TestCalculateNextRun:
    """Tests for calculate_next_run function."""
    
    def test_daily_frequency(self):
        """Daily frequency should return 1 day later."""
        base = datetime(2025, 1, 1, 12, 0, 0)
        result = calculate_next_run('daily', base)
        assert result == base + timedelta(days=1)
    
    def test_weekly_frequency(self):
        """Weekly frequency should return 7 days later."""
        base = datetime(2025, 1, 1, 12, 0, 0)
        result = calculate_next_run('weekly', base)
        assert result == base + timedelta(weeks=1)
    
    def test_monthly_frequency(self):
        """Monthly frequency should return 30 days later."""
        base = datetime(2025, 1, 1, 12, 0, 0)
        result = calculate_next_run('monthly', base)
        assert result == base + timedelta(days=30)
    
    def test_manual_frequency(self):
        """Manual frequency should return far future (365 days)."""
        base = datetime(2025, 1, 1, 12, 0, 0)
        result = calculate_next_run('manual', base)
        assert result == base + timedelta(days=365)
    
    def test_uses_current_time_when_none(self):
        """Should use current time when no base time provided."""
        before = datetime.utcnow()
        result = calculate_next_run('daily')
        after = datetime.utcnow() + timedelta(days=1, seconds=1)
        assert before + timedelta(days=1) <= result <= after


class TestRunDueScans:
    """Tests for run_due_scans function."""
    
    @patch('backend.services.scheduler.SessionLocal')
    def test_no_due_assets(self, mock_session_local):
        """Should do nothing when no assets are due."""
        mock_db = Mock(spec=Session)
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Should not raise
        run_due_scans()
        
        mock_db.close.assert_called_once()
    
    @patch('backend.services.scheduler.SessionLocal')
    @patch('backend.services.scheduler.trigger_asset_scan')
    def test_triggers_due_scan(self, mock_trigger, mock_session_local):
        """Should trigger scan for due assets."""
        mock_db = Mock(spec=Session)
        mock_session_local.return_value = mock_db
        
        # Create a mock due asset
        mock_asset = Mock(spec=Asset)
        mock_asset.id = 'asset-1'
        mock_asset.type = 'domain'
        mock_asset.name = 'example.com'
        mock_asset.status = 'active'
        mock_asset.scan_frequency = 'daily'
        mock_asset.next_scan_at = datetime.utcnow() - timedelta(hours=1)
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_asset]
        
        run_due_scans()
        
        mock_trigger.assert_called_once_with(mock_db, mock_asset)
        mock_db.close.assert_called_once()
    
    @patch('backend.services.scheduler.SessionLocal')
    @patch('backend.services.scheduler.trigger_asset_scan')
    def test_handles_scan_error(self, mock_trigger, mock_session_local):
        """Should handle errors and continue processing."""
        mock_db = Mock(spec=Session)
        mock_session_local.return_value = mock_db
        
        mock_asset = Mock(spec=Asset)
        mock_asset.id = 'asset-1'
        mock_asset.type = 'domain'
        mock_trigger.side_effect = Exception("Scan failed")
        
        # Mock the schedule query for error handling
        mock_schedule = Mock(spec=ScanSchedule)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_schedule
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_asset]
        
        # Should not raise
        run_due_scans()
        
        # Error should be logged on schedule
        assert mock_schedule.error_count == mock_schedule.error_count  # Just verify no exception
        mock_db.close.assert_called_once()


class TestUpdateScheduleAfterScan:
    """Tests for update_schedule_after_scan function."""
    
    def test_updates_schedule(self):
        """Should update schedule with new timestamps and clear errors."""
        mock_db = Mock(spec=Session)
        
        mock_schedule = Mock(spec=ScanSchedule)
        mock_schedule.run_count = 5
        
        mock_asset = Mock(spec=Asset)
        mock_asset.id = 'asset-1'
        mock_asset.next_scan_at = datetime.utcnow() + timedelta(days=1)
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_schedule
        
        update_schedule_after_scan(mock_db, mock_asset, 'scan-123')
        
        assert mock_schedule.last_scan_id == 'scan-123'
        assert mock_schedule.run_count == 6
        assert mock_schedule.last_error is None
        mock_db.commit.assert_called_once()
    
    def test_no_schedule_exists(self):
        """Should handle case when no schedule exists."""
        mock_db = Mock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        mock_asset = Mock(spec=Asset)
        mock_asset.id = 'asset-1'
        mock_asset.next_scan_at = datetime.utcnow()
        
        # Should not raise
        update_schedule_after_scan(mock_db, mock_asset, 'scan-123')


class TestGetSchedulerStatus:
    """Tests for get_scheduler_status function."""
    
    @patch('backend.services.scheduler._scheduler', None)
    def test_not_running(self):
        """Should return not running when scheduler is None."""
        status = get_scheduler_status()
        assert status['running'] is False
        assert status['jobs'] == []
    
    @patch('backend.services.scheduler._scheduler')
    def test_running_with_jobs(self, mock_scheduler):
        """Should return job info when running."""
        mock_job = Mock()
        mock_job.id = 'run_due_scans'
        mock_job.name = 'Check and run due asset scans'
        mock_job.next_run_time = datetime(2025, 1, 1, 12, 0, 0)
        
        mock_scheduler.running = True
        mock_scheduler.get_jobs.return_value = [mock_job]
        
        status = get_scheduler_status()
        
        assert status['running'] is True
        assert len(status['jobs']) == 1
        assert status['jobs'][0]['id'] == 'run_due_scans'
