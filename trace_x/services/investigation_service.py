"""
Investigation service: orchestrates connectors, ML engine, and database updates.
No business logic in routers; all logic lives here.
"""

import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from trace_x.db.repositories import InvestigationRepository
from trace_x.connectors import CONNECTORS
from trace_x.ml.engine import resolve_candidates
from trace_x.ml.graph import build_knowledge_graph
from trace_x.schemas.models import Investigation, InvestigationStatus, AuditEntry
from trace_x.core.config import get_config

config = get_config()

logger = logging.getLogger(__name__)


class InvestigationService:
    """Service for managing investigations (connector + ML orchestration)."""

    def __init__(self, investigation_repo: InvestigationRepository):
        self.investigation_repo = investigation_repo

    async def start_investigation(
        self, name: str, email: Optional[str] = None, context: Optional[str] = None
    ) -> str:
        """
        Start a new investigation (async, returns immediately with ID).
        Background task will process connectors + ML.
        
        Args:
            name: Subject name
            email: Optional email hint
            context: Optional additional context
            
        Returns:
            investigation_id (UUID string)
        """
        investigation_id = str(uuid.uuid4())

        investigation = Investigation(
            investigation_id=investigation_id,
            query={"name": name, "email": email, "context": context},
            status=InvestigationStatus.PENDING,
            top_candidates=[],
            profiles=[],
            timeline=[],
            conflicts=[],
            relationship_graph={"nodes": [], "edges": []},
            metadata={
                "processing_time_ms": 0,
                "version": "2.0",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            consent_purpose="OSINT identity resolution demo",
            retention_expiry=datetime.now(timezone.utc) + timedelta(days=config.retention_days),
            audit_log=[
                AuditEntry(
                    action="INVESTIGATION_CREATED",
                    actor="system",
                    delta={"status": "PENDING"},
                )
            ],
        )

        await self.investigation_repo.create(investigation)
        logger.info(f"Started investigation: {investigation_id}")

        return investigation_id

    async def process_investigation(self, investigation_id: str) -> None:
        """
        Process investigation: call connectors, run ML, update database.
        Typically called by background task.
        
        Args:
            investigation_id: UUID of investigation to process
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Fetch investigation
            investigation = await self.investigation_repo.get(investigation_id)
            if not investigation:
                logger.error(f"Investigation not found: {investigation_id}")
                return

            # Update status
            investigation.status = InvestigationStatus.PROCESSING
            await self.investigation_repo.update(investigation.investigation_id, investigation.model_dump())

            # Call all connectors sequentially for simplicity (or parallel in prod)
            subject_name = investigation.query.name
            query = investigation.query.model_dump()

            connector_results = {}
            for platform_name, connector_class in CONNECTORS.items():
                try:
                    connector = connector_class()
                    profiles = await connector.search(query, limit=3)
                    connector_results[platform_name] = profiles
                    logger.info(f"Got {len(profiles)} profiles from {platform_name}")
                except Exception as e:
                    logger.error(f"Connector error ({platform_name}): {e}")
                    connector_results[platform_name] = []

            # Flatten profiles across all platforms
            all_profiles = []
            grouped_profiles = []
            for platform, profiles in connector_results.items():
                all_profiles.extend(profiles)
                if profiles:
                    grouped_profiles.append([p.model_dump(mode="json") for p in profiles])

            investigation.profiles = all_profiles

            # Run ML engine
            candidates, conflicts, graph_json = resolve_candidates(
                subject=query,
                platform_profiles=grouped_profiles,
                config=config.weights.model_dump() if hasattr(config, 'weights') else config.ml_weights,
            )

            investigation.top_candidates = candidates[:5]  # Top 5
            investigation.conflicts = conflicts
            investigation.top_candidate_id = (
                candidates[0].candidate_id if candidates else None
            )

            investigation.relationship_graph = graph_json

            # Update metadata
            processing_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            investigation.metadata.processing_time_ms = int(processing_ms)
            investigation.metadata.updated_at = datetime.now(timezone.utc).isoformat()

            # Audit log
            investigation.audit_log.append(
                AuditEntry(
                    action="INVESTIGATION_PROCESSED",
                    actor="system",
                    delta={
                        "status": "COMPLETE",
                        "candidates_count": len(candidates),
                        "conflicts_count": len(conflicts),
                    },
                )
            )

            # Save
            investigation.status = InvestigationStatus.COMPLETE
            await self.investigation_repo.update(investigation.investigation_id, investigation.model_dump())

            logger.info(
                f"Completed investigation: {investigation_id} "
                f"({int(processing_ms)}ms, {len(candidates)} candidates)"
            )

        except Exception as e:
            logger.error(f"Investigation processing failed: {e}", exc_info=True)
            investigation = await self.investigation_repo.get(investigation_id)
            if investigation:
                investigation.status = InvestigationStatus.FAILED
                investigation.audit_log.append(
                    AuditEntry(
                        action="INVESTIGATION_FAILED",
                        actor="system",
                        delta={"error": str(e)},
                    )
                )
                await self.investigation_repo.update(investigation.investigation_id, investigation.model_dump())

    async def resolve_conflict(
        self, investigation_id: str, conflict_id: str, resolution: str, note: str
    ) -> None:
        """
        Resolve a conflict (mark as EXPLAINED or REJECTED).
        Recalculate candidate confidence if conflict is rejected.
        
        Args:
            investigation_id: UUID of investigation
            conflict_id: UUID of conflict
            resolution: "EXPLAINED" or "REJECTED"
            note: Human-readable reason
        """
        investigation = await self.investigation_repo.get(investigation_id)
        if not investigation:
            return

        # Find conflict
        conflict = next(
            (c for c in investigation.conflicts if c.conflict_id == conflict_id),
            None,
        )
        if not conflict:
            return

        # Update conflict
        conflict.resolution = resolution
        conflict.resolution_note = note

        # If rejected, recalculate candidate confidence (remove penalty)
        if resolution == "REJECTED":
            severity_penalty = {
                "HIGH": 10,
                "MEDIUM": 5,
                "LOW": 2,
            }
            penalty = severity_penalty.get(conflict.severity.value, 0)

            for candidate in investigation.top_candidates:
                candidate.confidence_overall = min(99.9, candidate.confidence_overall + penalty)

        # Audit log
        investigation.audit_log.append(
            AuditEntry(
                action="CONFLICT_RESOLVED",
                actor="system",
                delta={
                    "conflict_id": conflict_id,
                    "resolution": resolution,
                },
            )
        )

        await self.investigation_repo.update(investigation.investigation_id, investigation.model_dump())
        logger.info(f"Resolved conflict: {conflict_id} → {resolution}")
