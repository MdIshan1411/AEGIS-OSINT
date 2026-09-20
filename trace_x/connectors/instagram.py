"""Instagram connector (synthetic demo data)."""

from typing import Optional
from trace_x.connectors.base import BaseConnector
from trace_x.schemas.models import PlatformProfile
from trace_x.schemas.enums import Platform
from trace_x.core.config import get_config

config = get_config()


class InstagramConnector(BaseConnector):
    """Instagram profile connector (DEMO_MODE: synthetic data only)."""

    platform = Platform.INSTAGRAM

    def __init__(self):
        super().__init__()
        if not config.demo_mode:
            raise RuntimeError("Instagram connector only supports DEMO_MODE=true")

    async def search(
        self, query: dict, limit: int = 5
    ) -> list[PlatformProfile]:
        """
        Search Instagram by name (returns synthetic data).
        Note: Instagram profiles are less commonly used for professional identity matching.
        """
        # For this phase, return empty list (Instagram not in primary demo scenarios)
        # In Phase 4, can add optional Instagram profiles
        return []

    async def get_profile_details(
        self, username: str
    ) -> Optional[PlatformProfile]:
        """Get full Instagram profile (synthetic)."""
        return None
