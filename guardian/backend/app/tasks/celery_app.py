from celery import Celery
import os
import asyncio
from pathlib import Path
from datetime import datetime
import shutil

from app.core.config import settings

celery_app = Celery(
    "guardian_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Import tasks so Celery discovers them
import app.tasks.scan_repository
import app.tasks.github_pr
