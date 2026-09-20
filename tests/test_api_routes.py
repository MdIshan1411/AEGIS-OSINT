"""
Tests for API routes (full investigation workflow).
"""

import pytest
from fastapi.testclient import TestClient
from trace_x.main import app
import asyncio


@pytest.fixture
def client():
    """FastAPI test client."""
    with TestClient(app) as c:
        yield c


def test_health(client):
    """Test /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_create_investigation(client):
    """Test POST /api/investigate."""
    response = client.post(
        "/api/investigate/",
        json={"name": "Alice Johnson", "email": None},
    )

    assert response.status_code == 200
    data = response.json()
    assert "investigation_id" in data
    assert data["status"] == "PENDING"

    investigation_id = data["investigation_id"]

    # Wait a bit for processing
    await asyncio.sleep(2)

    # Poll for completion
    max_polls = 10
    result = None
    for _ in range(max_polls):
        result = client.get(f"/api/investigate/{investigation_id}")
        if result.json()["status"] == "COMPLETE":
            break
        await asyncio.sleep(0.5)

    assert result is not None
    investigation = result.json()
    assert investigation["status"] == "COMPLETE"
    assert len(investigation["top_candidates"]) > 0
    assert investigation["top_candidates"][0]["confidence_overall"] > 60


@pytest.mark.asyncio
async def test_investigation_bob_chen_conflict(client):
    """Test investigation with location conflict."""
    response = client.post(
        "/api/investigate/",
        json={"name": "Bob Chen"},
    )

    investigation_id = response.json()["investigation_id"]

    # Wait for processing
    await asyncio.sleep(2)

    # Poll for completion
    max_polls = 10
    result = None
    for _ in range(max_polls):
        result = client.get(f"/api/investigate/{investigation_id}")
        if result.json()["status"] == "COMPLETE":
            break
        await asyncio.sleep(0.5)

    assert result is not None
    investigation = result.json()
    assert len(investigation["conflicts"]) > 0
    
    conflict_types = [c["conflict_type"] for c in investigation["conflicts"]]
    assert "LOCATION_OVERLAP" in conflict_types
