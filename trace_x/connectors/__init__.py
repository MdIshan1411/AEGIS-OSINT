"""
Connector registry and factory.
"""

from trace_x.connectors.base import BaseConnector
from trace_x.connectors.github import GitHubConnector
from trace_x.connectors.linkedin import LinkedInConnector
from trace_x.connectors.x import XConnector
from trace_x.connectors.instagram import InstagramConnector

CONNECTORS = {
    "github": GitHubConnector,
    "linkedin": LinkedInConnector,
    "x": XConnector,
    "instagram": InstagramConnector,
}

async def get_connector(platform: str) -> BaseConnector:
    """Factory function to get connector instance."""
    connector_class = CONNECTORS.get(platform.lower())
    if not connector_class:
        raise ValueError(f"Unknown platform: {platform}")
    return connector_class()
