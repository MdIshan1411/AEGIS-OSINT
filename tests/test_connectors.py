"""
Tests for connectors (synthetic data validation).
"""

import pytest
from trace_x.connectors.github import GitHubConnector
from trace_x.connectors.linkedin import LinkedInConnector
from trace_x.connectors.x import XConnector
from trace_x.schemas.enums import Platform


@pytest.mark.asyncio
async def test_github_connector_alice_johnson():
    """Test GitHub connector returns consistent data for Alice Johnson."""
    connector = GitHubConnector()
    query = {"name": "Alice Johnson", "email": None}
    profiles = await connector.search(query, limit=1)

    assert len(profiles) >= 1
    assert profiles[0].platform == Platform.GITHUB
    assert profiles[0].display_name == "Alice Johnson"
    assert "alice" in profiles[0].username.lower()


@pytest.mark.asyncio
async def test_linkedin_connector_bob_chen():
    """Test LinkedIn connector returns consistent data for Bob Chen."""
    connector = LinkedInConnector()
    query = {"name": "Bob Chen", "email": None}
    profiles = await connector.search(query, limit=1)

    assert len(profiles) >= 1
    assert profiles[0].platform == Platform.LINKEDIN
    assert profiles[0].display_name == "Bob Chen"


@pytest.mark.asyncio
async def test_x_connector_john_smith():
    """Test X connector returns consistent data for John Smith."""
    connector = XConnector()
    query = {"name": "John Smith", "email": None}
    profiles = await connector.search(query, limit=1)

    assert len(profiles) >= 1
    assert profiles[0].platform == Platform.X


@pytest.mark.asyncio
async def test_connector_determinism():
    """Test: Same query returns same result (deterministic)."""
    connector = GitHubConnector()
    query = {"name": "Alice Johnson"}

    result1 = await connector.search(query, limit=1)
    result2 = await connector.search(query, limit=1)

    assert result1[0].profile_id == result2[0].profile_id
    assert result1[0].bio == result2[0].bio
