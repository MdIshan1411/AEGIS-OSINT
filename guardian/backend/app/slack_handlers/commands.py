import uuid
from fastapi import Request
from app.main import app, logger
from app.db.postgres import AsyncSessionLocal
from app.db.models import User, AuditRecord
from app.db.repositories import UserRepository, AuditRecordRepository
from app.tasks.celery_app import scan_repository

@app.post("/api/slack/commands")
async def handle_guardian_command(request: Request):
    """
    Handle /guardian audit <repo-url> command.
    Using FastAPI endpoint for simple Slack interactions.
    """
    form = await request.form()
    command_text = form.get("text", "").strip()
    channel_id = form.get("channel_id")
    user_id = form.get("user_id")
    user_name = form.get("user_name")
    
    if not command_text.startswith("http"):
        return {
            "response_type": "ephemeral",
            "text": "❌ Usage: `/guardian audit https://github.com/owner/repo`"
        }
        
    repo_url = command_text
    
    async with AsyncSessionLocal() as db:
        user_repo = UserRepository(db)
        audit_repo = AuditRecordRepository(db)
        
        user = User(
            slack_user_id=user_id,
            slack_username=user_name
        )
        user_record = await user_repo.get_or_create(user)
        
        audit = AuditRecord(
            audit_id=str(uuid.uuid4()),
            user_id=user_record.user_id,
            repo_url=repo_url,
            repo_owner=repo_url.split("/")[-2] if "/" in repo_url else "unknown",
            repo_name=repo_url.split("/")[-1] if "/" in repo_url else "unknown",
            status="PENDING",
            slack_channel_id=channel_id,
            slack_user_id=user_id,
        )
        await audit_repo.create(audit)
        
        # Queue Celery task
        scan_repository.delay(audit.audit_id, channel_id)
        
    logger.info(f"Queued scan for {repo_url} (audit_id: {audit.audit_id})")
    
    return {
        "response_type": "in_channel",
        "text": f"🔍 *Scanning {audit.repo_name}...*\nAudit ID: `{audit.audit_id}`"
    }
