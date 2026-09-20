"""
TRACE-X Enumerations.

Type-safe string enumerations for all categorical fields across schemas.
Using StrEnum ensures JSON serialization works natively with Pydantic v2.
"""

from __future__ import annotations

from enum import StrEnum


class VerificationMethod(StrEnum):
    """How a claim was verified."""

    EXACT_MATCH = "EXACT_MATCH"
    FUZZY_MATCH = "FUZZY_MATCH"
    TF_IDF_SIMILARITY = "TF_IDF_SIMILARITY"
    CROSS_REFERENCE = "CROSS_REFERENCE"
    PROFILE_TEXT_EXTRACTION = "PROFILE_TEXT_EXTRACTION"


class Platform(StrEnum):
    """Supported social/professional platforms."""

    GITHUB = "github"
    LINKEDIN = "linkedin"
    X = "x"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"


class EventType(StrEnum):
    """Types of timeline events."""

    EMPLOYMENT = "EMPLOYMENT"
    PROJECT = "PROJECT"
    PUBLICATION = "PUBLICATION"
    EVENT = "EVENT"
    CONTRIBUTION = "CONTRIBUTION"


class ConflictType(StrEnum):
    """Types of detected conflicts between profiles."""

    LOCATION_OVERLAP = "LOCATION_OVERLAP"
    TIMELINE_INCONSISTENCY = "TIMELINE_INCONSISTENCY"
    EMPLOYER_MISMATCH = "EMPLOYER_MISMATCH"
    BIO_CONTRADICTION = "BIO_CONTRADICTION"
    NAME_VARIANCE = "NAME_VARIANCE"


class Severity(StrEnum):
    """Conflict severity levels and their confidence penalties."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Resolution(StrEnum):
    """Conflict resolution status."""

    UNRESOLVED = "UNRESOLVED"
    EXPLAINED = "EXPLAINED"
    REJECTED = "REJECTED"


class InvestigationStatus(StrEnum):
    """Lifecycle status of an investigation."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class CandidateStatus(StrEnum):
    """Candidate verification status based on confidence thresholds."""

    VERIFIED = "VERIFIED"          # confidence > 80%
    AMBIGUOUS = "AMBIGUOUS"        # 40% <= confidence <= 80%
    LOW_CONFIDENCE = "LOW_CONFIDENCE"  # confidence < 40%
    CONFLICT = "CONFLICT"          # conflicts detected


# ── Severity → penalty mapping (used by ML engine) ─────────

SEVERITY_PENALTY: dict[Severity, float] = {
    Severity.HIGH: 10.0,
    Severity.MEDIUM: 5.0,
    Severity.LOW: 2.0,
}
