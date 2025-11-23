"""Smoke test for scan endpoint."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from httpx import AsyncClient
from backend.main import app


@pytest.mark.asyncio
async def test_scan_example_com():
    """Smoke test: scan example.com and verify response structure."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/scan/vendor",
            json={"domain": "example.com"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "result" in data
        result = data["result"]
        
        # Verify required fields
        assert "id" in result
        assert "domain" in result
        assert result["domain"] == "example.com"
        assert "risk_score" in result
        assert "categories" in result
        assert "signals" in result
        assert "summary" in result
        assert "breach_likelihood_30d" in result
        assert "breach_likelihood_90d" in result
        assert "created_at" in result
        
        # Verify value ranges
        assert 0 <= result["risk_score"] <= 100
        assert 0.0 <= result["breach_likelihood_30d"] <= 1.0
        assert 0.0 <= result["breach_likelihood_90d"] <= 1.0
        
        # Verify at least one signal
        assert len(result["signals"]) >= 1
        
        # Verify categories
        assert "network" in result["categories"]
        assert "software" in result["categories"]
        assert "data_exposure" in result["categories"]
        assert "ai_integration" in result["categories"]


@pytest.mark.asyncio
async def test_scan_invalid_domain():
    """Test that invalid domains are rejected."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test IP address
        response = await client.post(
            "/api/v1/scan/vendor",
            json={"domain": "192.168.1.1"},
        )
        assert response.status_code == 422  # Validation error
        
        # Test URL
        response = await client.post(
            "/api/v1/scan/vendor",
            json={"domain": "https://example.com"},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_ping_endpoint():
    """Test ping endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/ping")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

