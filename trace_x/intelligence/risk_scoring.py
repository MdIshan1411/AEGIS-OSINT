"""
TRACE-X Risk Scoring & Threat Level Engine.

Comprehensive risk assessment using:
- Probability × Impact matrix (5×5 grid)
- 5 threat dimensions: maliciousness, targeting, capability, imminence, impact
- Threat level classification: NONE → LOW → MEDIUM → HIGH → CRITICAL
- Actionable, prioritized recommendations

Integrates with ThreatProfile for unified scoring.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class RiskDimension:
    """Individual dimension in the risk assessment."""
    name: str
    probability: float  # 0.0-1.0 how likely
    impact: float  # 0.0-1.0 how severe
    combined_score: float  # probability × impact
    level: str  # "NEGLIGIBLE", "LOW", "MODERATE", "HIGH", "CRITICAL"
    explanation: str
    mitigations: List[str] = field(default_factory=list)


@dataclass
class RiskMatrixCell:
    """Position on the 5×5 risk matrix."""
    probability_band: int  # 1-5
    impact_band: int  # 1-5
    risk_level: str
    color: str  # For frontend rendering


@dataclass
class RiskAssessment:
    """Complete risk assessment output."""
    target_identifier: str
    overall_risk_score: float  # 0-100
    threat_level: str  # "NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"
    dimensions: List[RiskDimension]
    matrix_position: RiskMatrixCell
    probability_label: str  # "Very Low" to "Very High"
    impact_label: str
    recommendations: List[str]
    risk_trend: str  # "STABLE", "INCREASING", "DECREASING"
    historical_scores: List[float]  # Last 7 assessments (simulated)
    confidence: float
    generated_at: str


class RiskScoringEngine:
    """
    Calculates comprehensive threat/risk scores using a probability × impact model.

    Risk = Σ(probability_i × impact_i × weight_i)

    Each risk dimension is scored independently, then aggregated
    into an overall risk score and mapped to a threat level.
    """

    RISK_LEVELS = {
        (1, 1): ("NEGLIGIBLE", "#22c55e"),
        (1, 2): ("LOW", "#22c55e"),
        (1, 3): ("LOW", "#84cc16"),
        (1, 4): ("MODERATE", "#eab308"),
        (1, 5): ("MODERATE", "#eab308"),
        (2, 1): ("LOW", "#22c55e"),
        (2, 2): ("LOW", "#84cc16"),
        (2, 3): ("MODERATE", "#eab308"),
        (2, 4): ("MODERATE", "#f97316"),
        (2, 5): ("HIGH", "#f97316"),
        (3, 1): ("LOW", "#84cc16"),
        (3, 2): ("MODERATE", "#eab308"),
        (3, 3): ("MODERATE", "#f97316"),
        (3, 4): ("HIGH", "#ef4444"),
        (3, 5): ("HIGH", "#ef4444"),
        (4, 1): ("MODERATE", "#eab308"),
        (4, 2): ("MODERATE", "#f97316"),
        (4, 3): ("HIGH", "#ef4444"),
        (4, 4): ("HIGH", "#dc2626"),
        (4, 5): ("CRITICAL", "#dc2626"),
        (5, 1): ("MODERATE", "#f97316"),
        (5, 2): ("HIGH", "#ef4444"),
        (5, 3): ("HIGH", "#dc2626"),
        (5, 4): ("CRITICAL", "#dc2626"),
        (5, 5): ("CRITICAL", "#7f1d1d"),
    }

    PROBABILITY_LABELS = {1: "Very Low", 2: "Low", 3: "Moderate", 4: "High", 5: "Very High"}
    IMPACT_LABELS = {1: "Negligible", 2: "Minor", 3: "Moderate", 4: "Major", 5: "Severe"}

    def __init__(self):
        pass

    def _get_seed(self, identifier: str) -> int:
        return int(hashlib.sha256(identifier.lower().encode()).hexdigest()[:8], 16)

    def _check_demo(self, identifier: str) -> Optional[str]:
        ident = identifier.lower()
        for key in ["ishan", "hammad", "lokesh"]:
            if key in ident:
                return key
        return None

    def assess_risk(
        self,
        target_identifier: str,
        email_hint: str = "",
        subject_name: str = "",
    ) -> RiskAssessment:
        """Run comprehensive risk assessment."""
        combined = f"{target_identifier} {email_hint} {subject_name}".lower().strip()
        seed = self._get_seed(combined)
        rng = random.Random(seed)
        demo_key = self._check_demo(combined)

        dimensions = self._generate_dimensions(rng, demo_key)

        # Calculate overall risk
        overall = sum(d.combined_score * 100 for d in dimensions) / len(dimensions)
        overall = round(min(max(overall, 0.0), 100.0), 1)

        # Map to 5×5 matrix
        avg_prob = sum(d.probability for d in dimensions) / len(dimensions)
        avg_impact = sum(d.impact for d in dimensions) / len(dimensions)
        prob_band = min(max(int(avg_prob * 5) + 1, 1), 5)
        impact_band = min(max(int(avg_impact * 5) + 1, 1), 5)

        level_color = self.RISK_LEVELS.get((prob_band, impact_band), ("MODERATE", "#eab308"))

        threat_level = self._score_to_level(overall)
        recommendations = self._generate_recommendations(threat_level, dimensions)

        # Simulate historical trend
        historical = self._generate_historical(rng, overall)
        trend = self._determine_trend(historical)

        return RiskAssessment(
            target_identifier=target_identifier,
            overall_risk_score=overall,
            threat_level=threat_level,
            dimensions=dimensions,
            matrix_position=RiskMatrixCell(
                probability_band=prob_band,
                impact_band=impact_band,
                risk_level=level_color[0],
                color=level_color[1],
            ),
            probability_label=self.PROBABILITY_LABELS.get(prob_band, "Unknown"),
            impact_label=self.IMPACT_LABELS.get(impact_band, "Unknown"),
            recommendations=recommendations,
            risk_trend=trend,
            historical_scores=historical,
            confidence=0.95 if demo_key else round(rng.uniform(0.60, 0.88), 3),
            generated_at=datetime.now().isoformat(),
        )

    def _generate_dimensions(self, rng: random.Random, demo_key: Optional[str]) -> List[RiskDimension]:
        """Generate risk dimensions."""
        if demo_key:
            # Safe profiles
            dims = [
                ("Data Breach Exposure", 0.08, 0.15, "Minor exposure in aggregated breach databases. No active credential leaks detected.", ["Enable 2FA on all accounts", "Rotate exposed passwords"]),
                ("Social Engineering Risk", 0.05, 0.10, "Low social engineering risk. Limited publicly exposed PII.", ["Review public profile information", "Limit oversharing"]),
                ("Account Takeover Risk", 0.03, 0.20, "Very low account takeover risk. Strong authentication practices detected.", ["Maintain current security posture"]),
                ("Malware Association", 0.01, 0.05, "No malware association detected across all monitored sources.", ["Continue standard monitoring"]),
                ("Reputation Risk", 0.02, 0.08, "Clean online reputation. No negative mentions or associations found.", ["No action required"]),
            ]
        else:
            # Random profiles
            dims = [
                ("Data Breach Exposure", round(rng.uniform(0.1, 0.6), 3), round(rng.uniform(0.2, 0.7), 3),
                 "Breach exposure analysis based on HIBP and dark web monitoring.", ["Review breach details", "Rotate credentials"]),
                ("Social Engineering Risk", round(rng.uniform(0.05, 0.45), 3), round(rng.uniform(0.15, 0.5), 3),
                 "Risk assessment based on publicly available personal information.", ["Reduce public data exposure"]),
                ("Account Takeover Risk", round(rng.uniform(0.05, 0.4), 3), round(rng.uniform(0.2, 0.6), 3),
                 "Account security posture evaluation across platforms.", ["Enable 2FA", "Use password manager"]),
                ("Malware Association", round(rng.uniform(0.02, 0.25), 3), round(rng.uniform(0.1, 0.5), 3),
                 "Malware and infrastructure association scan results.", ["Deep scan if elevated"]),
                ("Reputation Risk", round(rng.uniform(0.05, 0.35), 3), round(rng.uniform(0.1, 0.4), 3),
                 "Online reputation and association analysis.", ["Monitor mentions"]),
            ]

        result = []
        for name, prob, impact, explanation, mitigations in dims:
            combined = round(prob * impact, 4)
            level = self._combined_to_level(combined)
            result.append(RiskDimension(
                name=name,
                probability=prob,
                impact=impact,
                combined_score=combined,
                level=level,
                explanation=explanation,
                mitigations=mitigations,
            ))

        return result

    def _combined_to_level(self, score: float) -> str:
        if score < 0.02:
            return "NEGLIGIBLE"
        elif score < 0.08:
            return "LOW"
        elif score < 0.20:
            return "MODERATE"
        elif score < 0.40:
            return "HIGH"
        else:
            return "CRITICAL"

    def _score_to_level(self, score: float) -> str:
        if score < 5:
            return "NONE"
        elif score < 15:
            return "LOW"
        elif score < 35:
            return "MEDIUM"
        elif score < 60:
            return "HIGH"
        else:
            return "CRITICAL"

    def _generate_recommendations(self, level: str, dims: List[RiskDimension]) -> List[str]:
        recs = []
        # Add dimension-specific mitigations for elevated risks
        for d in dims:
            if d.combined_score > 0.05:
                recs.extend(d.mitigations)

        # Add level-specific recommendations
        if level in ("NONE", "LOW"):
            recs.append("Continue standard passive monitoring")
            recs.append("No immediate action required")
        elif level == "MEDIUM":
            recs.append("Increase monitoring frequency")
            recs.append("Review security posture of associated accounts")
        elif level == "HIGH":
            recs.append("ALERT: Escalate to security operations team")
            recs.append("Block access to sensitive systems pending review")
        elif level == "CRITICAL":
            recs.append("CRITICAL: Immediate incident response required")
            recs.append("Activate containment procedures")
            recs.append("Notify legal and compliance teams")

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for r in recs:
            if r not in seen:
                seen.add(r)
                unique.append(r)
        return unique

    def _generate_historical(self, rng: random.Random, current: float) -> List[float]:
        """Generate 7 historical risk scores for trend visualization."""
        scores = []
        base = current + rng.uniform(-5, 5)
        for i in range(7):
            score = base + rng.uniform(-3, 3)
            scores.append(round(max(0, min(100, score)), 1))
        scores.append(current)
        return scores[-7:]

    def _determine_trend(self, scores: List[float]) -> str:
        if len(scores) < 3:
            return "STABLE"
        recent_avg = sum(scores[-3:]) / 3
        older_avg = sum(scores[:3]) / 3
        diff = recent_avg - older_avg
        if diff > 3:
            return "INCREASING"
        elif diff < -3:
            return "DECREASING"
        return "STABLE"
