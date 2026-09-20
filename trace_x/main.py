from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uuid
from datetime import datetime
from typing import List, Dict, Optional
import json

from trace_x.schemas.models import (
    InvestigationRequest, InvestigationResponse, Candidate,
    KnowledgeGraph, GraphNode, GraphEdge
)
from trace_x.services.discovery import DynamicOSINTGenerator
from trace_x.ml.similarity import MLSimilarityEngine

app = FastAPI(
    title="TRACE-X API",
    description="Digital Identity Intelligence Platform",
    version="2.0.0"
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for investigation results (in production: use Redis/DB)
INVESTIGATION_CACHE: Dict[str, InvestigationResponse] = {}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "TRACE-X Backend",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/investigation/create", response_model=InvestigationResponse)
async def create_investigation(request: InvestigationRequest) -> InvestigationResponse:
    """
    Create investigation for a given subject name
    
    This endpoint:
    1. Validates input
    2. Generates deterministic 3-candidate dossier
    3. Builds knowledge graph
    4. Returns results
    
    CRITICAL: Same name always produces same results (deterministic seeding)
    """
    
    if not request.subject_name or len(request.subject_name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Subject name must be at least 2 characters")

    try:
        # Generate investigation ID
        investigation_id = str(uuid.uuid4())
        
        # Generate dynamic OSINT candidates (deterministic)
        generator = DynamicOSINTGenerator(
            subject_name=request.subject_name,
            email_hint=request.email_hint,
            domain_context=request.domain_context
        )
        
        candidates = generator.generate_candidates()
        
        # Build knowledge graph
        graph_nodes, graph_edges = generator.build_knowledge_graph(candidates)
        
        # Find top candidate (highest overall confidence)
        top_candidate = max(candidates, key=lambda c: c.overall_confidence)
        
        # Count evidence and conflicts
        total_evidence = sum(len(c.evidence) for c in candidates)
        total_conflicts = sum(len(c.conflicts) for c in candidates)
        
        # Build response
        response = InvestigationResponse(
            investigation_id=investigation_id,
            subject_name=request.subject_name,
            email_hint=request.email_hint,
            timestamp=datetime.now().isoformat(),
            candidates=candidates,
            top_candidate=top_candidate,
            total_evidence_items=total_evidence,
            conflicts_detected=total_conflicts,
            graph_nodes=graph_nodes,
            graph_edges=graph_edges
        )
        
        # Cache for quick retrieval
        INVESTIGATION_CACHE[investigation_id] = response
        
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Investigation failed: {str(e)}")


@app.get("/api/investigation/{investigation_id}", response_model=InvestigationResponse)
async def get_investigation(investigation_id: str) -> InvestigationResponse:
    """
    Retrieve cached investigation result
    """
    if investigation_id not in INVESTIGATION_CACHE:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    return INVESTIGATION_CACHE[investigation_id]


@app.post("/api/investigation/candidates/{investigation_id}", response_model=List[Candidate])
async def get_candidates(investigation_id: str) -> List[Candidate]:
    """
    Get all candidates for investigation
    """
    if investigation_id not in INVESTIGATION_CACHE:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    return INVESTIGATION_CACHE[investigation_id].candidates


@app.get("/api/investigation/top-candidate/{investigation_id}", response_model=Candidate)
async def get_top_candidate(investigation_id: str) -> Candidate:
    """
    Get top candidate for investigation
    """
    if investigation_id not in INVESTIGATION_CACHE:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    investigation = INVESTIGATION_CACHE[investigation_id]
    if not investigation.top_candidate:
        raise HTTPException(status_code=404, detail="No top candidate found")
    
    return investigation.top_candidate


@app.post("/api/investigation/knowledge-graph/{investigation_id}")
async def get_knowledge_graph(investigation_id: str) -> Dict:
    """
    Get knowledge graph (nodes and edges) for visualization
    """
    if investigation_id not in INVESTIGATION_CACHE:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    investigation = INVESTIGATION_CACHE[investigation_id]
    
    return {
        "graph_id": investigation_id,
        "nodes": investigation.graph_nodes,
        "edges": investigation.graph_edges,
        "node_count": len(investigation.graph_nodes),
        "edge_count": len(investigation.graph_edges),
        "timestamp": investigation.timestamp
    }


@app.get("/api/candidate/{candidate_id}")
async def get_candidate_detail(investigation_id: str, candidate_id: str) -> Dict:
    """
    Get detailed information about a specific candidate
    """
    if investigation_id not in INVESTIGATION_CACHE:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    investigation = INVESTIGATION_CACHE[investigation_id]
    candidate = next((c for c in investigation.candidates if c.candidate_id == candidate_id), None)
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    return {
        "candidate": candidate.model_dump(),
        "platform_count": len(candidate.platforms),
        "evidence_count": len(candidate.evidence),
        "timeline_events": len(candidate.timeline_events),
        "conflict_count": len(candidate.conflicts),
        "aliases": candidate.aliases
    }


@app.get("/api/evidence/{investigation_id}")
async def get_evidence(investigation_id: str) -> Dict:
    """
    Get all evidence collected in investigation
    """
    if investigation_id not in INVESTIGATION_CACHE:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    investigation = INVESTIGATION_CACHE[investigation_id]
    
    all_evidence = []
    for candidate in investigation.candidates:
        for evidence in candidate.evidence:
            all_evidence.append({
                "evidence_id": evidence.id,
                "candidate_id": candidate.candidate_id,
                "source_platform": evidence.source_platform,
                "evidence_type": evidence.evidence_type,
                "content": evidence.content,
                "credibility_score": evidence.credibility_score,
                "timestamp": evidence.timestamp,
                "url": evidence.url
            })
    
    return {
        "investigation_id": investigation_id,
        "total_evidence": len(all_evidence),
        "evidence": sorted(all_evidence, key=lambda x: x['timestamp'], reverse=True)
    }


@app.get("/api/conflicts/{investigation_id}")
async def get_conflicts(investigation_id: str) -> Dict:
    """
    Get all detected conflicts
    """
    if investigation_id not in INVESTIGATION_CACHE:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    investigation = INVESTIGATION_CACHE[investigation_id]
    
    all_conflicts = []
    for candidate in investigation.candidates:
        for conflict in candidate.conflicts:
            all_conflicts.append({
                "conflict_id": conflict.conflict_id,
                "candidate_id": candidate.candidate_id,
                "conflict_type": conflict.conflict_type,
                "severity": conflict.severity,
                "description": conflict.description,
                "affected_platforms": conflict.affected_platforms,
                "evidence_ids": conflict.evidence_ids
            })
    
    return {
        "investigation_id": investigation_id,
        "total_conflicts": len(all_conflicts),
        "conflicts": sorted(all_conflicts, key=lambda x: x['severity'])
    }


@app.post("/api/comparison/candidates")
async def compare_candidates(investigation_id: str, candidate_ids: List[str]) -> Dict:
    """
    Compare multiple candidates side-by-side
    """
    if investigation_id not in INVESTIGATION_CACHE:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    investigation = INVESTIGATION_CACHE[investigation_id]
    candidates = [c for c in investigation.candidates if c.candidate_id in candidate_ids]
    
    if not candidates:
        raise HTTPException(status_code=404, detail="No matching candidates found")
    
    comparison = {
        "investigation_id": investigation_id,
        "comparison_timestamp": datetime.now().isoformat(),
        "candidates": [
            {
                "candidate_id": c.candidate_id,
                "name": c.name,
                "confidence": c.confidence_breakdown.model_dump(),
                "platforms": list(c.platforms.keys()),
                "aliases": c.aliases,
                "risk_level": c.risk_level,
                "evidence_count": len(c.evidence),
                "conflicts": len(c.conflicts)
            }
            for c in candidates
        ]
    }
    
    return comparison


@app.get("/api/demo/scenarios")
async def get_demo_scenarios() -> Dict:
    """
    Get demo scenarios to showcase different investigation types
    """
    return {
        "scenarios": [
            {
                "name": "Alice Johnson",
                "description": "Common name - returns ambiguous matches",
                "expected_candidates": 3,
                "expected_conflicts": "medium"
            },
            {
                "name": "Bob Chen",
                "description": "Technical professional - high confidence",
                "expected_candidates": 3,
                "expected_conflicts": "low"
            },
            {
                "name": "John Smith",
                "description": "Very common name - many ambiguous matches",
                "expected_candidates": 3,
                "expected_conflicts": "high"
            },
            {
                "name": "Sarah Developer",
                "description": "Unique name with strong signals",
                "expected_candidates": 3,
                "expected_conflicts": "low"
            },
            {
                "name": "Alex Hacker",
                "description": "Suspicious activity detected",
                "expected_candidates": 3,
                "expected_conflicts": "critical"
            }
        ]
    }


@app.post("/api/export/investigation/{investigation_id}")
async def export_investigation(investigation_id: str, format: str = "json") -> Dict:
    """
    Export investigation in different formats (json, csv)
    """
    if investigation_id not in INVESTIGATION_CACHE:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    investigation = INVESTIGATION_CACHE[investigation_id]
    
    if format == "json":
        return {
            "investigation_id": investigation.investigation_id,
            "subject_name": investigation.subject_name,
            "timestamp": investigation.timestamp,
            "export_format": "json",
            "data": investigation.model_dump()
        }
    
    elif format == "csv":
        # Convert to CSV-friendly format
        rows = []
        for candidate in investigation.candidates:
            rows.append({
                "Investigation_ID": investigation_id,
                "Candidate_ID": candidate.candidate_id,
                "Name": candidate.name,
                "Overall_Confidence": candidate.overall_confidence,
                "Name_Match": candidate.confidence_breakdown.name_match,
                "Bio_Similarity": candidate.confidence_breakdown.bio_similarity,
                "Platform_Consistency": candidate.confidence_breakdown.cross_platform_consistency,
                "Evidence_Corroboration": candidate.confidence_breakdown.evidence_corroboration,
                "Platform_Count": len(candidate.platforms),
                "Evidence_Count": len(candidate.evidence),
                "Risk_Level": candidate.risk_level
            })
        
        return {
            "investigation_id": investigation_id,
            "export_format": "csv",
            "row_count": len(rows),
            "data": rows
        }
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'json' or 'csv'")


# ─────────────────────────────────────────────────────────────
# EMAIL FOOTPRINT SCANNER MODULE
# ─────────────────────────────────────────────────────────────

from pydantic import BaseModel as PydanticBaseModel, EmailStr, field_validator
import re

class EmailScanRequest(PydanticBaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email format")
        return v


@app.post("/api/email-scanner/scan")
async def email_scanner_scan(request: EmailScanRequest) -> Dict:
    """
    Scan an email address across 55+ services.
    Returns categorized results showing which services the email is registered on.
    Deterministic: same email always produces the same results.
    """
    from trace_x.email_scanner.scanner_service import scan_email

    try:
        result = scan_email(request.email)
        return {
            "scan_id": result.scan_id,
            "email": result.email,
            "status": result.status,
            "total_services": result.total_services,
            "registered_count": result.registered_count,
            "not_registered_count": result.not_registered_count,
            "error_count": result.error_count,
            "breached_count": result.breached_count,
            "processing_time_ms": result.processing_time_ms,
            "timestamp": result.timestamp,
            "results": result.results,
            "category_summary": result.category_summary,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email scan failed: {str(e)}")


@app.get("/api/email-scanner/services")
async def email_scanner_services() -> Dict:
    """List all available services that the scanner checks."""
    from trace_x.email_scanner.scanner_service import get_services_list

    services = get_services_list()
    return {
        "total_services": len(services),
        "services": services,
    }


@app.get("/api/email-scanner/history")
async def email_scanner_history() -> Dict:
    """Return recent email scan history (in-memory cache)."""
    from trace_x.email_scanner.scanner_service import get_scan_history

    history = get_scan_history()
    return {
        "total_scans": len(history),
        "scans": history,
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ─────────────────────────────────────────────────────────────
# INTELLIGENCE FUSION MODULE
# ─────────────────────────────────────────────────────────────

class IntelligenceRequest(PydanticBaseModel):
    target_identifier: str
    email_hint: Optional[str] = None
    subject_name: Optional[str] = None


@app.post("/api/intelligence/threat-profile")
async def get_threat_profile(request: IntelligenceRequest) -> Dict:
    """
    Generate unified threat intelligence profile.
    Fuses data from 26+ simulated sources into a single threat dossier.
    """
    from trace_x.intelligence.threat_profile import ThreatProfileEngine

    try:
        engine = ThreatProfileEngine()
        profile = engine.generate_threat_profile(
            target_identifier=request.target_identifier,
            email_hint=request.email_hint or "",
            subject_name=request.subject_name or "",
        )
        return {
            "target_identifier": profile.target_identifier,
            "risk_score": profile.risk_score,
            "threat_level": profile.threat_level.value,
            "bot_probability": profile.bot_probability,
            "bot_explanation": profile.bot_explanation,
            "threat_components": [
                {
                    "name": c.name,
                    "score": c.score,
                    "weight": c.weight,
                    "explanation": c.explanation,
                    "indicators": c.indicators,
                }
                for c in profile.threat_components
            ],
            "data_sources": [
                {
                    "source_name": s.source_name,
                    "category": s.category,
                    "status": s.status.value,
                    "records_found": s.records_found,
                    "confidence": s.confidence,
                    "last_checked": s.last_checked,
                    "key_findings": s.key_findings,
                }
                for s in profile.data_sources
            ],
            "total_sources_queried": profile.total_sources_queried,
            "sources_with_data": profile.sources_with_data,
            "total_records": profile.total_records,
            "recommendations": profile.recommendations,
            "assessment_summary": profile.assessment_summary,
            "confidence": profile.confidence,
            "generated_at": profile.generated_at,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Threat profile generation failed: {str(e)}")


@app.post("/api/intelligence/behavioral-analysis")
async def get_behavioral_analysis(request: IntelligenceRequest) -> Dict:
    """
    Generate behavioral fingerprint for a target identity.
    Analyzes circadian rhythm, linguistic style, interaction patterns, and more.
    """
    from trace_x.intelligence.behavioral_analysis import BehavioralAnalysisEngine

    try:
        engine = BehavioralAnalysisEngine()
        sig = engine.generate_behavioral_signature(
            target_identifier=request.target_identifier,
            email_hint=request.email_hint or "",
            subject_name=request.subject_name or "",
        )
        return {
            "target_identifier": sig.target_identifier,
            "circadian": {
                "hourly_activity": sig.circadian.hourly_activity,
                "peak_hours": sig.circadian.peak_hours,
                "sleep_gap_start": sig.circadian.sleep_gap_start,
                "sleep_duration_hours": sig.circadian.sleep_duration_hours,
                "inferred_timezone": sig.circadian.inferred_timezone,
                "consistency_score": sig.circadian.consistency_score,
            },
            "linguistic": {
                "avg_word_length": sig.linguistic.avg_word_length,
                "vocabulary_richness": sig.linguistic.vocabulary_richness,
                "emoji_frequency": sig.linguistic.emoji_frequency,
                "favorite_emojis": sig.linguistic.favorite_emojis,
                "capitalization_style": sig.linguistic.capitalization_style,
                "punctuation_density": sig.linguistic.punctuation_density,
                "avg_sentence_length": sig.linguistic.avg_sentence_length,
                "formality_score": sig.linguistic.formality_score,
                "language_detected": sig.linguistic.language_detected,
            },
            "interaction": {
                "reply_ratio": sig.interaction.reply_ratio,
                "retweet_ratio": sig.interaction.retweet_ratio,
                "original_content_ratio": sig.interaction.original_content_ratio,
                "engagement_style": sig.interaction.engagement_style,
                "avg_response_time_minutes": sig.interaction.avg_response_time_minutes,
                "network_density": sig.interaction.network_density,
                "top_interaction_topics": sig.interaction.top_interaction_topics,
            },
            "technical": {
                "primary_device": sig.technical.primary_device,
                "os_fingerprint": sig.technical.os_fingerprint,
                "primary_browser": sig.technical.primary_browser,
                "ip_consistency": sig.technical.ip_consistency,
                "primary_region": sig.technical.primary_region,
                "device_count": sig.technical.device_count,
                "session_duration_avg_minutes": sig.technical.session_duration_avg_minutes,
            },
            "content": {
                "top_topics": sig.content.top_topics,
                "topic_consistency": sig.content.topic_consistency,
                "content_type_distribution": sig.content.content_type_distribution,
                "posting_frequency": sig.content.posting_frequency,
                "content_originality": sig.content.content_originality,
                "sentiment_distribution": sig.content.sentiment_distribution,
            },
            "signature_strength": sig.signature_strength,
            "uniqueness_score": sig.uniqueness_score,
            "generated_at": sig.generated_at,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Behavioral analysis failed: {str(e)}")


@app.post("/api/intelligence/bot-detection")
async def get_bot_detection(request: IntelligenceRequest) -> Dict:
    """
    Run bot detection analysis on a target identity.
    Returns bot probability (0.0-1.0) with per-factor breakdown.
    """
    from trace_x.intelligence.bot_detector import BotDetectionEngine

    try:
        engine = BotDetectionEngine()
        result = engine.detect_bot(
            target_identifier=request.target_identifier,
            email_hint=request.email_hint or "",
            subject_name=request.subject_name or "",
        )
        return {
            "target_identifier": result.target_identifier,
            "bot_probability": result.bot_probability,
            "risk_label": result.risk_label,
            "factors": [
                {
                    "name": f.name,
                    "score": f.score,
                    "weight": f.weight,
                    "explanation": f.explanation,
                    "indicators": f.indicators,
                }
                for f in result.factors
            ],
            "explanation": result.explanation,
            "confidence": result.confidence,
            "generated_at": result.generated_at,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bot detection failed: {str(e)}")


@app.post("/api/intelligence/risk-assessment")
async def get_risk_assessment(request: IntelligenceRequest) -> Dict:
    """
    Comprehensive risk assessment using probability × impact matrix.
    Returns overall risk score, threat level, and per-dimension breakdown.
    """
    from trace_x.intelligence.risk_scoring import RiskScoringEngine

    try:
        engine = RiskScoringEngine()
        result = engine.assess_risk(
            target_identifier=request.target_identifier,
            email_hint=request.email_hint or "",
            subject_name=request.subject_name or "",
        )
        return {
            "target_identifier": result.target_identifier,
            "overall_risk_score": result.overall_risk_score,
            "threat_level": result.threat_level,
            "dimensions": [
                {
                    "name": d.name,
                    "probability": d.probability,
                    "impact": d.impact,
                    "combined_score": d.combined_score,
                    "level": d.level,
                    "explanation": d.explanation,
                    "mitigations": d.mitigations,
                }
                for d in result.dimensions
            ],
            "matrix_position": {
                "probability_band": result.matrix_position.probability_band,
                "impact_band": result.matrix_position.impact_band,
                "risk_level": result.matrix_position.risk_level,
                "color": result.matrix_position.color,
            },
            "probability_label": result.probability_label,
            "impact_label": result.impact_label,
            "recommendations": result.recommendations,
            "risk_trend": result.risk_trend,
            "historical_scores": result.historical_scores,
            "confidence": result.confidence,
            "generated_at": result.generated_at,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")


@app.get("/api/intelligence/capabilities")
async def get_intelligence_capabilities() -> Dict:
    """List all available intelligence modules and their status."""
    return {
        "platform": "TRACE-X Intelligence Fusion Platform",
        "version": "2.0.0",
        "modules": [
            {
                "name": "Threat Profile Engine",
                "endpoint": "/api/intelligence/threat-profile",
                "status": "ACTIVE",
                "description": "Unified threat intelligence dossier fusing 26+ data sources",
                "data_sources": 26,
            },
            {
                "name": "Behavioral Analysis Engine",
                "endpoint": "/api/intelligence/behavioral-analysis",
                "status": "ACTIVE",
                "description": "Circadian rhythm, linguistic, interaction, and technical fingerprinting",
            },
            {
                "name": "Bot Detection Engine",
                "endpoint": "/api/intelligence/bot-detection",
                "status": "ACTIVE",
                "description": "Ensemble bot probability scoring across 5 detection factors",
            },
            {
                "name": "Risk Scoring Engine",
                "endpoint": "/api/intelligence/risk-assessment",
                "status": "ACTIVE",
                "description": "Probability × Impact risk matrix with 5 threat dimensions",
            },
            {
                "name": "Entity Resolution Engine",
                "endpoint": "/api/investigation/create",
                "status": "ACTIVE",
                "description": "Bayesian entity resolution with explainable confidence scoring",
            },
            {
                "name": "Email Footprint Scanner",
                "endpoint": "/api/email-scanner/scan",
                "status": "ACTIVE",
                "description": "Real email-to-platform mapping using holehe + supplementary providers",
            },
        ],
        "total_data_sources": 26,
        "layers": [
            "Layer 1: Investigation Engine",
            "Layer 2: Distributed Data Sources (26 providers)",
            "Layer 3: Data Enrichment",
            "Layer 4: Behavioral Analysis",
            "Layer 5: Threat Intelligence Feeds",
            "Layer 6: Advanced Analytics (ML/NLP)",
            "Layer 7: Risk & Threat Scoring",
            "Layer 8: Attribution Engine",
        ],
    }
