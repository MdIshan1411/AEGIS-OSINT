"""
Abstract base connector interface.
All platform-specific connectors inherit from this.
"""

from abc import ABC, abstractmethod
from typing import Optional
from trace_x.schemas.models import PlatformProfile
from trace_x.schemas.enums import Platform


class BaseConnector(ABC):
    """Abstract connector interface for platform data sources."""

    platform: Platform

    def __init__(self):
        """Initialize connector."""
        pass

    @abstractmethod
    async def search(
        self, query: dict, limit: int = 5
    ) -> list[PlatformProfile]:
        """
        Search for profiles matching query.
        
        Args:
            query: {name, email, bio, context} (flexible)
            limit: max profiles to return
            
        Returns:
            List of PlatformProfile objects (sorted by relevance)
        """
        pass

    @abstractmethod
    async def get_profile_details(
        self, username: str
    ) -> Optional[PlatformProfile]:
        """
        Get full details for a specific user.
        
        Args:
            username: Platform-specific username
            
        Returns:
            PlatformProfile or None if not found
        """
        pass
