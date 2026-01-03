"""Tests for external API integrations with missing keys."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services import cve_service, github_service, llm_service, otx_service
from backend.schemas import Signal, Evidence
from datetime import datetime, timezone


def make_test_signal(signal_id: str, severity: str = "low") -> Signal:
    """Helper to create test signals."""
    return Signal(
        id=signal_id,
        type="http",
        detail="Test signal",
        severity=severity,
        category="network",
        evidence=Evidence(
            source="test",
            observed_at=datetime.now(timezone.utc),
            raw={},
        ),
    )


@pytest.mark.asyncio
async def test_gemini_missing_key():
    """Test that Gemini falls back when API key is missing."""
    with patch("backend.services.llm_service.settings") as mock_settings:
        mock_settings.gemini_api_key = None
        
        signals = [make_test_signal("test1", "high")]
        # Create a proper mock session with cache entry support
        session = MagicMock()
        session.get.return_value = None  # No cache entry
        
        summary = await llm_service.summarize(session, signals, 50, {"breach_likelihood_30d": 0.1, "breach_likelihood_90d": 0.2})
        
        assert summary is not None
        assert "Risk score" in summary or "50" in summary


@pytest.mark.asyncio
async def test_nvd_empty_tokens():
    """Test that NVD returns empty results for empty token list."""
    cves, signals = await cve_service.fetch_cves([])
    
    assert cves == []
    assert signals == []


@pytest.mark.asyncio
async def test_nvd_mock_response():
    """Test NVD with mocked successful response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "vulnerabilities": [
            {
                "cve": {
                    "id": "CVE-2024-1234",
                    "descriptions": [
                        {"lang": "en", "value": "Test CVE vulnerability description"}
                    ],
                    "published": "2024-01-15T10:00:00.000",
                    "metrics": {
                        "cvssMetricV31": [
                            {
                                "cvssData": {
                                    "baseScore": 8.5
                                }
                            }
                        ]
                    }
                }
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        cves, signals = await cve_service.fetch_cves(["nginx"])
        
        assert len(cves) == 1
        assert len(signals) == 1
        assert signals[0].type == "cve"
        assert signals[0].evidence.source == "nvd"
        assert signals[0].severity == "high"


@pytest.mark.asyncio
async def test_nvd_error_handling():
    """Test that NVD returns service error signal on failure."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=Exception("Connection timeout")
        )
        
        cves, signals = await cve_service.fetch_cves(["nginx"])
        
        assert cves == []
        assert len(signals) == 1
        assert signals[0].id.startswith("service_")
        assert signals[0].severity == "low"


@pytest.mark.asyncio
async def test_otx_missing_key():
    """Test that OTX returns service error signal when API key is missing."""
    with patch("backend.services.otx_service.settings") as mock_settings:
        mock_settings.otx_api_key = None
        
        metadata, signals = await otx_service.fetch_otx("example.com")
        
        assert metadata == {}
        assert len(signals) == 1
        assert signals[0].id.startswith("service_")
        assert signals[0].severity == "low"


@pytest.mark.asyncio
async def test_otx_mock_response():
    """Test OTX with mocked successful response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "pulse_info": {
            "count": 3,
            "pulses": [{"id": "1", "name": "Test Pulse"}]
        }
    }
    mock_response.raise_for_status = MagicMock()

    with patch("backend.services.otx_service.settings") as mock_settings, \
         patch("httpx.AsyncClient") as mock_client:
        mock_settings.otx_api_key = "test-key"
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        metadata, signals = await otx_service.fetch_otx("example.com")
        
        assert "pulse_info" in metadata
        assert len(signals) == 1
        assert signals[0].type == "otx"
        assert "pulse" in signals[0].detail.lower()


@pytest.mark.asyncio
async def test_github_missing_key():
    """Test that GitHub returns service error signal when API key is missing."""
    with patch("backend.services.github_service.settings") as mock_settings:
        mock_settings.github_token = None
        
        leaks, signals = await github_service.search_code_leaks("test-org")
        
        assert leaks == []
        assert len(signals) == 1
        assert signals[0].id.startswith("service_")
        assert signals[0].severity == "low"


@pytest.mark.asyncio
async def test_github_mock_response():
    """Test GitHub with mocked successful response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"X-RateLimit-Remaining": "10"}
    mock_response.json.return_value = {
        "items": [
            {
                "name": ".env",
                "path": ".env",
                "repository": {"full_name": "test-org/repo"},
                "html_url": "https://github.com/test-org/repo/blob/main/.env",
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("backend.services.github_service.settings") as mock_settings, \
         patch("httpx.AsyncClient") as mock_client:
        mock_settings.github_token = "test-token"
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        leaks, signals = await github_service.search_code_leaks("test-org")
        
        assert len(leaks) == 1
        assert len(signals) == 1
        assert signals[0].type == "github"
        assert signals[0].severity == "high"
        assert ".env" in signals[0].detail


@pytest.mark.asyncio
async def test_github_empty_org():
    """Test that GitHub returns empty when org is not provided."""
    leaks, signals = await github_service.search_code_leaks("")
    
    assert leaks == []
    assert signals == []
