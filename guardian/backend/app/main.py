from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.db.postgres import engine, Base
from app.routers import audits, integrations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GUARDIAN API",
    description="AI-Powered Code Security & Dependency Auditor",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # In production, use Alembic migrations instead
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized.")

app.include_router(audits.router, prefix="/api")
app.include_router(integrations.router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "GUARDIAN Backend"}

# Import slack handlers down here to avoid circular imports if they rely on app
from app.slack_handlers import commands, events
