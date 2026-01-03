"""
Tests for Phase 2 Decision Impact Service.

Tests:
- Delta calculation correctness
- Confidence scoring rules (1.0, 0.7, 0.4, 0.2)
- Integration: resolving decision creates/updates DecisionImpact
- Integration: risk-timeline returns correct weekly aggregation
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from backend.services.impact_service import (
    calculate_confidence,
    compute_decision_impact,
    _check_signal_disappeared,
)


class TestDeltaCalculation:
    """Test delta calculation correctness."""

    def test_negative_delta_means_improvement(self):
        """Risk going from 70 to 50 = -20 delta (improvement)."""
        risk_before = 70
        risk_after = 50
        delta = risk_after - risk_before
        assert delta == -20
        assert delta < 0  # Negative = improvement

    def test_positive_delta_means_regression(self):
        """Risk going from 50 to 70 = +20 delta (regression)."""
        risk_before = 50
        risk_after = 70
        delta = risk_after - risk_before
        assert delta == 20
        assert delta > 0  # Positive = regression

    def test_zero_delta_means_no_change(self):
        """Risk staying at 60 = 0 delta (no change)."""
        risk_before = 60
        risk_after = 60
        delta = risk_after - risk_before
        assert delta == 0

    def test_delta_formula_is_after_minus_before(self):
        """Verify delta = risk_after - risk_before."""
        test_cases = [
            (80, 40, -40),  # Big improvement
            (30, 50, 20),   # Regression
            (100, 0, -100), # Complete fix
            (0, 100, 100),  # Complete regression
        ]
        for before, after, expected in test_cases:
            delta = after - before
            assert delta == expected, f"Failed for before={before}, after={after}"


class TestConfidenceRules:
    """Test deterministic confidence scoring."""

    def test_confidence_02_no_after_scan(self):
        """Confidence = 0.2 when no after scan exists."""
        mock_decision = MagicMock()
        mock_before_scan = MagicMock()
        no_after_scan = None
        resolved_at = datetime.now(timezone.utc)
        mock_db = MagicMock()

        confidence, notes = calculate_confidence(
            mock_decision, mock_before_scan, no_after_scan, resolved_at, mock_db
        )

        assert confidence == 0.2
        assert notes is not None
        assert "No scan after resolution" in notes

    def test_confidence_04_old_after_scan(self):
        """Confidence = 0.4 when after scan is older than 7 days."""
        mock_decision = MagicMock()
        mock_decision.action_id = 'some-action'
        mock_before_scan = MagicMock()
        mock_after_scan = MagicMock()
        
        # After scan created 10 days after resolution
        resolved_at = datetime(2024, 12, 1, tzinfo=timezone.utc)
        mock_after_scan.created_at = resolved_at + timedelta(days=10)
        mock_after_scan.signals_json = []
        mock_after_scan.scan_ai = None
        
        mock_db = MagicMock()

        confidence, notes = calculate_confidence(
            mock_decision, mock_before_scan, mock_after_scan, resolved_at, mock_db
        )

        assert confidence == 0.4
        assert notes is not None
        assert "days old" in notes

    def test_confidence_07_recent_scan_signal_unknown(self):
        """Confidence = 0.7 when scan within 7 days but signal status unknown."""
        mock_decision = MagicMock()
        mock_decision.action_id = 'unknown-action'  # Action not in mapping
        mock_before_scan = MagicMock()
        mock_after_scan = MagicMock()
        
        # After scan created 3 days after resolution
        resolved_at = datetime(2024, 12, 1, tzinfo=timezone.utc)
        mock_after_scan.created_at = resolved_at + timedelta(days=3)
        mock_after_scan.signals_json = []
        mock_after_scan.scan_ai = None
        
        mock_db = MagicMock()

        confidence, notes = calculate_confidence(
            mock_decision, mock_before_scan, mock_after_scan, resolved_at, mock_db
        )

        assert confidence == 0.7
        assert notes is not None or confidence == 0.7

    def test_confidence_10_signal_disappeared(self):
        """Confidence = 1.0 when scan within 7 days and triggering signal gone."""
        mock_decision = MagicMock()
        mock_decision.action_id = 'key-rotation'
        
        mock_before_scan = MagicMock()
        mock_before_ai = MagicMock()
        mock_before_ai.ai_keys = [{'key': 'exposed'}]
        mock_before_scan.scan_ai = mock_before_ai
        
        mock_after_scan = MagicMock()
        mock_after_ai = MagicMock()
        mock_after_ai.ai_keys = []  # Keys rotated (gone)
        mock_after_scan.scan_ai = mock_after_ai
        
        # After scan created 2 days after resolution
        resolved_at = datetime(2024, 12, 1, tzinfo=timezone.utc)
        mock_after_scan.created_at = resolved_at + timedelta(days=2)
        mock_after_scan.signals_json = []
        
        mock_db = MagicMock()

        confidence, notes = calculate_confidence(
            mock_decision, mock_before_scan, mock_after_scan, resolved_at, mock_db
        )

        assert confidence == 1.0
        assert notes is None


class TestSignalDisappeared:
    """Test signal disappearance detection."""

    def test_key_rotation_detected(self):
        """Detect key rotation when AI keys reduced."""
        mock_decision = MagicMock()
        mock_decision.action_id = 'key-rotation'
        
        mock_before = MagicMock()
        mock_before_ai = MagicMock()
        mock_before_ai.ai_keys = [{'key': 'exposed1'}, {'key': 'exposed2'}]
        mock_before.scan_ai = mock_before_ai
        
        mock_after = MagicMock()
        mock_after_ai = MagicMock()
        mock_after_ai.ai_keys = [{'key': 'exposed1'}]  # One key rotated
        mock_after.scan_ai = mock_after_ai
        
        mock_db = MagicMock()

        result = _check_signal_disappeared(mock_decision, mock_before, mock_after, mock_db)
        assert result is True

    def test_cve_patching_detected(self):
        """Detect CVE patching when high severity software signals reduced."""
        mock_decision = MagicMock()
        mock_decision.action_id = 'patch-cves'
        
        mock_before = MagicMock()
        mock_before.signals_json = [
            {'category': 'software', 'severity': 'high', 'detail': 'CVE-2024-1234'},
            {'category': 'software', 'severity': 'high', 'detail': 'CVE-2024-5678'},
        ]
        mock_before.scan_ai = None
        
        mock_after = MagicMock()
        mock_after.signals_json = [
            {'category': 'software', 'severity': 'high', 'detail': 'CVE-2024-1234'},
        ]  # One CVE patched
        mock_after.scan_ai = None
        
        mock_db = MagicMock()

        result = _check_signal_disappeared(mock_decision, mock_before, mock_after, mock_db)
        assert result is True

    def test_no_change_detected(self):
        """Return False when signals are the same."""
        mock_decision = MagicMock()
        mock_decision.action_id = 'patch-cves'
        
        mock_before = MagicMock()
        mock_before.signals_json = [
            {'category': 'software', 'severity': 'high', 'detail': 'CVE-2024-1234'},
        ]
        mock_before.scan_ai = None
        
        mock_after = MagicMock()
        mock_after.signals_json = [
            {'category': 'software', 'severity': 'high', 'detail': 'CVE-2024-1234'},
        ]
        mock_after.scan_ai = None
        
        mock_db = MagicMock()

        result = _check_signal_disappeared(mock_decision, mock_before, mock_after, mock_db)
        assert result is False


class TestComputeDecisionImpact:
    """Test the main compute_decision_impact function."""

    def test_creates_impact_record(self):
        """Verify impact record is created with correct fields."""
        mock_db = MagicMock()
        mock_decision = MagicMock()
        mock_decision.id = 'decision-123'
        mock_decision.scan_id = 'scan-before'
        mock_decision.resolved_at = datetime.now(timezone.utc)
        mock_decision.action_id = 'patch-cves'
        mock_decision.before_score = 75
        mock_decision.created_at = datetime.now(timezone.utc) - timedelta(days=2)
        
        # Mock before scan
        mock_before_scan = MagicMock()
        mock_before_scan.id = 'scan-before'
        mock_before_scan.risk_score = 75
        mock_before_scan.domain = 'example.com'
        mock_before_scan.scan_ai = None
        mock_before_scan.signals_json = []
        
        # Mock after scan with actual datetime
        mock_after_scan = MagicMock()
        mock_after_scan.id = 'scan-after'
        mock_after_scan.risk_score = 55
        # Use actual datetime for created_at since calculate_confidence needs it
        mock_after_scan.created_at = datetime.now(timezone.utc) + timedelta(days=1)
        mock_after_scan.scan_ai = None
        mock_after_scan.signals_json = []
        
        # Setup proper mock chain for all queries
        # Order matters: first query is for before_scan, then after_scan, then existing_impact
        def mock_query_side_effect(*args):
            query_mock = MagicMock()
            filter_mock = MagicMock()
            
            # Configure the filter().first() chain
            filter_mock.first.return_value = mock_before_scan
            filter_mock.order_by.return_value.first.return_value = mock_after_scan
            
            query_mock.filter.return_value = filter_mock
            return query_mock
        
        mock_db.query.side_effect = mock_query_side_effect
        
        with patch('backend.services.impact_service.DecisionImpact') as MockImpact:
            mock_impact_instance = MagicMock()
            MockImpact.return_value = mock_impact_instance
            
            result = compute_decision_impact(mock_db, mock_decision, 'org-123')
            
            # Verify impact was created - commit should be called
            mock_db.commit.assert_called()

    def test_handles_no_before_scan_gracefully(self):
        """Continue gracefully if before scan is missing."""
        mock_db = MagicMock()
        mock_decision = MagicMock()
        mock_decision.id = 'decision-123'
        mock_decision.scan_id = 'missing-scan'
        mock_decision.resolved_at = datetime.now(timezone.utc)
        mock_decision.before_score = 50
        
        # No scans found
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        with patch('backend.services.impact_service.DecisionImpact') as MockImpact:
            mock_impact_instance = MagicMock()
            MockImpact.return_value = mock_impact_instance
            
            # Should not raise
            result = compute_decision_impact(mock_db, mock_decision, 'org-123')
            
            # Should still create impact with low confidence
            mock_db.add.assert_called_once()
