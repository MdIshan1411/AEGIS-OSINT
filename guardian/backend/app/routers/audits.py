from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.postgres import get_db
from app.db.models import User
from app.db.repositories import AuditRecordRepository, VulnerabilityRepository, DependencyVulnerabilityRepository
from app.schemas.models import AuditRecordSchema, AuditStartRequest
# Dummy get_current_user for now
async def get_current_user():
    return User(user_id="dummy-user-id")

router = APIRouter(prefix="/audits", tags=["audits"])

@router.get("", response_model=List[AuditRecordSchema])
async def list_audits(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = AuditRecordRepository(db)
    audits = await repo.list_by_user(user.user_id)
    return audits

@router.get("/{audit_id}")
async def get_audit(
    audit_id: str, 
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    audit_repo = AuditRecordRepository(db)
    vuln_repo = VulnerabilityRepository(db)
    dep_vuln_repo = DependencyVulnerabilityRepository(db)
    
    audit = await audit_repo.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    if audit.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    vulns = await vuln_repo.get_by_audit(audit_id)
    dep_vulns = await dep_vuln_repo.get_by_audit(audit_id)
    
    return {
        "audit": audit,
        "vulnerabilities": vulns,
        "dependency_vulnerabilities": dep_vulns,
    }

@router.post("")
async def create_audit(
    request: AuditStartRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # This will be similar to slash command
    return {"status": "queued"}

@router.delete("/{audit_id}")
async def delete_audit(
    audit_id: str, 
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = AuditRecordRepository(db)
    audit = await repo.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404)
    if audit.user_id != user.user_id:
        raise HTTPException(status_code=403)
    await repo.delete(audit_id)
    return {"status": "deleted"}
