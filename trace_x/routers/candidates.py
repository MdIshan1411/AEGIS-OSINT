"""
API routes for candidate details.
"""

import logging
from fastapi import APIRouter, HTTPException
from trace_x.db.repositories import InvestigationRepository
from trace_x.db.mongo import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/candidates", tags=["candidates"])


@router.get("/{candidate_id}")
async def get_candidate(candidate_id: str) -> dict:
    """
    Get full candidate details.
    
    This endpoint searches all investigations for the candidate.
    In production, would be indexed separately.
    """
    db = get_db()
    repo = InvestigationRepository(db)

    # Find investigation containing this candidate
    # (In production: query candidates collection directly)
    investigations = await repo.list()

    for investigation in investigations:
        for candidate in investigation.top_candidates:
            if candidate.candidate_id == candidate_id:
                return {
                    "investigation_id": investigation.investigation_id,
                    "candidate": candidate.model_dump(),
                    "profiles": [p.model_dump() for p in investigation.profiles],
                    "timeline": [t.model_dump() for t in investigation.timeline],
                    "relationship_graph": investigation.relationship_graph,
                }

    raise HTTPException(status_code=404, detail="Candidate not found")
