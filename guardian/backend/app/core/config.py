from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    POSTGRES_URL: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5432/guardian")
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    GITHUB_CLIENT_ID: str = Field(default="")
    GITHUB_CLIENT_SECRET: str = Field(default="")
    GITHUB_ACCESS_TOKEN: str = Field(default="")
    SLACK_BOT_TOKEN: str = Field(default="")
    SLACK_SIGNING_SECRET: str = Field(default="")
    CLAUDE_API_KEY: str = Field(default="")
    LOG_LEVEL: str = Field(default="INFO")
    DEBUG_MODE: bool = Field(default=False)

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
