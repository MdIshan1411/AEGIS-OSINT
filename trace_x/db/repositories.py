"""
TRACE-X Repository Layer.

Async CRUD operations using the Repository pattern. Each collection
gets its own repository class. No business logic — just data access.
All methods are async and return Pydantic models or raw dicts.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from trace_x.db.mongo import get_db
from trace_x.schemas.models import (
    AuditEntry,
    Candidate,
    Conflict,
    Investigation,
    TimelineEvent,
)

logger = logging.getLogger("trace_x.db.repositories")


def _utcnow() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(tz=timezone.utc)


# ── Investigation Repository ───────────────────────────────


class InvestigationRepository:
    """Async CRUD for the investigations collection."""

    COLLECTION = "investigations"

    def __init__(self, db: AsyncIOMotorDatabase | None = None) -> None:
        """Initialize with an optional database handle."""
        self._db = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Return the database handle (lazy)."""
        if self._db is None:
            self._db = get_db()
        return self._db

    @property
    def collection(self):
        """Return the investigations collection."""
        return self.db[self.COLLECTION]

    async def create(self, investigation: Investigation) -> str:
        """
        Insert a new investigation document.

        Returns the investigation_id.
        """
        doc = investigation.model_dump(mode="json")
        await self.collection.insert_one(doc)
        logger.info("Created investigation %s", investigation.investigation_id)
        return investigation.investigation_id

    async def get(self, investigation_id: str) -> Investigation | None:
        """Retrieve an investigation by ID. Returns None if not found."""
        doc = await self.collection.find_one(
            {"investigation_id": investigation_id}
        )
        if doc is None:
            return None
        doc.pop("_id", None)
        return Investigation.model_validate(doc)

    async def update(
        self, investigation_id: str, updates: dict[str, Any]
    ) -> bool:
        """
        Update specific fields of an investigation.

        Returns True if a document was modified.
        """
        if "metadata" not in updates:
            updates["metadata.updated_at"] = _utcnow().isoformat()
        result = await self.collection.update_one(
            {"investigation_id": investigation_id},
            {"$set": updates},
        )
        if result.modified_count > 0:
            logger.info("Updated investigation %s", investigation_id)
            return True
        return False

    async def list_all(
        self, skip: int = 0, limit: int = 50
    ) -> list[Investigation]:
        """List investigations with pagination."""
        cursor = (
            self.collection.find({}, {"_id": 0})
            .sort("metadata.created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        results = []
        async for doc in cursor:
            results.append(Investigation.model_validate(doc))
        return results

    async def delete(self, investigation_id: str) -> bool:
        """Delete an investigation by ID. Returns True if deleted."""
        result = await self.collection.delete_one(
            {"investigation_id": investigation_id}
        )
        if result.deleted_count > 0:
            logger.info("Deleted investigation %s", investigation_id)
            return True
        return False

    async def append_audit(
        self, investigation_id: str, entry: AuditEntry
    ) -> bool:
        """Append an audit log entry (append-only, never overwrite)."""
        result = await self.collection.update_one(
            {"investigation_id": investigation_id},
            {"$push": {"audit_log": entry.model_dump(mode="json")}},
        )
        return result.modified_count > 0


# ── Candidate Repository ───────────────────────────────────


class CandidateRepository:
    """Async CRUD for the candidates collection."""

    COLLECTION = "candidates"

    def __init__(self, db: AsyncIOMotorDatabase | None = None) -> None:
        """Initialize with an optional database handle."""
        self._db = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Return the database handle (lazy)."""
        if self._db is None:
            self._db = get_db()
        return self._db

    @property
    def collection(self):
        """Return the candidates collection."""
        return self.db[self.COLLECTION]

    async def create_bulk(self, candidates: list[Candidate]) -> int:
        """
        Insert multiple candidates at once.

        Returns the count of inserted documents.
        """
        if not candidates:
            return 0
        docs = [c.model_dump(mode="json") for c in candidates]
        result = await self.collection.insert_many(docs)
        logger.info("Inserted %d candidates", len(result.inserted_ids))
        return len(result.inserted_ids)

    async def get_by_investigation(
        self, investigation_id: str
    ) -> list[Candidate]:
        """Retrieve all candidates for an investigation, sorted by rank."""
        cursor = (
            self.collection.find(
                {"investigation_id": investigation_id}, {"_id": 0}
            )
            .sort("rank", 1)
        )
        results = []
        async for doc in cursor:
            results.append(Candidate.model_validate(doc))
        return results

    async def get_by_rank(
        self, investigation_id: str, rank: int
    ) -> Candidate | None:
        """Retrieve a specific candidate by investigation ID and rank."""
        doc = await self.collection.find_one(
            {"investigation_id": investigation_id, "rank": rank},
            {"_id": 0},
        )
        if doc is None:
            return None
        return Candidate.model_validate(doc)


# ── Timeline Event Repository ──────────────────────────────


class TimelineEventRepository:
    """Async CRUD for the timeline_events collection."""

    COLLECTION = "timeline_events"

    def __init__(self, db: AsyncIOMotorDatabase | None = None) -> None:
        """Initialize with an optional database handle."""
        self._db = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Return the database handle (lazy)."""
        if self._db is None:
            self._db = get_db()
        return self._db

    @property
    def collection(self):
        """Return the timeline_events collection."""
        return self.db[self.COLLECTION]

    async def create(self, event: TimelineEvent) -> str:
        """Insert a timeline event. Returns the event_id."""
        doc = event.model_dump(mode="json")
        await self.collection.insert_one(doc)
        logger.info("Created timeline event %s", event.event_id)
        return event.event_id

    async def get_by_candidate(
        self, candidate_id: str
    ) -> list[TimelineEvent]:
        """Retrieve all timeline events for a candidate."""
        cursor = self.collection.find(
            {"candidate_id": candidate_id}, {"_id": 0}
        ).sort("start_date", 1)
        results = []
        async for doc in cursor:
            results.append(TimelineEvent.model_validate(doc))
        return results

    async def delete_by_investigation(
        self, investigation_id: str
    ) -> int:
        """Delete all timeline events for an investigation. Returns count."""
        result = await self.collection.delete_many(
            {"investigation_id": investigation_id}
        )
        logger.info(
            "Deleted %d timeline events for investigation %s",
            result.deleted_count,
            investigation_id,
        )
        return result.deleted_count


# ── Conflict Repository ────────────────────────────────────


class ConflictRepository:
    """Async CRUD for the conflicts collection."""

    COLLECTION = "conflicts"

    def __init__(self, db: AsyncIOMotorDatabase | None = None) -> None:
        """Initialize with an optional database handle."""
        self._db = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Return the database handle (lazy)."""
        if self._db is None:
            self._db = get_db()
        return self._db

    @property
    def collection(self):
        """Return the conflicts collection."""
        return self.db[self.COLLECTION]

    async def create(self, conflict: Conflict) -> str:
        """Insert a conflict. Returns the conflict_id."""
        doc = conflict.model_dump(mode="json")
        await self.collection.insert_one(doc)
        logger.info("Created conflict %s", conflict.conflict_id)
        return conflict.conflict_id

    async def get_by_investigation(
        self, investigation_id: str
    ) -> list[Conflict]:
        """Retrieve all conflicts for an investigation."""
        cursor = self.collection.find(
            {"investigation_id": investigation_id}, {"_id": 0}
        )
        results = []
        async for doc in cursor:
            results.append(Conflict.model_validate(doc))
        return results
