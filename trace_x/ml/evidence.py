"""
TRACE-X Evidence Factory.

Pure functions for creating validated Evidence and FeatureContribution
objects. Handles confidence scaling (0-1 ↔ 0-100), timestamp attachment,
and explanation generation. Zero I/O.
"""

from __future__ import annotations

from datetime import datetime, timezone

from trace_x.schemas.enums import VerificationMethod
from trace_x.schemas.models import Evidence, FeatureContribution


# ── Fixed timestamp for determinism in tests ────────────────

_FIXED_TIMESTAMP: datetime | None = None


def set_fixed_timestamp(ts: datetime | None) -> None:
    """
    Set a fixed timestamp for deterministic Evidence creation.

    Pass None to revert to real-time timestamps.
    Used by tests to ensure reproducibility.
    """
    global _FIXED_TIMESTAMP
    _FIXED_TIMESTAMP = ts


def _get_timestamp() -> datetime:
    """Return the current or fixed timestamp."""
    if _FIXED_TIMESTAMP is not None:
        return _FIXED_TIMESTAMP
    return datetime.now(tz=timezone.utc)


# ── Evidence Factory ────────────────────────────────────────


def build_evidence(
    claim: str,
    feature: str,
    raw_value: float,
    source_url: str | None,
    verification_method: str | VerificationMethod,
    extracted_text: str | None = None,
) -> Evidence:
    """
    Create a validated Evidence object.

    Auto-detects whether raw_value is on a 0–1 or 0–100 scale and
    normalizes confidence to 0–1 for storage.

    Args:
        claim: What is being claimed (e.g., "Name matches GitHub profile").
        feature: Feature name (e.g., "name_match", "bio_similarity").
        raw_value: Raw score. If > 1.0, treated as 0–100 scale.
        source_url: Where the claim originated (URL or None).
        verification_method: How the claim was verified.
        extracted_text: Raw data supporting the claim.

    Returns:
        Validated Evidence object.

    Examples:
        >>> e = build_evidence(
        ...     claim="Name 'Alice' matches profile",
        ...     feature="name_match",
        ...     raw_value=95.5,
        ...     source_url="https://github.com/alice",
        ...     verification_method="FUZZY_MATCH",
        ... )
        >>> e.confidence
        0.955
    """
    # Normalize confidence to 0–1 scale
    if raw_value > 1.0:
        confidence = raw_value / 100.0
    else:
        confidence = raw_value

    # Clamp to valid range
    confidence = max(0.0, min(1.0, confidence))

    # Ensure verification_method is the enum type
    if isinstance(verification_method, str):
        verification_method = VerificationMethod(verification_method)

    return Evidence(
        claim=claim,
        source_url=source_url,
        verification_method=verification_method,
        confidence=confidence,
        extracted_text=extracted_text,
        timestamp=_get_timestamp(),
    )


# ── Feature Contribution Factory ────────────────────────────


def build_feature_contribution(
    feature: str,
    raw_value: float,
    weight: float,
    likelihood_ratio: float,
    log_odds_delta: float,
    explanation: str,
) -> FeatureContribution:
    """
    Create a FeatureContribution for the explainability breakdown.

    Args:
        feature: Feature name (e.g., "name_match").
        raw_value: Raw score (0–100).
        weight: Weight applied to this feature.
        likelihood_ratio: P(data|same) / P(data|different).
        log_odds_delta: Contribution to the log-odds accumulation.
        explanation: Human-readable explanation.

    Returns:
        Validated FeatureContribution object.
    """
    return FeatureContribution(
        feature=feature,
        raw_value=raw_value,
        weight=weight,
        weighted_value=raw_value * weight,
        likelihood_ratio=likelihood_ratio,
        log_odds_delta=log_odds_delta,
        explanation=explanation,
    )
