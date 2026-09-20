"""
TRACE-X Threat Profile Engine.

Generates a unified threat intelligence dossier for any target identifier.
Fuses data from multiple sources into a single ThreatProfile object with:
- Risk score (0-100) using probability × impact
- Threat level (NONE → CRITICAL)
- Bot probability with explanation
- Data source attribution
- Actionable recommendations

Uses deterministic seeding for demo reproducibility.
"""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


# ── Enums ────────────────────────────────────────────────────

class ThreatLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DataSourceStatus(str, Enum):
    CONNECTED = "CONNECTED"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"


# ── Data Classes ─────────────────────────────────────────────

@dataclass
class DataSourceResult:
    """Result from a single intelligence data source."""
    source_name: str
    category: str  # e.g. "Social", "Developer", "Threat Intel", "Dark Web"
    status: DataSourceStatus
    records_found: int
    confidence: float  # 0.0 - 1.0
    last_checked: str  # ISO timestamp
    key_findings: List[str] = field(default_factory=list)


@dataclass
class ThreatComponent:
    """Individual component of the overall threat score."""
    name: str
    score: float  # 0.0 - 1.0
    weight: float
    explanation: str
    indicators: List[str] = field(default_factory=list)


@dataclass
class ThreatProfile:
    """Unified threat intelligence dossier for a target."""
    target_identifier: str
    risk_score: float  # 0-100
    threat_level: ThreatLevel
    bot_probability: float  # 0.0 - 1.0
    bot_explanation: str
    threat_components: List[ThreatComponent]
    data_sources: List[DataSourceResult]
    total_sources_queried: int
    sources_with_data: int
    total_records: int
    recommendations: List[str]
    assessment_summary: str
    generated_at: str
    confidence: float  # 0.0 - 1.0


# ── Demo Override Data ───────────────────────────────────────

_DEMO_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "ishan": {
        "risk_score": 8.5,
        "threat_level": ThreatLevel.NONE,
        "bot_probability": 0.02,
        "bot_explanation": "Account exhibits strong human behavioral patterns: irregular posting times, diverse vocabulary, natural engagement patterns. Profile is well-established with consistent activity over 3+ years.",
        "assessment_summary": "Target is a verified student at JBIET (Diploma from Govt Polytechnic, 10th from SHA School). Active developer on GitHub with consistent contributions. No threat indicators detected. All social accounts show organic growth patterns.",
        "recommendations": [
            "No action required — profile is clean",
            "Continue passive monitoring as standard practice",
            "Profile suitable for professional networking outreach"
        ]
    },
    "hammad": {
        "risk_score": 6.2,
        "threat_level": ThreatLevel.NONE,
        "bot_probability": 0.03,
        "bot_explanation": "Strong human behavioral signature detected. Irregular posting cadence, diverse content topics, natural follower growth curve. Account age and activity consistency indicate genuine user.",
        "assessment_summary": "Target is a verified student at JBIET. Hackathon Winner (HackX). Active across GitHub, LinkedIn, YouTube, and Telegram. Previously at Krishnaveni (Intermediate) and Triveni (School). No threat indicators or suspicious patterns detected.",
        "recommendations": [
            "No action required — profile is clean",
            "Notable achievement: hackathon winner (positive signal)",
            "Continue passive monitoring as standard practice"
        ]
    },
    "lokesh": {
        "risk_score": 7.1,
        "threat_level": ThreatLevel.NONE,
        "bot_probability": 0.04,
        "bot_explanation": "Human behavioral patterns confirmed. Natural sleep/wake posting cycle, diverse content creation, genuine interaction patterns with real users.",
        "assessment_summary": "Target is a verified student at JBREC. Completed internship at NetworkWorks. Active across GitHub, LinkedIn, YouTube, Telegram, and LeetCode. Previously at Vector College (Intermediate) and Vishvodaya (School). No threat indicators detected.",
        "recommendations": [
            "No action required — profile is clean",
            "Notable: active LeetCode profile indicates genuine technical interest",
            "Continue passive monitoring as standard practice"
        ]
    },
}


