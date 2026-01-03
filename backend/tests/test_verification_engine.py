"""
Tests for Verification Engine - Phase 2.3

Tests the deterministic verification rules and confidence tiers.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch


# =============================================================================
# Confidence Tier Tests
# =============================================================================

class TestConfidenceTiers:
    """Test confidence tier calculation."""
    
    def test_high_confidence_recent_scan_signal_gone(self):
        """High confidence when recent scan confirms signal is gone."""
        from backend.services.verification_engine import calculate_confidence_tier
        
        decision = MagicMock()
        decision.resolved_at = datetime.now(timezone.utc) - timedelta(days=1)
        
        latest_scan = MagicMock()
        latest_scan.created_at = datetime.now(timezone.utc) - timedelta(hours=12)
        
        confidence, reason = calculate_confidence_tier(decision, latest_scan, signal_gone=True)
        
        assert confidence == 1.0
        assert "High" in reason
    
    def test_medium_confidence_recent_scan_signal_unclear(self):
        """Medium confidence when recent scan but signal status unclear."""
        from backend.services.verification_engine import calculate_confidence_tier
        
        decision = MagicMock()
        decision.resolved_at = datetime.now(timezone.utc) - timedelta(days=1)
        
        latest_scan = MagicMock()
        latest_scan.created_at = datetime.now(timezone.utc) - timedelta(hours=12)
        
        confidence, reason = calculate_confidence_tier(decision, latest_scan, signal_gone=False)
        
        assert confidence == 0.7
        assert "Medium" in reason
    
    def test_low_confidence_old_scan(self):
        """Low confidence when scan is older than 7 days."""
        from backend.services.verification_engine import calculate_confidence_tier
        
        decision = MagicMock()
        decision.resolved_at = datetime.now(timezone.utc) - timedelta(days=10)
        
        latest_scan = MagicMock()
        latest_scan.created_at = datetime.now(timezone.utc) - timedelta(days=9)
        
        confidence, reason = calculate_confidence_tier(decision, latest_scan, signal_gone=True)
        
        assert confidence == 0.4
        assert "Low" in reason
    
    def test_very_low_confidence_no_scan(self):
        """Very low confidence when no scan after resolution."""
        from backend.services.verification_engine import calculate_confidence_tier
        
        decision = MagicMock()
        decision.resolved_at = datetime.now(timezone.utc) - timedelta(days=1)
        
        confidence, reason = calculate_confidence_tier(decision, None, signal_gone=False)
        
        assert confidence == 0.2
        assert "Very Low" in reason


# =============================================================================
# Verification Rule Tests
# =============================================================================

class TestVerificationRules:
    """Test individual verification rules."""
    
    @pytest.mark.asyncio
    async def test_hsts_verification_pass(self):
        """Test HSTS verification when header is now present."""
        from backend.services.verification_engine import verify_hsts_enabled
        
        decision = MagicMock()
        decision.scan = MagicMock()
        decision.scan.domain = "example.com"
        decision.scan.signals_json = [{"detail": "Missing HSTS header", "severity": "high"}]
        decision.resolved_at = datetime.now(timezone.utc)
        
        latest_scan = MagicMock()
        latest_scan.created_at = datetime.now(timezone.utc)
        
        db = MagicMock()
        
        with patch('backend.services.verification_engine.http_service.fetch_http_metadata') as mock_http:
            # Return format: (metadata, signals, tech_tokens)
            mock_http.return_value = (
                {"headers": {"strict-transport-security": "max-age=31536000"}},
                [],
                []
            )
            
            result, confidence, evidence, notes = await verify_hsts_enabled(decision, latest_scan, db)
            
            assert result == "pass"
            assert confidence > 0.5
            assert evidence["after"]["hsts_present"] == True
    
    @pytest.mark.asyncio
    async def test_hsts_verification_fail(self):
        """Test HSTS verification when header is still missing."""
        from backend.services.verification_engine import verify_hsts_enabled
        
        decision = MagicMock()
        decision.scan = MagicMock()
        decision.scan.domain = "example.com"
        decision.scan.signals_json = []
        
        latest_scan = MagicMock()
        db = MagicMock()
        
        with patch('backend.services.verification_engine.http_service.fetch_http_metadata') as mock_http:
            mock_http.return_value = (
                {"headers": {}},  # No HSTS header
                [],
                []
            )
            
            result, confidence, evidence, notes = await verify_hsts_enabled(decision, latest_scan, db)
            
            assert result == "fail"
            assert "still missing" in notes.lower()
    
    @pytest.mark.asyncio  
    async def test_cve_verification_pass(self):
        """Test CVE verification when CVEs are patched."""
        from backend.services.verification_engine import verify_cve_patched
        
        decision = MagicMock()
        decision.scan = MagicMock()
        decision.scan.signals_json = [
            {"type": "cve", "detail": "CVE-2023-1234", "severity": "high"}
        ]
        decision.resolved_at = datetime.now(timezone.utc)
        
        latest_scan = MagicMock()
        latest_scan.signals_json = []  # No CVEs anymore
        latest_scan.created_at = datetime.now(timezone.utc)
        
        db = MagicMock()
        
        result, confidence, evidence, notes = await verify_cve_patched(decision, latest_scan, db)
        
        assert result == "pass"
        assert "resolved" in notes.lower()
        assert evidence["before"]["cve_count"] == 1
        assert evidence["after"]["cve_count"] == 0
    
    @pytest.mark.asyncio
    async def test_cve_verification_fail(self):
        """Test CVE verification when CVEs still present."""
        from backend.services.verification_engine import verify_cve_patched
        
        decision = MagicMock()
        decision.scan = MagicMock()
        decision.scan.signals_json = [
            {"type": "cve", "detail": "CVE-2023-1234"}
        ]
        
        latest_scan = MagicMock()
        latest_scan.signals_json = [
            {"type": "cve", "detail": "CVE-2023-1234"}
        ]
        latest_scan.created_at = datetime.now(timezone.utc)
        
        db = MagicMock()
        
        result, confidence, evidence, notes = await verify_cve_patched(decision, latest_scan, db)
        
        assert result == "fail"
        assert evidence["after"]["cve_count"] == 1


# =============================================================================
# Verification Run Tests  
# =============================================================================

class TestVerificationRun:
    """Test the main verification run function."""
    
    @pytest.mark.asyncio
    async def test_unknown_action_id(self):
        """Test handling of unknown action_id."""
        from backend.services.verification_engine import run_verification
        
        decision = MagicMock()
        decision.id = "test-decision-id"
        decision.action_id = "unknown-action"
        decision.scan = MagicMock()
        decision.scan.domain = "example.com"
        decision.resolved_at = datetime.now(timezone.utc)
        decision.created_at = datetime.now(timezone.utc)
        
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        
        run = await run_verification(db, decision)
        
        assert run.result == "unknown"
        assert "No verification rule" in run.notes


# =============================================================================
# Integration Tests
# =============================================================================

class TestVerificationIntegration:
    """Integration tests for verification workflow."""
    
    def test_verification_rules_mapping(self):
        """Verify all expected action IDs have rules."""
        from backend.services.verification_engine import VERIFICATION_RULES
        
        expected_actions = [
            'key-rotation',
            'patch-cves',
            'enable-hsts',
            'update-tls',
            'review-agents',
        ]
        
        for action in expected_actions:
            assert action in VERIFICATION_RULES, f"Missing rule for {action}"
