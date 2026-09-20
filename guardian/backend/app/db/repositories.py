from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from typing import List, Optional, Any
from app.db.models import User, AuditRecord, Vulnerability, DependencyVulnerability, GitHubIntegration, SlackIntegration, AuditLog

class BaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

class UserRepository(BaseRepository):
    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get(self, user_id: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.user_id == user_id))
        return result.scalars().first()

    async def get_or_create(self, user: User) -> User:
        if user.slack_user_id:
            result = await self.session.execute(select(User).where(User.slack_user_id == user.slack_user_id))
            existing = result.scalars().first()
            if existing:
                return existing
        return await self.create(user)

class AuditRecordRepository(BaseRepository):
    async def create(self, audit: AuditRecord) -> AuditRecord:
        self.session.add(audit)
        await self.session.commit()
        await self.session.refresh(audit)
        return audit

    async def get(self, audit_id: str) -> Optional[AuditRecord]:
        result = await self.session.execute(select(AuditRecord).where(AuditRecord.audit_id == audit_id))
        return result.scalars().first()

    async def update(self, audit: AuditRecord) -> AuditRecord:
        await self.session.commit()
        await self.session.refresh(audit)
        return audit

    async def list_by_user(self, user_id: str) -> List[AuditRecord]:
        result = await self.session.execute(select(AuditRecord).where(AuditRecord.user_id == user_id).order_by(AuditRecord.created_at.desc()))
        return list(result.scalars().all())

    async def delete(self, audit_id: str):
        await self.session.execute(delete(AuditRecord).where(AuditRecord.audit_id == audit_id))
        await self.session.commit()

class VulnerabilityRepository(BaseRepository):
    async def create(self, vuln: Vulnerability) -> Vulnerability:
        self.session.add(vuln)
        await self.session.commit()
        await self.session.refresh(vuln)
        return vuln

    async def get_by_audit(self, audit_id: str) -> List[Vulnerability]:
        result = await self.session.execute(select(Vulnerability).where(Vulnerability.audit_id == audit_id))
        return list(result.scalars().all())

class DependencyVulnerabilityRepository(BaseRepository):
    async def create(self, vuln: DependencyVulnerability) -> DependencyVulnerability:
        self.session.add(vuln)
        await self.session.commit()
        await self.session.refresh(vuln)
        return vuln

    async def get_by_audit(self, audit_id: str) -> List[DependencyVulnerability]:
        result = await self.session.execute(select(DependencyVulnerability).where(DependencyVulnerability.audit_id == audit_id))
        return list(result.scalars().all())

class GitHubIntegrationRepository(BaseRepository):
    async def get_by_user(self, user_id: str) -> Optional[GitHubIntegration]:
        result = await self.session.execute(select(GitHubIntegration).where(GitHubIntegration.user_id == user_id))
        return result.scalars().first()

class SlackIntegrationRepository(BaseRepository):
    async def get_by_user(self, user_id: str) -> Optional[SlackIntegration]:
        result = await self.session.execute(select(SlackIntegration).where(SlackIntegration.user_id == user_id))
        return result.scalars().first()

class AuditLogRepository(BaseRepository):
    async def log_action(self, log: AuditLog) -> AuditLog:
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log
