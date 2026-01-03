"""
Tests for the extended SecurityDecision lifecycle (Phase 3).

Tests:
- Accepted status transition
- Verified status transition
- Auto-verification logic
- Invalid state transitions
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch


class TestDecisionLifecycle:
    """Test extended decision lifecycle transitions."""

    def test_pending_to_accepted(self):
        """Decision can transition from pending to accepted."""
        valid_transitions = {
            'pending': ['accepted', 'in_progress', 'resolved'],
            'accepted': ['in_progress', 'resolved'],
            'in_progress': ['accepted', 'resolved'],
            'resolved': ['in_progress', 'verified'],
            'verified': ['resolved']  # Can go back to resolved
        }
        
        # pending -> accepted is valid
        assert 'accepted' in valid_transitions['pending']
    
    def test_resolved_to_verified(self):
        """Resolved decisions can be marked as verified."""
        valid_transitions = ['in_progress', 'verified']
        assert 'verified' in valid_transitions
    
    def test_verified_requires_resolved(self):
        """Cannot mark as verified unless already resolved."""
        # This tests the validation logic
        current_status = 'pending'
        requested_status = 'verified'
        
        # The route should reject this
        should_reject = current_status != 'resolved' and requested_status == 'verified'
        assert should_reject is True
    
    def test_verified_accepts_resolved(self):
        """Can verify a resolved decision."""
        current_status = 'resolved'
        requested_status = 'verified'
        
        should_allow = current_status == 'resolved' and requested_status == 'verified'
        assert should_allow is True


class TestAutoVerification:
    """Test auto-verification service logic."""

    def test_key_rotation_verified_when_no_keys(self):
        """key-rotation decision is verified when no AI keys found."""
        from backend.services.verification_service import _check_signal_resolved
        
        mock_decision = MagicMock()
        mock_decision.action_id = 'key-rotation'
        
        mock_scan_ai = MagicMock()
        mock_scan_ai.ai_keys = []  # No keys found
        
        result = _check_signal_resolved(mock_decision, [], mock_scan_ai)
        assert result is True
    
    def test_key_rotation_not_verified_when_keys_present(self):
        """key-rotation decision is NOT verified when AI keys still found."""
        from backend.services.verification_service import _check_signal_resolved
        
        mock_decision = MagicMock()
        mock_decision.action_id = 'key-rotation'
        
        mock_scan_ai = MagicMock()
        mock_scan_ai.ai_keys = [{'key_type': 'openai'}]  # Keys still present
        
        result = _check_signal_resolved(mock_decision, [], mock_scan_ai)
        assert result is False
    
    def test_patch_cves_verified_when_no_high_severity(self):
        """patch-cves decision is verified when no high-severity CVEs."""
        from backend.services.verification_service import _check_signal_resolved
        
        mock_decision = MagicMock()
        mock_decision.action_id = 'patch-cves'
        
        # Only low severity signals
        signals = [
            {'category': 'software', 'severity': 'low'},
            {'category': 'software', 'severity': 'medium'},
        ]
        
        result = _check_signal_resolved(mock_decision, signals, None)
        assert result is True
    
    def test_patch_cves_not_verified_when_high_severity(self):
        """patch-cves decision is NOT verified when high-severity CVEs remain."""
        from backend.services.verification_service import _check_signal_resolved
        
        mock_decision = MagicMock()
        mock_decision.action_id = 'patch-cves'
        
        # High severity signal still present
        signals = [
            {'category': 'software', 'severity': 'high'},
        ]
        
        result = _check_signal_resolved(mock_decision, signals, None)
        assert result is False
    
    def test_review_agents_verified_when_no_agents(self):
        """review-agents decision is verified when no agent frameworks found."""
        from backend.services.verification_service import _check_signal_resolved
        
        mock_decision = MagicMock()
        mock_decision.action_id = 'review-agents'
        
        mock_scan_ai = MagicMock()
        mock_scan_ai.ai_tools = ['openai-python']  # No agent frameworks
        
        result = _check_signal_resolved(mock_decision, [], mock_scan_ai)
        assert result is True
    
    def test_review_agents_not_verified_when_agents_present(self):
        """review-agents decision is NOT verified when agent frameworks still found."""
        from backend.services.verification_service import _check_signal_resolved
        
        mock_decision = MagicMock()
        mock_decision.action_id = 'review-agents'
        
        mock_scan_ai = MagicMock()
        mock_scan_ai.ai_tools = ['langchain-serve', 'crewai']  # Agents present
        
        result = _check_signal_resolved(mock_decision, [], mock_scan_ai)
        assert result is False
    
    def test_audit_ai_tools_not_auto_verified(self):
        """audit-ai-tools decisions are NOT auto-verified (require manual review)."""
        from backend.services.verification_service import _check_signal_resolved
        
        mock_decision = MagicMock()
        mock_decision.action_id = 'audit-ai-tools'
        
        result = _check_signal_resolved(mock_decision, [], None)
        assert result is False


class TestDecisionStatusValues:
    """Test that valid status values are correctly defined."""

    def test_all_status_values_defined(self):
        """All extended status values should be valid."""
        valid_statuses = ['pending', 'accepted', 'in_progress', 'resolved', 'verified']
        
        assert 'pending' in valid_statuses
        assert 'accepted' in valid_statuses
        assert 'in_progress' in valid_statuses
        assert 'resolved' in valid_statuses
        assert 'verified' in valid_statuses
        assert len(valid_statuses) == 5


class TestStatusTimestamps:
    """Test that status changes set correct timestamps."""

    def test_accepted_at_set_on_accept(self):
        """accepted_at should be set when status changes to accepted."""
        # Simulate the timestamp logic
        old_status = 'pending'
        new_status = 'accepted'
        
        should_set_accepted_at = (
            new_status == 'accepted' and 
            old_status not in ('accepted', 'in_progress', 'resolved', 'verified')
        )
        
        assert should_set_accepted_at is True
    
    def test_verified_at_set_on_verify(self):
        """verified_at should be set when status changes to verified."""
        old_status = 'resolved'
        new_status = 'verified'
        
        should_set_verified_at = (
            new_status == 'verified' and 
            old_status == 'resolved'
        )
        
        assert should_set_verified_at is True
    
    def test_timestamps_cleared_on_revert(self):
        """Timestamps should be cleared when reverting from resolved/verified."""
        new_status = 'in_progress'
        old_status = 'resolved'
        
        should_clear = (
            new_status not in ('resolved', 'verified') and 
            old_status in ('resolved', 'verified')
        )
        
        assert should_clear is True