# ── Engine ───────────────────────────────────────────────────

class ThreatProfileEngine:
    """
    Generates unified threat intelligence profiles.

    For demo mode: uses deterministic seeding to generate consistent,
    realistic-looking threat assessments. Demo overrides ensure
    known subjects get accurate, curated results.

    In production: would call 50+ real APIs in parallel.
    """

    # Simulated data sources the platform "checks"
    DATA_SOURCES = [
        ("GitHub API", "Developer", 0.98),
        ("GitLab API", "Developer", 0.95),
        ("npm Registry", "Developer", 0.92),
        ("PyPI Registry", "Developer", 0.90),
        ("LinkedIn API", "Professional", 0.85),
        ("X (Twitter) API", "Social", 0.88),
        ("Instagram Graph API", "Social", 0.82),
        ("Reddit API", "Social", 0.90),
        ("Have I Been Pwned", "Threat Intel", 0.99),
        ("Shodan", "Threat Intel", 0.94),
        ("VirusTotal", "Threat Intel", 0.96),
        ("AbuseIPDB", "Threat Intel", 0.91),
        ("Censys", "Threat Intel", 0.89),
        ("URLhaus", "Threat Intel", 0.87),
        ("Blockchain.com", "Crypto", 0.80),
        ("Etherscan", "Crypto", 0.82),
        ("WHOIS Lookup", "Infrastructure", 0.95),
        ("DNS Records", "Infrastructure", 0.93),
        ("Clearbit", "Enrichment", 0.78),
        ("ZeroBounce", "Enrichment", 0.85),
        ("Dark Web Monitor", "Dark Web", 0.70),
        ("IntelX", "Dark Web", 0.72),
        ("Telegram OSINT", "Social", 0.75),
        ("Discord OSINT", "Social", 0.73),
        ("Steam API", "Gaming", 0.88),
        ("Chess.com API", "Gaming", 0.92),
    ]

    def __init__(self):
        pass

    def _get_seed(self, identifier: str) -> int:
        """Deterministic seed from identifier."""
        return int(hashlib.sha256(identifier.lower().encode()).hexdigest()[:8], 16)

    def _check_demo_override(self, identifier: str) -> Optional[str]:
        """Check if identifier matches a demo override key."""
        ident_lower = identifier.lower()
        for key in _DEMO_OVERRIDES:
            if key in ident_lower:
                return key
        return None

    def generate_threat_profile(
        self,
        target_identifier: str,
        email_hint: str = "",
        subject_name: str = "",
    ) -> ThreatProfile:
        """
        Generate a complete threat intelligence profile.

        Args:
            target_identifier: Primary identifier (email or name).
            email_hint: Optional email for additional context.
            subject_name: Optional subject name for overrides.

        Returns:
            ThreatProfile with all intelligence fusion data.
        """
        combined = f"{target_identifier} {email_hint} {subject_name}".lower().strip()
        seed = self._get_seed(combined)
        rng = random.Random(seed)

        # Check for demo overrides
        override_key = self._check_demo_override(combined)
        override = _DEMO_OVERRIDES.get(override_key) if override_key else None

        # Generate data source results
        data_sources = self._generate_data_sources(rng, override_key)

        # Generate threat components
        threat_components = self._generate_threat_components(rng, override)

        # Calculate overall risk score
        if override:
            risk_score = override["risk_score"]
            threat_level = override["threat_level"]
            bot_probability = override["bot_probability"]
            bot_explanation = override["bot_explanation"]
            assessment_summary = override["assessment_summary"]
            recommendations = override["recommendations"]
        else:
            risk_score = self._calculate_risk_score(threat_components)
            threat_level = self._risk_to_level(risk_score)
            bot_probability = self._calculate_bot_probability(rng)
            bot_explanation = self._generate_bot_explanation(bot_probability, rng)
            assessment_summary = self._generate_assessment_summary(
                target_identifier, risk_score, threat_level, rng
            )
            recommendations = self._generate_recommendations(threat_level, risk_score, rng)

        sources_with_data = sum(1 for s in data_sources if s.records_found > 0)
        total_records = sum(s.records_found for s in data_sources)

        confidence = 0.95 if override else min(0.60 + (sources_with_data / len(data_sources)) * 0.35, 0.92)

        return ThreatProfile(
            target_identifier=target_identifier,
            risk_score=round(risk_score, 1),
            threat_level=threat_level,
            bot_probability=round(bot_probability, 3),
            bot_explanation=bot_explanation,
            threat_components=threat_components,
            data_sources=data_sources,
            total_sources_queried=len(data_sources),
            sources_with_data=sources_with_data,
            total_records=total_records,
            recommendations=recommendations,
            assessment_summary=assessment_summary,
            generated_at=datetime.now().isoformat(),
            confidence=round(confidence, 3),
        )

    def _generate_data_sources(
        self, rng: random.Random, override_key: Optional[str]
    ) -> List[DataSourceResult]:
        """Generate simulated data source results."""
        sources = []
        now = datetime.now()

        for name, category, base_reliability in self.DATA_SOURCES:
            # Demo overrides get more "CONNECTED" sources
            if override_key:
                status_roll = rng.random()
                if status_roll < 0.75:
                    status = DataSourceStatus.CONNECTED
                elif status_roll < 0.90:
                    status = DataSourceStatus.PARTIAL
                else:
                    status = DataSourceStatus.UNAVAILABLE
            else:
                status_roll = rng.random()
                if status_roll < 0.55:
                    status = DataSourceStatus.CONNECTED
                elif status_roll < 0.80:
                    status = DataSourceStatus.PARTIAL
                else:
                    status = DataSourceStatus.UNAVAILABLE

            if status == DataSourceStatus.UNAVAILABLE:
                records = 0
                findings = []
            elif status == DataSourceStatus.PARTIAL:
                records = rng.randint(1, 5)
                findings = [f"Partial data retrieved from {name}"]
            else:
                records = rng.randint(3, 25)
                findings = self._generate_findings(name, category, rng)

            checked_offset = rng.randint(0, 30)
            checked_time = now - timedelta(seconds=checked_offset)

            sources.append(DataSourceResult(
                source_name=name,
                category=category,
                status=status,
                records_found=records,
                confidence=round(base_reliability * rng.uniform(0.85, 1.0), 3),
                last_checked=checked_time.isoformat(),
                key_findings=findings,
            ))

        return sources

    def _generate_findings(
        self, source_name: str, category: str, rng: random.Random
    ) -> List[str]:
        """Generate realistic key findings for a data source."""
        findings_pool = {
            "Developer": [
                "Active repository contributions detected",
                "Public code repositories found",
                "Package maintainer role identified",
                "Open source contributions confirmed",
                "CI/CD pipeline configurations found",
            ],
            "Professional": [
                "Employment history verified",
                "Professional connections mapped",
                "Industry affiliations confirmed",
                "Endorsements and recommendations found",
            ],
            "Social": [
                "Social media presence confirmed",
                "Follower network mapped",
                "Content posting patterns analyzed",
                "Engagement metrics collected",
                "Cross-platform username correlation found",
            ],
            "Threat Intel": [
                "No active threat indicators",
                "Breach exposure check completed",
                "No malicious infrastructure linked",
                "IP reputation: clean",
                "Domain reputation: neutral",
            ],
            "Crypto": [
                "No cryptocurrency wallets associated",
                "Blockchain analysis: no suspicious transactions",
            ],
            "Infrastructure": [
                "Domain registration data collected",
                "DNS resolution records mapped",
                "SSL certificate history checked",
            ],
            "Enrichment": [
                "Email validation: deliverable",
                "Email reputation: good",
                "Company association identified",
            ],
            "Dark Web": [
                "No dark web mentions found",
                "No forum activity detected",
                "No leaked credentials in monitored sources",
            ],
            "Gaming": [
                "Gaming profile found",
                "Activity patterns consistent with casual usage",
            ],
        }

        pool = findings_pool.get(category, ["Data collected successfully"])
        count = min(rng.randint(1, 3), len(pool))
        return rng.sample(pool, count)

    def _generate_threat_components(
        self, rng: random.Random, override: Optional[Dict]
    ) -> List[ThreatComponent]:
        """Generate the 5 threat scoring components."""
        if override:
            # Safe profile — all scores very low
            return [
                ThreatComponent(
                    name="Malicious Activity",
                    score=round(rng.uniform(0.0, 0.05), 3),
                    weight=0.25,
                    explanation="No malicious activity detected. No association with known threat actors, malware distribution, or phishing campaigns.",
                    indicators=["Clean breach history", "No dark web presence", "No fraud reports"],
                ),
                ThreatComponent(
                    name="Targeting Probability",
                    score=0.0,
                    weight=0.20,
                    explanation="No evidence of targeting behavior. Account shows normal social interaction patterns.",
                    indicators=["No reconnaissance activity", "Normal browsing patterns"],
                ),
                ThreatComponent(
                    name="Technical Capability",
                    score=round(rng.uniform(0.1, 0.3), 3),
                    weight=0.20,
                    explanation="Standard technical proficiency consistent with student/developer background. No advanced offensive capabilities detected.",
                    indicators=["Developer skillset (non-offensive)", "No exploit development"],
                ),
                ThreatComponent(
                    name="Imminence",
                    score=0.0,
                    weight=0.20,
                    explanation="No imminent threat indicators. No escalating behavior patterns or pre-attack reconnaissance detected.",
                    indicators=["Stable activity patterns", "No behavioral escalation"],
                ),
                ThreatComponent(
                    name="Potential Impact",
                    score=round(rng.uniform(0.0, 0.05), 3),
                    weight=0.15,
                    explanation="Minimal impact potential. Target has no access to high-value systems or sensitive data beyond personal accounts.",
                    indicators=["Student account", "Limited organizational access"],
                ),
            ]
        else:
            # Random profile — varied threat scores
            malicious = round(rng.uniform(0.05, 0.45), 3)
            targeting = round(rng.uniform(0.0, 0.25), 3)
            capability = round(rng.uniform(0.1, 0.55), 3)
            imminence = round(rng.uniform(0.0, 0.20), 3)
            impact = round(rng.uniform(0.05, 0.40), 3)

            return [
                ThreatComponent(
                    name="Malicious Activity",
                    score=malicious,
                    weight=0.25,
                    explanation=self._explain_malicious(malicious, rng),
                    indicators=self._malicious_indicators(malicious, rng),
                ),
                ThreatComponent(
                    name="Targeting Probability",
                    score=targeting,
                    weight=0.20,
                    explanation=f"{'Low' if targeting < 0.15 else 'Moderate'} targeting probability based on interaction analysis and content monitoring.",
                    indicators=["Network analysis complete", "Content pattern review done"],
                ),
                ThreatComponent(
                    name="Technical Capability",
                    score=capability,
                    weight=0.20,
                    explanation=f"{'Basic' if capability < 0.3 else 'Intermediate'} technical capability detected from public code and activity analysis.",
                    indicators=["Code complexity analysis", "Tool usage profiling"],
                ),
                ThreatComponent(
                    name="Imminence",
                    score=imminence,
                    weight=0.20,
                    explanation=f"{'No' if imminence < 0.1 else 'Low'} imminent threat indicators based on behavioral timeline analysis.",
                    indicators=["Timeline analysis complete", "No escalation patterns"],
                ),
                ThreatComponent(
                    name="Potential Impact",
                    score=impact,
                    weight=0.15,
                    explanation=f"{'Low' if impact < 0.2 else 'Moderate'} potential impact based on access level and organizational reach.",
                    indicators=["Access scope evaluated", "Data sensitivity reviewed"],
                ),
            ]

    def _explain_malicious(self, score: float, rng: random.Random) -> str:
        if score < 0.15:
            return "No significant malicious activity indicators. Clean record across all monitored threat intelligence feeds."
        elif score < 0.30:
            return "Minor indicators detected. Possible exposure in data breaches but no active malicious behavior confirmed."
        else:
            return "Moderate risk indicators. Account appears in some breach databases and shows some patterns warranting continued monitoring."

    def _malicious_indicators(self, score: float, rng: random.Random) -> List[str]:
        if score < 0.15:
            return ["Clean breach history", "No dark web mentions", "No fraud reports"]
        elif score < 0.30:
            return ["Minor breach exposure", "No active threats", "Monitoring recommended"]
        else:
            return ["Breach database matches found", "Elevated monitoring suggested", "Pattern review pending"]

    def _calculate_risk_score(self, components: List[ThreatComponent]) -> float:
        """Weighted sum of threat components, scaled to 0-100."""
        weighted_sum = sum(c.score * c.weight for c in components)
        return round(weighted_sum * 100, 1)

    def _risk_to_level(self, risk_score: float) -> ThreatLevel:
        if risk_score < 10:
            return ThreatLevel.NONE
        elif risk_score < 25:
            return ThreatLevel.LOW
        elif risk_score < 50:
            return ThreatLevel.MEDIUM
        elif risk_score < 75:
            return ThreatLevel.HIGH
        else:
            return ThreatLevel.CRITICAL

    def _calculate_bot_probability(self, rng: random.Random) -> float:
        """Generate bot probability for unknown targets."""
        return round(rng.uniform(0.05, 0.35), 3)

    def _generate_bot_explanation(self, prob: float, rng: random.Random) -> str:
        if prob < 0.15:
            return "Strong human behavioral indicators: natural posting cadence, diverse vocabulary, organic follower growth. Very low bot probability."
        elif prob < 0.30:
            return "Mostly human behavioral patterns detected. Minor automation indicators (regular posting schedule) but consistent with productivity tools."
        else:
            return "Some automated behavior patterns detected. Posting regularity and content patterns suggest possible use of scheduling tools or partial automation."

    def _generate_assessment_summary(
        self, target: str, risk: float, level: ThreatLevel, rng: random.Random
    ) -> str:
        if level == ThreatLevel.NONE:
            return f"Target '{target}' presents no identifiable threat. All intelligence indicators are within normal parameters. Profile appears genuine with consistent digital footprint."
        elif level == ThreatLevel.LOW:
            return f"Target '{target}' presents low risk. Minor exposure in data breaches detected. No active malicious behavior. Routine monitoring recommended."
        elif level == ThreatLevel.MEDIUM:
            return f"Target '{target}' presents moderate risk. Some indicators warrant attention including breach exposure and elevated online activity. Enhanced monitoring recommended."
        elif level == ThreatLevel.HIGH:
            return f"Target '{target}' presents high risk. Multiple threat indicators active. Recommend immediate investigation and active countermeasures."
        else:
            return f"Target '{target}' presents CRITICAL risk. Immediate action required. Multiple confirmed threat indicators across intelligence sources."

    def _generate_recommendations(
        self, level: ThreatLevel, risk: float, rng: random.Random
    ) -> List[str]:
        base = []
        if level == ThreatLevel.NONE:
            base = [
                "No action required — profile assessment is clean",
                "Continue standard passive monitoring",
                "Suitable for professional engagement",
            ]
        elif level == ThreatLevel.LOW:
            base = [
                "Maintain routine monitoring cadence",
                "Review breach exposure details for credential hygiene",
                "No immediate action required",
                "Recommend password rotation for exposed accounts",
            ]
        elif level == ThreatLevel.MEDIUM:
            base = [
                "Increase monitoring frequency to weekly",
                "Investigate breach exposure in detail",
                "Review associated accounts for suspicious activity",
                "Consider blocking from sensitive systems",
                "Alert security operations center",
            ]
        elif level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
            base = [
                "IMMEDIATE: Escalate to security operations team",
                "Block access to all organizational systems",
                "Initiate incident response procedure",
                "Preserve evidence for potential forensic analysis",
                "Notify relevant stakeholders and legal team",
                "Coordinate with law enforcement if applicable",
            ]
        return base
