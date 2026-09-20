import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .postgres import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    github_username = Column(String, nullable=True)
    github_access_token = Column(String, nullable=True)
    slack_user_id = Column(String, nullable=True)
    slack_username = Column(String, nullable=True)
    email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    audits = relationship("AuditRecord", back_populates="user")
    github_integrations = relationship("GitHubIntegration", back_populates="user")
    slack_integrations = relationship("SlackIntegration", back_populates="user")

class AuditRecord(Base):
    __tablename__ = "audit_records"

    audit_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=True)
    repo_url = Column(String, index=True)
    repo_owner = Column(String)
    repo_name = Column(String)
    repo_clone_path = Column(String, nullable=True)
    status = Column(String, default="QUEUED")  # QUEUED, SCANNING, ANALYZING, COMPLETE, FAILED
    slack_channel_id = Column(String, nullable=True)
    slack_message_ts = Column(String, nullable=True)
    slack_user_id = Column(String, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    execution_time_ms = Column(Integer, default=0)
    total_files_scanned = Column(Integer, default=0)
    total_loc = Column(Integer, default=0)
    summary_json = Column(JSON, default={"critical": 0, "high": 0, "medium": 0, "low": 0})
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="audits")
    vulnerabilities = relationship("Vulnerability", back_populates="audit", cascade="all, delete-orphan")
    dependency_vulns = relationship("DependencyVulnerability", back_populates="audit", cascade="all, delete-orphan")

class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    vuln_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    audit_id = Column(String, ForeignKey("audit_records.audit_id"))
    file_path = Column(String)
    line_number = Column(Integer)
    vulnerability_type = Column(String)
    severity = Column(String)
    cvss_score = Column(Float)
    description = Column(String)
    exploitation_scenario = Column(String, nullable=True)
    code_snippet = Column(String)
    suggested_fix = Column(String, nullable=True)
    cwe_id = Column(String, nullable=True)
    owasp_category = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    audit = relationship("AuditRecord", back_populates="vulnerabilities")

class DependencyVulnerability(Base):
    __tablename__ = "dependency_vulnerabilities"

    dep_vuln_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    audit_id = Column(String, ForeignKey("audit_records.audit_id"))
    package_name = Column(String)
    current_version = Column(String)
    vulnerable_in = Column(String, nullable=True)
    cve_id = Column(String)
    severity = Column(String)
    description = Column(String)
    recommendation = Column(String)
    published_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    audit = relationship("AuditRecord", back_populates="dependency_vulns")

class GitHubIntegration(Base):
    __tablename__ = "github_integrations"

    integration_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    github_username = Column(String)
    github_access_token = Column(String)
    github_token_expires_at = Column(DateTime, nullable=True)
    connected_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="github_integrations")

class SlackIntegration(Base):
    __tablename__ = "slack_integrations"

    integration_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    slack_team_id = Column(String)
    slack_team_name = Column(String)
    slack_bot_token = Column(String)
    connected_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="slack_integrations")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=True)
    action = Column(String)
    entity_type = Column(String)
    entity_id = Column(String)
    changes_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
