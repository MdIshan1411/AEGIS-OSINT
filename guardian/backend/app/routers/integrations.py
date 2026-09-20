from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.postgres import get_db
from app.db.models import User
from app.db.repositories import GitHubIntegrationRepository, SlackIntegrationRepository

router = APIRouter(prefix="/integrations", tags=["integrations"])

# Dummy get_current_user for now
async def get_current_user():
    return User(user_id="dummy-user-id")

@router.get("")
async def list_integrations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    gh_repo = GitHubIntegrationRepository(db)
    sl_repo = SlackIntegrationRepository(db)
    
    gh = await gh_repo.get_by_user(user.user_id)
    sl = await sl_repo.get_by_user(user.user_id)
    
    return {
        "github": gh is not None,
        "slack": sl is not None
    }

@router.get("/auth/github/callback")
async def github_callback(code: str):
    return {"status": "success", "token": "placeholder"}

@router.get("/auth/slack/callback")
async def slack_callback(code: str):
    return {"status": "success", "token": "placeholder"}
