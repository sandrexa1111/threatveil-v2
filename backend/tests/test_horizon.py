"""
Horizon API Tests

Tests for the Phase 1.2 Horizon features:
- Horizon aggregation endpoint
- Weekly brief service
- AI posture calculations
"""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db import Base
from backend.dependencies import get_db
from backend.main import app
from backend.models import Organization, Scan, ScanAI, SecurityDecision, Signal


# =============================================================================
# Test Setup
# =============================================================================

@pytest.fixture
def test_db():
    """Create a fresh test database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestingSessionLocal()
    
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    """Create test client with database override."""
    return TestClient(app)


@pytest.fixture
def sample_org(test_db):
    """Create a sample organization."""
    org = Organization(
        id=str(uuid.uuid4()),
        name="Test Org",
        primary_domain="test.com",
    )
    test_db.add(org)
    test_db.commit()
    return org


@pytest.fixture
def sample_scan(test_db, sample_org):
    """Create a sample scan with AI data."""
    scan = Scan(
        id=str(uuid.uuid4()),
        org_id=sample_org.id,
        domain="test.com",
        risk_score=45,
        risk_likelihood_30d=0.3,
        risk_likelihood_90d=0.5,
        categories_json={},
        signals_json=[
            {"severity": "high", "category": "software", "detail": "Test CVE"},
            {"severity": "medium", "category": "network", "detail": "Test network issue"},
        ],
        summary="Test scan summary",
        raw_payload={},
        created_at=datetime.now(timezone.utc),
    )
    test_db.add(scan)
    
    # Add ScanAI data
    scan_ai = ScanAI(
        id=str(uuid.uuid4()),
        scan_id=scan.id,
        ai_tools=["langchain", "openai"],
        ai_vendors=["OpenAI", "Anthropic"],
        ai_keys=[],
        ai_score=25,
        ai_summary="Test AI summary",
        created_at=datetime.now(timezone.utc),
    )
    test_db.add(scan_ai)
    test_db.commit()
    
    return scan


@pytest.fixture
def sample_decision(test_db, sample_scan):
    """Create a sample security decision."""
    decision = SecurityDecision(
        id=str(uuid.uuid4()),
        scan_id=sample_scan.id,
        action_id="patch-cves",
        title="Patch Critical Vulnerabilities",
        recommended_fix="Apply vendor patches",
        effort_estimate="2-4 hours",
        estimated_risk_reduction=20,
        priority=1,
        status="pending",
        before_score=45,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_db.add(decision)
    test_db.commit()
    return decision


@pytest.fixture
def sample_signal(test_db, sample_org, sample_scan):
    """Create a sample signal."""
    signal = Signal(
        id=str(uuid.uuid4()),
        org_id=sample_org.id,
        scan_id=sample_scan.id,
        source="threatveil_external",
        type="cve",
        severity="high",
        category="software",
        title="Critical CVE Found",
        detail="CVE-2024-1234",
        evidence={
            "source_service": "nvd",
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "raw": {},
        },
        created_at=datetime.now(timezone.utc),
    )
    test_db.add(signal)
    test_db.commit()
    return signal


# =============================================================================
# Horizon Endpoint Tests
# =============================================================================

def test_horizon_endpoint_empty_org(client, sample_org):
    """Test Horizon endpoint returns defaults for org with no scans."""
    response = client.get(f"/api/v1/org/{sample_org.id}/horizon")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["current_risk_score"] == 0
    assert data["risk_trend"] == 0
    assert data["top_decisions"] == []
    assert data["unresolved_critical_signals"] == 0
    assert data["ai_posture"]["score"] == 0
    assert data["ai_posture"]["status"] == "clean"


def test_horizon_endpoint_with_data(client, sample_org, sample_scan, sample_decision, sample_signal):
    """Test Horizon endpoint aggregates data correctly."""
    response = client.get(f"/api/v1/org/{sample_org.id}/horizon")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["current_risk_score"] == 45  # From sample_scan
    assert data["risk_trend"] == 0  # No previous scan to compare
    assert len(data["top_decisions"]) == 1
    assert data["top_decisions"][0]["title"] == "Patch Critical Vulnerabilities"
    assert data["unresolved_critical_signals"] == 1  # sample_signal is high severity
    assert data["ai_posture"]["score"] == 25  # From sample_scan_ai
    assert data["ai_posture"]["status"] == "warning"  # 25 is in warning range


def test_horizon_endpoint_org_not_found(client):
    """Test Horizon endpoint returns 404 for non-existent org."""
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/org/{fake_id}/horizon")
    
    assert response.status_code == 404


def test_horizon_ai_posture_status_levels(client, test_db, sample_org):
    """Test AI posture status correctly maps to score thresholds."""
    # Create scan with high AI score
    scan = Scan(
        id=str(uuid.uuid4()),
        org_id=sample_org.id,
        domain="test.com",
        risk_score=75,
        risk_likelihood_30d=0.6,
        risk_likelihood_90d=0.8,
        categories_json={},
        signals_json=[],
        summary="High risk scan",
        raw_payload={},
        created_at=datetime.now(timezone.utc),
    )
    test_db.add(scan)
    
    scan_ai = ScanAI(
        id=str(uuid.uuid4()),
        scan_id=scan.id,
        ai_tools=["langchain"],
        ai_vendors=[],
        ai_keys=[{"key": "exposed"}],  # Key leak
        ai_score=75,  # High AI risk
        ai_summary="Critical AI exposure",
        created_at=datetime.now(timezone.utc),
    )
    test_db.add(scan_ai)
    test_db.commit()
    
    response = client.get(f"/api/v1/org/{sample_org.id}/horizon")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["ai_posture"]["score"] == 75
    assert data["ai_posture"]["status"] == "critical"  # >50 is critical


# =============================================================================
# Weekly Brief Endpoint Tests
# =============================================================================

def test_weekly_brief_empty_org(client, sample_org):
    """Test weekly brief returns sensible defaults for org with no data."""
    response = client.get(f"/api/v1/org/{sample_org.id}/weekly-brief?include_explanation=false")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "headline" in data
    assert data["top_changes"] == []
    assert data["top_3_actions"] == []
    assert data["confidence_level"] == "low"  # No data = low confidence


def test_weekly_brief_with_data(client, sample_org, sample_scan, sample_decision, sample_signal):
    """Test weekly brief correctly aggregates data."""
    response = client.get(f"/api/v1/org/{sample_org.id}/weekly-brief?include_explanation=false")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "headline" in data
    assert len(data["top_3_actions"]) == 1  # One pending decision
    assert data["top_3_actions"][0]["title"] == "Patch Critical Vulnerabilities"
    assert "generated_at" in data


def test_weekly_brief_deterministic_without_gemini(client, sample_org, sample_scan):
    """Test brief works fully without Gemini (fallback mode)."""
    with patch("backend.services.weekly_brief_service.settings") as mock_settings:
        mock_settings.gemini_api_key = None  # Disable Gemini
        
        response = client.get(f"/api/v1/org/{sample_org.id}/weekly-brief")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still have all fields
        assert "headline" in data
        assert "top_changes" in data
        assert "top_3_actions" in data
        assert "ai_exposure_summary" in data
        assert "confidence_level" in data


def test_weekly_brief_org_not_found(client):
    """Test weekly brief returns 404 for non-existent org."""
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/org/{fake_id}/weekly-brief")
    
    assert response.status_code == 404


# =============================================================================
# Weekly Brief Service Unit Tests
# =============================================================================

def test_build_headline_risk_decrease():
    """Test headline generation for risk decrease."""
    from backend.services.weekly_brief_service import build_headline
    
    headline = build_headline(current_score=42, delta=-8, resolved_count=2)
    assert "decreased by 8" in headline


def test_build_headline_risk_increase():
    """Test headline generation for risk increase."""
    from backend.services.weekly_brief_service import build_headline
    
    headline = build_headline(current_score=50, delta=10, resolved_count=0)
    assert "increased by 10" in headline
    assert "action needed" in headline


def test_build_headline_stable():
    """Test headline generation for stable risk."""
    from backend.services.weekly_brief_service import build_headline
    
    headline = build_headline(current_score=35, delta=0, resolved_count=0)
    assert "stable" in headline


def test_build_confidence_level():
    """Test confidence level determination."""
    from backend.services.weekly_brief_service import build_confidence_level
    
    # No recent scan = low
    assert build_confidence_level(has_recent_scan=False, signal_count=10, decision_count=5) == "low"
    
    # Recent scan + high data = high
    assert build_confidence_level(has_recent_scan=True, signal_count=10, decision_count=2) == "high"
    
    # Recent scan + some data = medium
    assert build_confidence_level(has_recent_scan=True, signal_count=3, decision_count=0) == "medium"


def test_fallback_explanation():
    """Test fallback explanation generates without errors."""
    from backend.services.weekly_brief_service import fallback_explanation
    from backend.schemas import WeeklyBriefResponse, DecisionSummary
    
    brief = WeeklyBriefResponse(
        headline="Test headline",
        top_changes=["Fixed issue 1", "Fixed issue 2"],
        top_3_actions=[
            DecisionSummary(
                id="1",
                title="Test Action",
                effort_estimate="1h",
                estimated_risk_reduction=10,
                priority=1,
                status="pending",
            )
        ],
        ai_exposure_summary="Clean",
        confidence_level="high",
    )
    
    explanation = fallback_explanation(brief)
    assert len(explanation) > 0
    assert "Test Action" in explanation or "Fixed issue" in explanation


# =============================================================================
# Risk Memory Utility Tests
# =============================================================================

def test_get_risk_delta_no_scans(test_db, sample_org):
    """Test risk delta returns zeros when no scans exist."""
    from backend.services.weekly_brief_service import get_risk_delta
    
    score, delta = get_risk_delta(test_db, sample_org.id)
    
    assert score == 0
    assert delta == 0


def test_get_risk_delta_with_scans(test_db, sample_org):
    """Test risk delta calculates correctly with multiple scans."""
    from backend.services.weekly_brief_service import get_risk_delta
    
    # Create old scan
    old_scan = Scan(
        id=str(uuid.uuid4()),
        org_id=sample_org.id,
        domain="test.com",
        risk_score=60,
        risk_likelihood_30d=0.5,
        risk_likelihood_90d=0.7,
        categories_json={},
        signals_json=[],
        summary="Old scan",
        raw_payload={},
        created_at=datetime.now(timezone.utc) - timedelta(days=10),
    )
    test_db.add(old_scan)
    
    # Create new scan
    new_scan = Scan(
        id=str(uuid.uuid4()),
        org_id=sample_org.id,
        domain="test.com",
        risk_score=45,
        risk_likelihood_30d=0.3,
        risk_likelihood_90d=0.5,
        categories_json={},
        signals_json=[],
        summary="New scan",
        raw_payload={},
        created_at=datetime.now(timezone.utc),
    )
    test_db.add(new_scan)
    test_db.commit()
    
    score, delta = get_risk_delta(test_db, sample_org.id)
    
    assert score == 45  # Current score
    assert delta == -15  # 45 - 60 = -15 (improved)
