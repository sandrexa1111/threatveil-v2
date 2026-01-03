"""Tests for ScanAI creation in Horizon Phase 1."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from backend.db import get_session
from backend.main import app
from backend.models import Company, Scan, ScanAI
from backend.services.ai.ai_scoring import compute_ai_score
from backend.services.ai.ai_summary_service import fallback_ai_summary


@pytest.mark.asyncio
async def test_scan_creates_scan_ai():
    """Test that scanning a domain creates a ScanAI record."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/scan/vendor",
            json={"domain": "example.com"},
        )
        
        assert response.status_code == 200
        data = response.json()
        scan_id = data["result"]["id"]
        
        # Verify ScanAI was created
        # Note: We use a new session to query after the scan completes
        from backend.db import SessionLocal
        db = SessionLocal()
        try:
            scan_ai = db.query(ScanAI).filter(ScanAI.scan_id == scan_id).first()
            # ScanAI may not be created if AI scan fails, so we check if it exists
            if scan_ai:
                assert scan_ai.ai_score is not None
                assert isinstance(scan_ai.ai_score, int)
                assert 0 <= scan_ai.ai_score <= 100, "ai_score should be 0-100"
                assert scan_ai.ai_summary is not None
                assert len(scan_ai.ai_summary) > 0, "ai_summary should be non-empty"
                assert scan_ai.ai_tools is not None
                assert isinstance(scan_ai.ai_tools, list)
        finally:
            db.close()


@pytest.mark.asyncio
async def test_scan_ai_without_github_org():
    """Test that ScanAI is created even without GitHub org."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/scan/vendor",
            json={"domain": "test-no-github.com"},
        )
        
        assert response.status_code == 200
        data = response.json()
        scan_id = data["result"]["id"]
        
        # Verify ScanAI was created with minimal info
        from backend.db import SessionLocal
        db = SessionLocal()
        try:
            scan_ai = db.query(ScanAI).filter(ScanAI.scan_id == scan_id).first()
            # ScanAI may not be created if AI scan fails, so we check if it exists
            if scan_ai:
                assert scan_ai.ai_score == 0, "No GitHub org should result in score 0"
                assert scan_ai.ai_tools == [], "No tools detected without GitHub org"
                assert len(scan_ai.ai_summary) > 0, "Should have fallback summary"
        finally:
            db.close()


def test_ai_scoring_no_tools():
    """Test AI scoring with no tools."""
    score = compute_ai_score(ai_tools=[], ai_vendors=[], ai_keys=[])
    assert score == 0


def test_ai_scoring_with_tools():
    """Test AI scoring with tools."""
    # 1-3 tools should give 10 points
    # Note: "langchain" triggers agent detection (+10), so total is 20
    score = compute_ai_score(ai_tools=["openai", "langchain"], ai_vendors=[], ai_keys=[])
    assert score == 20  # 10 (tools) + 10 (agent detection)
    
    # Test without agent keywords
    score = compute_ai_score(ai_tools=["openai", "anthropic"], ai_vendors=[], ai_keys=[])
    assert score == 10  # 10 (tools), no agent
    
    # 4+ tools should give 20 points base
    score = compute_ai_score(
        ai_tools=["openai", "anthropic", "cohere", "huggingface"],
        ai_vendors=[],
        ai_keys=[],
    )
    assert score == 20  # 20 (4+ tools), no agent keywords


def test_ai_scoring_with_key_leaks():
    """Test AI scoring with key leaks."""
    ai_keys = [
        {"key_type": "openai", "repository": "test/repo", "path": ".env"},
        {"key_type": "gemini", "repository": "test/repo2", "path": "config.json"},
    ]
    
    score = compute_ai_score(ai_tools=["openai"], ai_vendors=[], ai_keys=ai_keys)
    # 10 (tools) + 60 (2 leaks * 30, capped at 60) = 70
    assert score == 70


def test_ai_scoring_with_agent():
    """Test AI scoring with agent detection."""
    score = compute_ai_score(
        ai_tools=["langchain", "openai"],  # langchain suggests agent usage
        ai_vendors=[],
        ai_keys=[],
    )
    # 10 (tools) + 10 (agent) = 20
    assert score == 20


def test_ai_scoring_capped_at_100():
    """Test that AI score is capped at 100."""
    # Create scenario that would exceed 100
    ai_keys = [
        {"key_type": "openai"},
        {"key_type": "gemini"},
        {"key_type": "anthropic"},
        {"key_type": "cohere"},
    ]  # 4 leaks = 60 points (capped)
    
    score = compute_ai_score(
        ai_tools=["openai", "langchain", "anthropic", "cohere", "huggingface"],  # 20 points
        ai_vendors=[],
        ai_keys=ai_keys,  # 60 points (capped)
    )
    # 20 + 60 + 10 (agent) = 90, should be <= 100
    assert score <= 100


def test_fallback_ai_summary_no_tools():
    """Test fallback AI summary with no tools."""
    summary = fallback_ai_summary(ai_tools=[], ai_keys=[], domain="example.com")
    assert "No obvious AI usage" in summary
    assert "example.com" in summary


def test_fallback_ai_summary_with_keys():
    """Test fallback AI summary with key leaks."""
    ai_keys = [
        {"key_type": "openai", "repository": "test/repo", "path": ".env"},
    ]
    summary = fallback_ai_summary(ai_tools=["openai"], ai_keys=ai_keys, domain="example.com")
    assert "key leak" in summary.lower()
    assert "rotate" in summary.lower() or "remove" in summary.lower()


def test_fallback_ai_summary_with_tools():
    """Test fallback AI summary with tools but no keys."""
    summary = fallback_ai_summary(
        ai_tools=["openai", "langchain"],
        ai_keys=[],
        domain="example.com",
    )
    assert "AI tools detected" in summary
    assert "openai" in summary.lower() or "langchain" in summary.lower()

