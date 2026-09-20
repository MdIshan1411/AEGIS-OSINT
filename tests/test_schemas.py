"""
TRACE-X Schema Validation Tests.

Tests Pydantic v2 model validation: confidence clamping, email masking,
Evidence validation, Investigation round-trip, and model_dump behavior.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from trace_x.schemas.enums import (
    CandidateStatus,
    InvestigationStatus,
    Platform,
    VerificationMethod,
)
from trace_x.schemas.models import (
    AuditEntry,
    Candidate,
    ConfidenceBreakdown,
    Evidence,
    Investigation,
    InvestigationQuery,
    PlatformProfile,
    hash_email,
    mask_email,
)


# ── Evidence Validation Tests ───────────────────────────────


class TestEvidenceValidation:
    """Tests for Evidence model validation."""

    def test_valid_evidence(self):
        """Valid Evidence creates successfully."""
        ev = Evidence(
            claim="Name matches GitHub profile",
            source_url="https://github.com/alice",
            verification_method=VerificationMethod.FUZZY_MATCH,
            confidence=0.92,
            extracted_text="Alice Johnson — Software Engineer",
        )
        assert ev.claim == "Name matches GitHub profile"
        assert ev.confidence == 0.92

    def test_confidence_range_valid(self):
        """Confidence at boundaries is accepted."""
        ev_low = Evidence(
            claim="Test",
            verification_method=VerificationMethod.EXACT_MATCH,
            confidence=0.0,
        )
        ev_high = Evidence(
            claim="Test",
            verification_method=VerificationMethod.EXACT_MATCH,
            confidence=1.0,
        )
        assert ev_low.confidence == 0.0
        assert ev_high.confidence == 1.0

    def test_confidence_out_of_range(self):
        """Confidence outside [0, 1] raises ValidationError."""
        with pytest.raises(ValidationError):
            Evidence(
                claim="Test",
                verification_method=VerificationMethod.EXACT_MATCH,
                confidence=1.5,
            )
        with pytest.raises(ValidationError):
            Evidence(
                claim="Test",
                verification_method=VerificationMethod.EXACT_MATCH,
                confidence=-0.1,
            )

    def test_empty_claim_rejected(self):
        """Empty claim string is rejected."""
        with pytest.raises(ValidationError):
            Evidence(
                claim="",
                verification_method=VerificationMethod.EXACT_MATCH,
                confidence=0.5,
            )

    def test_timestamp_auto_set(self):
        """Timestamp is auto-populated if not provided."""
        ev = Evidence(
            claim="Test claim",
            verification_method=VerificationMethod.EXACT_MATCH,
            confidence=0.5,
        )
        assert ev.timestamp is not None
        assert isinstance(ev.timestamp, datetime)


# ── Candidate Confidence Clamping Tests ─────────────────────


class TestConfidenceClamping:
    """Tests for confidence clamping on Candidate model."""

    def test_confidence_clamped_at_max(self):
        """Confidence above 99.9 is clamped to 99.9."""
        c = Candidate(
            investigation_id="test",
            name="Test",
            confidence_overall=100.0,
        )
        assert c.confidence_overall == 99.9

    def test_confidence_clamped_at_min(self):
        """Confidence below 0.1 is clamped to 0.1."""
        c = Candidate(
            investigation_id="test",
            name="Test",
            confidence_overall=0.0,
        )
        assert c.confidence_overall == 0.1

    def test_confidence_in_range_unchanged(self):
        """Confidence within (0.1, 99.9) is unchanged."""
        c = Candidate(
            investigation_id="test",
            name="Test",
            confidence_overall=55.5,
        )
        assert c.confidence_overall == 55.5


# ── Email Masking Tests ─────────────────────────────────────


class TestEmailMasking:
    """Tests for email masking and hashing utilities."""

    def test_mask_email_standard(self):
        """Standard email is masked correctly."""
        assert mask_email("alice.johnson@techcorp.com") == "a***@techcorp.com"

    def test_mask_email_short_local(self):
        """Single-character local part is masked."""
        assert mask_email("a@example.com") == "a***@example.com"

    def test_mask_email_no_at(self):
        """String without @ is returned as-is."""
        assert mask_email("not-an-email") == "not-an-email"

    def test_mask_email_empty(self):
        """Empty string is returned as-is."""
        assert mask_email("") == ""

    def test_hash_email_deterministic(self):
        """Email hashing is deterministic."""
        h1 = hash_email("alice@techcorp.com")
        h2 = hash_email("alice@techcorp.com")
        assert h1 == h2

    def test_hash_email_case_insensitive(self):
        """Email hashing is case-insensitive."""
        h1 = hash_email("Alice@TechCorp.com")
        h2 = hash_email("alice@techcorp.com")
        assert h1 == h2


# ── Platform Profile Tests ──────────────────────────────────


class TestPlatformProfile:
    """Tests for PlatformProfile model."""

    def test_valid_profile(self):
        """Valid profile creates successfully."""
        p = PlatformProfile(
            platform=Platform.GITHUB,
            username="alice",
            display_name="Alice Johnson",
            bio="Engineer",
        )
        assert p.platform == Platform.GITHUB
        assert p.profile_id is not None

    def test_empty_username_rejected(self):
        """Empty username is rejected."""
        with pytest.raises(ValidationError):
            PlatformProfile(
                platform=Platform.GITHUB,
                username="",
            )


# ── Investigation Tests ─────────────────────────────────────


class TestInvestigation:
    """Tests for Investigation root aggregate model."""

    def test_valid_investigation(self):
        """Valid Investigation creates successfully."""
        inv = Investigation(
            query=InvestigationQuery(name="Alice Johnson"),
            consent_purpose="Internal security audit",
        )
        assert inv.investigation_id is not None
        assert inv.status == InvestigationStatus.PENDING
        assert inv.consent_purpose == "Internal security audit"
        assert inv.relationship_graph == {"nodes": [], "edges": []}

    def test_consent_purpose_required(self):
        """consent_purpose is required."""
        with pytest.raises(ValidationError):
            Investigation(
                query=InvestigationQuery(name="Alice"),
                consent_purpose="",  # min_length=1
            )

    def test_model_dump_roundtrip(self):
        """Investigation survives model_dump → model_validate roundtrip."""
        inv = Investigation(
            query=InvestigationQuery(name="Test User", email="test@example.com"),
            consent_purpose="Test investigation",
        )
        data = inv.model_dump(mode="json")
        restored = Investigation.model_validate(data)
        assert restored.investigation_id == inv.investigation_id
        assert restored.query.name == "Test User"
        assert restored.consent_purpose == "Test investigation"

    def test_audit_log_appendable(self):
        """Audit log can be appended to."""
        inv = Investigation(
            query=InvestigationQuery(name="Test"),
            consent_purpose="Audit test",
        )
        assert len(inv.audit_log) == 0
        inv.audit_log.append(
            AuditEntry(action="CREATE", actor="test_user")
        )
        assert len(inv.audit_log) == 1
        assert inv.audit_log[0].action == "CREATE"


# ── Confidence Breakdown Tests ──────────────────────────────


class TestConfidenceBreakdown:
    """Tests for ConfidenceBreakdown model."""

    def test_defaults(self):
        """Default breakdown has zero scores."""
        bd = ConfidenceBreakdown()
        assert bd.name_score == 0.0
        assert bd.bio_score == 0.0
        assert bd.prior == 0.3

    def test_score_ranges(self):
        """Scores outside [0, 100] are rejected."""
        with pytest.raises(ValidationError):
            ConfidenceBreakdown(name_score=150.0)
        with pytest.raises(ValidationError):
            ConfidenceBreakdown(bio_score=-10.0)
