from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, List, Dict, Optional
from datetime import datetime

class VulnerabilitySchema(BaseModel):
    vuln_id: str
    file_path: str
    line_number: int
    vulnerability_type: str
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    cvss_score: float
    description: str
    exploitation_scenario: Optional[str] = None
    code_snippet: str
    suggested_fix: Optional[str] = None
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class DependencyVulnerabilitySchema(BaseModel):
    dep_vuln_id: str
    package_name: str
    current_version: str
    vulnerable_in: Optional[str] = None
    cve_id: str
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    description: str
    recommendation: str
    published_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class AuditRecordSchema(BaseModel):
    audit_id: str
    repo_url: str
    repo_owner: str
    repo_name: str
    status: Literal["QUEUED", "SCANNING", "ANALYZING", "COMPLETE", "FAILED"]
    started_at: datetime
    completed_at: Optional[datetime] = None
    execution_time_ms: int = 0
    total_files_scanned: int = 0
    total_loc: int = 0
    vulnerabilities: List[VulnerabilitySchema] = []
    dependency_vulns: List[DependencyVulnerabilitySchema] = []
    summary_json: Dict[str, int] = Field(default_factory=lambda: {"critical": 0, "high": 0, "medium": 0, "low": 0})
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class AuditStartRequest(BaseModel):
    repo_url: str
    slack_channel_id: Optional[str] = None
    slack_user_id: Optional[str] = None

class UserSchema(BaseModel):
    user_id: str
    github_username: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
