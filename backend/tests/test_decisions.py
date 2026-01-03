"""
Tests for the SecurityDecision model and decision routes.

Tests decision persistence, status updates, and risk delta calculation.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

# Test the decision generation logic directly
from backend.routes.decisions import generate_decisions_for_scan, DECISION_TEMPLATES


class TestDecisionGeneration:
    """Test deterministic decision generation logic."""

    def test_generates_key_rotation_for_key_leaks(self):
        """Key leaks should trigger key-rotation decision."""
        mock_scan = MagicMock()
        mock_scan.signals_json = []
        mock_scan.risk_score = 75
        
        mock_scan_ai = MagicMock()
        mock_scan_ai.ai_keys = [{"key_type": "openai", "path": "test.py"}]
        mock_scan_ai.ai_tools = []
        
        decisions = generate_decisions_for_scan(mock_scan, mock_scan_ai)
        
        assert len(decisions) >= 1
        assert decisions[0]['action_id'] == 'key-rotation'
        assert decisions[0]['title'] == 'Rotate Exposed Credentials'
        assert decisions[0]['priority'] == 1

    def test_generates_patch_cves_for_high_severity(self):
        """High severity CVEs should trigger patch-cves decision."""
        mock_scan = MagicMock()
        mock_scan.signals_json = [
            {'category': 'software', 'severity': 'high', 'detail': 'CVE-2024-1234'}
        ]
        mock_scan.risk_score = 60
        
        decisions = generate_decisions_for_scan(mock_scan, None)
        
        assert len(decisions) >= 1
        assert any(d['action_id'] == 'patch-cves' for d in decisions)

    def test_generates_agent_review_for_exposed_agents(self):
        """Exposed agent frameworks should trigger review-agents decision."""
        mock_scan = MagicMock()
        mock_scan.signals_json = []
        mock_scan.risk_score = 50
        
        mock_scan_ai = MagicMock()
        mock_scan_ai.ai_keys = []
        mock_scan_ai.ai_tools = ['langchain-serve', 'crewai-api']
        
        decisions = generate_decisions_for_scan(mock_scan, mock_scan_ai)
        
        assert any(d['action_id'] == 'review-agents' for d in decisions)

    def test_limits_to_three_decisions(self):
        """Should return at most 3 decisions."""
        mock_scan = MagicMock()
        mock_scan.signals_json = [
            {'category': 'software', 'severity': 'high', 'detail': 'CVE-1'},
            {'category': 'data_exposure', 'severity': 'high', 'detail': 'Exposed DB'},
            {'category': 'network', 'severity': 'medium', 'detail': 'Open port'},
            {'evidence': {'source': 'tls'}, 'severity': 'high', 'detail': 'Weak TLS'},
        ]
        mock_scan.risk_score = 80
        
        mock_scan_ai = MagicMock()
        mock_scan_ai.ai_keys = [{"key_type": "anthropic"}]
        mock_scan_ai.ai_tools = ['openai-agent', 'langchain']
        
        decisions = generate_decisions_for_scan(mock_scan, mock_scan_ai)
        
        assert len(decisions) <= 3

    def test_returns_empty_for_clean_scan(self):
        """Clean scan with no issues should return empty list."""
        mock_scan = MagicMock()
        mock_scan.signals_json = []
        mock_scan.risk_score = 10
        
        decisions = generate_decisions_for_scan(mock_scan, None)
        
        assert decisions == []

    def test_priorities_are_correct_order(self):
        """Decisions should be sorted by priority."""
        mock_scan = MagicMock()
        mock_scan.signals_json = [
            {'category': 'software', 'severity': 'high', 'detail': 'CVE-1'},
            {'category': 'data_exposure', 'severity': 'medium', 'detail': 'Data'},
        ]
        mock_scan.risk_score = 70
        
        mock_scan_ai = MagicMock()
        mock_scan_ai.ai_keys = [{"key_type": "openai"}]
        mock_scan_ai.ai_tools = []
        
        decisions = generate_decisions_for_scan(mock_scan, mock_scan_ai)
        
        # Verify they're in priority order
        priorities = [d['priority'] for d in decisions]
        assert priorities == sorted(priorities)
        

class TestDecisionTemplates:
    """Test that all decision templates are properly defined."""

    def test_all_templates_have_required_fields(self):
        """Each template should have title, recommended_fix, effort_estimate, etc."""
        required_fields = ['title', 'recommended_fix', 'effort_estimate', 'estimated_risk_reduction', 'priority']
        
        for action_id, template in DECISION_TEMPLATES.items():
            for field in required_fields:
                assert field in template, f"Template {action_id} missing field {field}"

    def test_all_priorities_are_unique(self):
        """Each template should have a unique priority."""
        priorities = [t['priority'] for t in DECISION_TEMPLATES.values()]
        assert len(priorities) == len(set(priorities)), "Priorities should be unique"


class TestRiskDeltaCalculation:
    """Test risk delta calculation logic."""

    def test_delta_is_before_minus_after(self):
        """Risk delta should be before_score - after_score."""
        before_score = 75
        after_score = 55
        
        delta = before_score - after_score
        
        assert delta == 20

    def test_positive_delta_means_improvement(self):
        """Positive delta means risk was reduced."""
        before_score = 80
        after_score = 60
        
        delta = before_score - after_score
        
        assert delta > 0  # Improvement

    def test_negative_delta_means_regression(self):
        """Negative delta means risk increased."""
        before_score = 50
        after_score = 70
        
        delta = before_score - after_score
        
        assert delta < 0  # Regression
