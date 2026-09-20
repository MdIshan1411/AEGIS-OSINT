"""
API routes for investigations.
All business logic in InvestigationService.
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from trace_x.services.investigation_service import InvestigationService
from trace_x.db.repositories import InvestigationRepository
from trace_x.db.mongo import get_db
from trace_x.schemas.models import Investigation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/investigate", tags=["investigate"])


# Request/Response models
class InvestigateRequest(BaseModel):
    """POST /api/investigate request."""
    name: str
    email: str | None = None
    context: str | None = None


class InvestigateResponse(BaseModel):
    """Response to investigation creation."""
    investigation_id: str
    status: str
    message: str


class ResolveConflictRequest(BaseModel):
    """PATCH /api/investigate/{id}/conflicts/{conflict_id} request."""
    resolution: str  # "EXPLAINED" or "REJECTED"
    resolution_note: str


# Dependency: InvestigationService
async def get_investigation_service() -> InvestigationService:
    """Get investigation service with repo."""
    db = get_db()
    repo = InvestigationRepository(db)
    return InvestigationService(repo)


# Endpoints


@router.post("/")
async def create_investigation(
    request: InvestigateRequest,
    background_tasks: BackgroundTasks,
    service: InvestigationService = Depends(get_investigation_service),
) -> InvestigateResponse:
    """
    Start a new investigation (async).
    
    Request:
    {
      "name": "John Doe",
      "email": "john@example.com",
      "context": "Optional background info"
    }
    
    Response:
    {
      "investigation_id": "uuid",
      "status": "PENDING",
      "message": "Investigation started. Poll /api/investigate/{id} for results."
    }
    """
    investigation_id = await service.start_investigation(
        name=request.name,
        email=request.email,
        context=request.context,
    )

    # Start background processing
    background_tasks.add_task(service.process_investigation, investigation_id)

    return InvestigateResponse(
        investigation_id=investigation_id,
        status="PENDING",
        message=f"Investigation started. Poll /api/investigate/{investigation_id} for results.",
    )


@router.get("/{investigation_id}")
async def get_investigation(
    investigation_id: str,
    service: InvestigationService = Depends(get_investigation_service),
) -> Investigation:
    """
    Get investigation status and results.
    
    Returns full Investigation object when complete.
    """
    repo = InvestigationRepository(get_db())
    investigation = await repo.get(investigation_id)

    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")

    return investigation


@router.patch("/{investigation_id}/conflicts/{conflict_id}")
async def resolve_conflict(
    investigation_id: str,
    conflict_id: str,
    request: ResolveConflictRequest,
    service: InvestigationService = Depends(get_investigation_service),
) -> dict:
    """
    Resolve a conflict (mark as EXPLAINED or REJECTED).
    
    Request:
    {
      "resolution": "REJECTED",
      "resolution_note": "Travel was for conference"
    }
    """
    await service.resolve_conflict(
        investigation_id=investigation_id,
        conflict_id=conflict_id,
        resolution=request.resolution,
        note=request.resolution_note,
    )

    return {
        "status": "ok",
        "investigation_id": investigation_id,
        "conflict_id": conflict_id,
        "resolution": request.resolution,
    }
