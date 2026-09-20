"""
TRACE-X MongoDB Client & Lifecycle.

Motor async MongoDB client with FastAPI lifespan integration,
automatic index creation (including TTL), and ObjectId helpers.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from trace_x.core.config import get_config

logger = logging.getLogger("trace_x.db")

# ── Module-level client (set during lifespan) ───────────────

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


# ── ObjectId ↔ str helper ───────────────────────────────────


class ObjectIdStr(str):
    """
    Custom type for Pydantic v2 that accepts MongoDB ObjectId as string.

    Validates that the string is a 24-character hex string (ObjectId format).
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """Register custom validation for Pydantic v2."""
        return core_schema.no_info_plain_validator_function(cls._validate)

    @classmethod
    def _validate(cls, v: Any) -> str:
        """Validate and convert ObjectId to string."""
        if hasattr(v, "__str__"):
            s = str(v)
            return s
        return str(v)


# ── Index Definitions ───────────────────────────────────────


async def _create_indexes(db: AsyncIOMotorDatabase) -> None:
    """
    Create all required indexes on startup.

    Indexes:
    - investigations: unique on investigation_id
    - candidates: compound on (investigation_id, rank)
    - timeline_events: index on candidate_id
    - investigations: TTL on retention_expiry (auto-delete expired docs)
    """
    config = get_config()

    # Investigation indexes
    investigations = db["investigations"]
    await investigations.create_index("investigation_id", unique=True)
    await investigations.create_index(
        "retention_expiry",
        expireAfterSeconds=0,  # Documents deleted when retention_expiry passes
    )
    await investigations.create_index("status")
    await investigations.create_index("email_hash")

    # Candidate indexes
    candidates = db["candidates"]
    await candidates.create_index(
        [("investigation_id", 1), ("rank", 1)],
        unique=True,
    )
    await candidates.create_index("candidate_id", unique=True)

    # Timeline event indexes
    timeline_events = db["timeline_events"]
    await timeline_events.create_index("candidate_id")
    await timeline_events.create_index("investigation_id")
    await timeline_events.create_index("event_id", unique=True)

    # Conflict indexes
    conflicts = db["conflicts"]
    await conflicts.create_index("investigation_id")
    await conflicts.create_index("conflict_id", unique=True)

    logger.info(
        "MongoDB indexes created (TTL=%d days)", config.retention_days
    )


# ── Lifecycle ───────────────────────────────────────────────


async def init_mongo() -> AsyncIOMotorDatabase:
    """
    Initialize the Motor client and return the database handle.

    Creates indexes on first call. Idempotent.
    """
    global _client, _db
    config = get_config()

    if _client is None:
        _client = AsyncIOMotorClient(config.mongo_uri)
        _db = _client[config.db_name]
        await _create_indexes(_db)
        logger.info(
            "MongoDB connected: %s / %s", config.mongo_uri, config.db_name
        )
    return _db


async def close_mongo() -> None:
    """Close the Motor client gracefully."""
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed.")


def get_db() -> AsyncIOMotorDatabase:
    """
    Return the current database handle.

    Raises RuntimeError if called before init_mongo().
    """
    if _db is None:
        raise RuntimeError(
            "Database not initialized. Call init_mongo() first."
        )
    return _db


async def check_connection() -> bool:
    """
    Ping MongoDB to verify connectivity.

    Returns True if connected, False otherwise.
    """
    if _client is None:
        return False
    try:
        await _client.admin.command("ping")
        return True
    except Exception:
        logger.warning("MongoDB ping failed.", exc_info=True)
        return False


@asynccontextmanager
async def mongo_lifespan() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    Async context manager for FastAPI lifespan integration.

    Usage in main.py:
        async with mongo_lifespan() as db:
            yield
    """
    db = await init_mongo()
    try:
        yield db
    finally:
        await close_mongo()
