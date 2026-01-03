"""Tests for Phase 1.1 structural refinements."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from sqlalchemy.orm import Session

from backend.db import get_session
from backend.models import Company, Scan, ScanAI
from backend.services.ai.ai_registry_loader import (
    get_signal_category,
    get_signal_info,
    get_signal_remediation,
    get_signal_severity,
    reload_registry,
)


def test_company_creation(db_session: Session):
    """Test that Company can be created and queried."""
    company = Company(
        id="test-company-1",
        primary_domain="example.com",
        name="Example Corp",
    )
    db_session.add(company)
    db_session.commit()
    
    # Verify it was created
    found = db_session.query(Company).filter(Company.primary_domain == "example.com").first()
    assert found is not None
    assert found.id == "test-company-1"
    assert found.name == "Example Corp"
    assert found.primary_domain == "example.com"


def test_scan_linked_to_company(db_session: Session):
    """Test that Scan can be linked to a Company."""
    # Create company
    company = Company(
        id="test-company-2",
        primary_domain="test.com",
    )
    db_session.add(company)
    db_session.flush()
    
    # Create scan linked to company
    scan = Scan(
        id="test-scan-1",
        domain="test.com",
        risk_score=50,
        risk_likelihood_30d=0.3,
        risk_likelihood_90d=0.5,
        categories_json={},
        signals_json=[],
        summary="Test summary",
        raw_payload={},
        company_id=company.id,
    )
    db_session.add(scan)
    db_session.commit()
    
    # Verify relationship
    found_scan = db_session.query(Scan).filter(Scan.id == "test-scan-1").first()
    assert found_scan is not None
    assert found_scan.company_id == company.id
    assert found_scan.company is not None
    assert found_scan.company.primary_domain == "test.com"
    
    # Verify reverse relationship
    company_scans = db_session.query(Scan).filter(Scan.company_id == company.id).all()
    assert len(company_scans) == 1
    assert company_scans[0].id == "test-scan-1"


def test_scan_ai_model(db_session: Session):
    """Test that ScanAI model can be created and queried."""
    # Create company and scan first
    company = Company(
        id="test-company-3",
        primary_domain="ai-test.com",
    )
    db_session.add(company)
    db_session.flush()
    
    scan = Scan(
        id="test-scan-2",
        domain="ai-test.com",
        risk_score=30,
        risk_likelihood_30d=0.2,
        risk_likelihood_90d=0.4,
        categories_json={},
        signals_json=[],
        summary="Test summary",
        raw_payload={},
        company_id=company.id,
    )
    db_session.add(scan)
    db_session.flush()
    
    # Create ScanAI
    scan_ai = ScanAI(
        id="test-scan-ai-1",
        scan_id=scan.id,
        ai_tools=["openai", "langchain"],
        ai_vendors=[{"name": "OpenAI", "risk": "medium"}],
        ai_keys=[],
        ai_score=0,
        ai_summary=None,
    )
    db_session.add(scan_ai)
    db_session.commit()
    
    # Verify it was created
    found = db_session.query(ScanAI).filter(ScanAI.scan_id == scan.id).first()
    assert found is not None
    assert found.id == "test-scan-ai-1"
    assert found.ai_tools == ["openai", "langchain"]
    assert found.ai_score == 0
    
    # Verify relationship
    assert found.scan is not None
    assert found.scan.id == scan.id
    assert scan.scan_ai is not None
    assert scan.scan_ai.id == found.id


def test_company_auto_creation_on_scan():
    """Test that a Company is automatically created when scanning a new domain."""
    # This test verifies the scan flow creates companies
    # The actual implementation is in routes/scan.py
    # We'll test this via the scan endpoint in integration tests
    pass


def test_risk_registry_loader():
    """Test that risk_registry.json loads correctly."""
    # Force reload
    reload_registry()
    
    # Test direct lookup
    info = get_signal_info("http_header_strict_transport_security_missing")
    assert info["severity"] == "high"
    assert info["category"] == "network"
    assert "HSTS" in info["remediation"]
    
    # Test pattern matching
    info = get_signal_info("cve_CVE-2024-12345")
    assert info["severity"] == "variable"
    assert info["category"] == "software"
    
    # Test missing signal (should return defaults)
    info = get_signal_info("nonexistent_signal")
    assert info["severity"] == "low"
    assert info["category"] == "software"
    assert "Review" in info["remediation"]


def test_risk_registry_helper_functions():
    """Test helper functions for risk registry."""
    # Test get_signal_severity
    severity = get_signal_severity("http_header_strict_transport_security_missing")
    assert severity == "high"
    
    # Test get_signal_category
    category = get_signal_category("http_header_strict_transport_security_missing")
    assert category == "network"
    
    # Test get_signal_remediation
    remediation = get_signal_remediation("http_header_strict_transport_security_missing")
    assert "HSTS" in remediation
    assert len(remediation) > 0


@pytest.fixture
def db_session():
    """Provide a database session for tests."""
    with get_session() as session:
        yield session
        # Cleanup: delete test data
        session.query(ScanAI).filter(ScanAI.id.like("test-%")).delete()
        session.query(Scan).filter(Scan.id.like("test-%")).delete()
        session.query(Company).filter(Company.id.like("test-%")).delete()
        session.commit()

