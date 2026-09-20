from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime

class ConflictType(str, Enum):
    LOCATION_OVERLAP = "LOCATION_OVERLAP"
    TIMELINE_CONFLICT = "TIMELINE_CONFLICT"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    PLATFORM_INCONSISTENCY = "PLATFORM_INCONSISTENCY"

class MatchStatus(str, Enum):
    STRONG_MATCH = "STRONG_MATCH"
    POSSIBLE_MATCH = "POSSIBLE_MATCH"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"

class PlatformProfile(BaseModel):
    platform: str  # github, linkedin, twitter, instagram, snapchat, etc.
    username: str
    url: str
    follower_count: int = 0
    verification_status: bool = False
    last_activity: Optional[str] = None

class TimelineEvent(BaseModel):
    timestamp: str  # RFC-3339 format
    event_type: str  # education, job, hackathon, project, social
    title: str
    description: str
    platform: str
    location: Optional[str] = None

class Evidence(BaseModel):
    id: str
    source_platform: str
    evidence_type: str
    content: str
    timestamp: str  # RFC-3339 format
    credibility_score: float = Field(ge=5.0, le=98.0)
    url: str
    metadata: Dict[str, str] = {}

class Conflict(BaseModel):
    conflict_id: str
    conflict_type: ConflictType
    severity: str  # low, medium, high, critical
    description: str
    affected_platforms: List[str]
    evidence_ids: List[str]

class FeatureContribution(BaseModel):
    feature: str
    raw_value: float
    weight: float
    likelihood_ratio: float
    log_odds_delta: float
    explanation: str

class ConfidenceBreakdown(BaseModel):
    name_match: float = Field(ge=5.0, le=98.0)  # mapped from name_score
    bio_similarity: float = Field(ge=5.0, le=98.0)  # mapped from bio_score
    cross_platform_consistency: float = Field(ge=5.0, le=98.0)
    evidence_corroboration: float = Field(ge=5.0, le=98.0)  # mapped from evidence_boost
    conflict_penalty: float = 0.0
    prior: float = 0.3
    posterior: float = 0.0
    log_odds: float = 0.0
    feature_contributions: List[FeatureContribution] = []
    explanation: str = ""
    match_status: MatchStatus = MatchStatus.INSUFFICIENT_EVIDENCE
    match_reasons: List[str] = []
    mismatch_reasons: List[str] = []
    supporting_evidence: List[str] = []
    contradicting_evidence: List[str] = []
    missing_evidence: List[str] = []

    @validator('name_match', 'bio_similarity', 'cross_platform_consistency', 'evidence_corroboration', pre=True)
    def clamp_scores(cls, v):
        if v is None:
            return 5.0
        v = float(v)
        return max(5.0, min(98.0, v))

class Candidate(BaseModel):
    candidate_id: str
    name: str
    bio: Optional[str] = None
    overall_confidence: float = Field(ge=5.0, le=98.0)
    confidence_breakdown: ConfidenceBreakdown
    aliases: List[str] = []
    platforms: Dict[str, PlatformProfile] = {}
    timeline_events: List[TimelineEvent] = []
    evidence: List[Evidence] = []
    conflicts: List[Conflict] = []
    investigation_tags: List[str] = []
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL

    class Config:
        use_enum_values = True

class InvestigationRequest(BaseModel):
    subject_name: str
    email_hint: Optional[str] = None
    domain_context: Optional[str] = None

class InvestigationResponse(BaseModel):
    investigation_id: str
    subject_name: str
    email_hint: Optional[str] = None
    timestamp: str
    candidates: List[Candidate]
    top_candidate: Optional[Candidate]
    total_evidence_items: int
    conflicts_detected: int
    graph_nodes: List[Dict] = []
    graph_edges: List[Dict] = []

class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str  # candidate, platform, person, organization
    confidence: float
    metadata: Dict[str, str] = {}

class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str
    strength: float  # 0-1, confidence of relationship
    evidence_ids: List[str] = []

class KnowledgeGraph(BaseModel):
    graph_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    serialization_format: str = "json"
    timestamp: str
