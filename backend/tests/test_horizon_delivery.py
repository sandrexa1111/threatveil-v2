
import pytest
from unittest.mock import patch, AsyncMock, MagicMock, Mock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.main import app
from backend.models import Organization, Scan, ScanAI
from backend.services.pdf_generator import generate_brief_pdf
from backend.services.weekly_brief_service import build_weekly_brief
from backend.schemas import WeeklyBriefResponse, DecisionSummary

client = TestClient(app)

# Mock Brief for testing
MOCK_BRIEF = WeeklyBriefResponse(
    headline="Risk decreased by 5 points",
    top_changes=["Resolved: Fix SQL Injection"],
    top_3_actions=[
        DecisionSummary(
            id="dec-1",
            title="Rotate API Keys",
            effort_estimate="Low",
            estimated_risk_reduction=15,
            priority=1,
            status="pending"
        )
    ],
    ai_exposure_summary="Clean AI posture",
    confidence_level="high",
    explanation="Great job security team.",
    generated_at=datetime.now(timezone.utc),
    decision_impacts=[]
)

@pytest.fixture
def mock_settings():
    with patch("backend.routes.horizon.settings") as mock:
        mock.resend_api_key = "re_123456"
        mock.gemini_api_key = "gemini_key"
        yield mock

@pytest.fixture
def db_session():
    db = MagicMock(spec=Session)
    # Setup default org query behavior to avoid 404s
    org_mock = Mock()
    org_mock.id = "org-123"
    org_mock.name = "Test Corp"
    org_mock.primary_domain = "test.com"
    
    # query(Org).filter(...).first() -> org_mock
    db.query.return_value.filter.return_value.first.return_value = org_mock
    return db

@pytest.fixture(autouse=True)
def override_db(db_session):
    from backend.dependencies import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides = {}

def test_pdf_bytes_non_empty():
    """Test PDF generator returns bytes."""
    pdf_bytes = generate_brief_pdf(MOCK_BRIEF, "Test Org")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    # PDF signature
    assert pdf_bytes.startswith(b"%PDF")

def test_send_missing_resend_key(db_session):
    """Test 400 error when RESEND_API_KEY is missing."""
    with patch("backend.routes.horizon.settings") as settings:
        settings.resend_api_key = None
        
        response = client.post(
            "/api/v1/org/org-123/weekly-brief/send",
            json={"to": "test@example.com"}
        )
        assert response.status_code == 400
        assert "RESEND_API_KEY not configured" in response.json()["detail"]

def test_send_invalid_email(mock_settings, db_session):
    """Test 422 error for invalid email format."""
    response = client.post(
        "/api/v1/org/org-123/weekly-brief/send",
        json={"to": "invalid-email"}
    )
    assert response.status_code == 422
    assert "Invalid email address" in response.json()["detail"]

@patch("backend.routes.horizon.build_weekly_brief")
@patch("httpx.AsyncClient.post")
def test_send_success_mocked(mock_post, mock_build, mock_settings, db_session):
    """Test successful email sending with mocked Resend API."""
    # Disable Gemini to avoid extra API call in this test
    mock_settings.gemini_api_key = None
    
    # Setup mocks
    db_session.query().filter().first.return_value = Organization(
        id="org-123", name="Test Corp", primary_domain="test.com"
    )
    mock_build.return_value = MOCK_BRIEF
    
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"id": "msg_123456"}
    )
    
    response = client.post(
        "/api/v1/org/org-123/weekly-brief/send",
        json={"to": "admin@test.com", "include_explanation": True}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message_id"] == "msg_123456"
    assert data["status"] == "sent"
    
    # Verify Resend API call
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["to"] == ["admin@test.com"]
    assert "attachments" in kwargs["json"]

@patch("backend.routes.horizon.build_weekly_brief")
@patch("httpx.AsyncClient.post")
def test_send_gemini_disabled_fallback(mock_post, mock_build, mock_settings, db_session):
    """Test sending works even if Gemini is disabled/fails."""
    # Setup mocks
    mock_settings.gemini_api_key = None  # Gemini disabled
    
    db_session.query().filter().first.return_value = Organization(
        id="org-123", name="Test Corp", primary_domain="test.com"
    )
    mock_build.return_value = MOCK_BRIEF
    
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"id": "msg_123"}
    )
    
    response = client.post(
        "/api/v1/org/org-123/weekly-brief/send",
        json={"to": "admin@test.com", "include_explanation": True}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "sent"

