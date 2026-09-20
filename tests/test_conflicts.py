"""
TRACE-X Conflict Detection Tests.

Tests all 5 conflict types: location overlap, timeline inconsistency,
employer mismatch, bio contradiction, and name variance.
"""

from __future__ import annotations

from datetime import date

import pytest

from trace_x.ml.conflicts import (
    detect_bio_contradictions,
    detect_conflicts,
    detect_employer_mismatch,
    detect_location_conflicts,
    detect_name_variance,
    detect_timeline_conflicts,
)
from trace_x.schemas.enums import ConflictType, Severity


# ── Location Conflict Tests ─────────────────────────────────


class TestLocationConflicts:
    """Tests for detect_location_conflicts()."""

    def test_distant_locations_flagged(self):
        """Profiles in distant cities are flagged."""
        profiles = [
            {"profile_id": "p1", "location": "San Francisco"},
            {"profile_id": "p2", "location": "Tokyo"},
        ]
        conflicts = detect_location_conflicts(profiles)
        assert len(conflicts) >= 1
        assert conflicts[0].conflict_type == ConflictType.LOCATION_OVERLAP
        assert conflicts[0].severity == Severity.HIGH

    def test_nearby_locations_ok(self):
        """Profiles in nearby cities are not flagged."""
        profiles = [
            {"profile_id": "p1", "location": "San Francisco"},
            {"profile_id": "p2", "location": "SF"},  # Same city
        ]
        conflicts = detect_location_conflicts(profiles)
        assert len(conflicts) == 0

    def test_unknown_locations_ignored(self):
        """Unknown locations are silently skipped."""
        profiles = [
            {"profile_id": "p1", "location": "Atlantis"},
            {"profile_id": "p2", "location": "Narnia"},
        ]
        conflicts = detect_location_conflicts(profiles)
        assert len(conflicts) == 0

    def test_no_locations(self):
        """Profiles without locations produce no conflicts."""
        profiles = [
            {"profile_id": "p1", "location": None},
            {"profile_id": "p2"},
        ]
        conflicts = detect_location_conflicts(profiles)
        assert len(conflicts) == 0


# ── Timeline Conflict Tests ─────────────────────────────────


class TestTimelineConflicts:
    """Tests for detect_timeline_conflicts()."""

    def test_overlapping_employment_different_orgs(self):
        """Overlapping employment at different orgs is flagged."""
        events = [
            {
                "event_type": "EMPLOYMENT",
                "start_date": date(2020, 1, 1),
                "end_date": None,
                "organization": "CompanyA",
                "candidate_id": "c1",
            },
            {
                "event_type": "EMPLOYMENT",
                "start_date": date(2021, 6, 1),
                "end_date": date(2023, 12, 31),
                "organization": "CompanyB",
                "candidate_id": "c1",
            },
        ]
        conflicts = detect_timeline_conflicts(events)
        assert len(conflicts) >= 1
        assert conflicts[0].conflict_type == ConflictType.TIMELINE_INCONSISTENCY

    def test_sequential_employment_ok(self):
        """Non-overlapping employment produces no conflicts."""
        events = [
            {
                "event_type": "EMPLOYMENT",
                "start_date": date(2018, 1, 1),
                "end_date": date(2020, 6, 30),
                "organization": "CompanyA",
                "candidate_id": "c1",
            },
            {
                "event_type": "EMPLOYMENT",
                "start_date": date(2020, 7, 1),
                "end_date": None,
                "organization": "CompanyB",
                "candidate_id": "c1",
            },
        ]
        conflicts = detect_timeline_conflicts(events)
        assert len(conflicts) == 0

    def test_same_org_overlap_ok(self):
        """Overlapping employment at the SAME org is not flagged (promotion)."""
        events = [
            {
                "event_type": "EMPLOYMENT",
                "start_date": date(2020, 1, 1),
                "end_date": None,
                "organization": "TechCorp",
                "candidate_id": "c1",
            },
            {
                "event_type": "EMPLOYMENT",
                "start_date": date(2022, 1, 1),
                "end_date": None,
                "organization": "TechCorp",
                "candidate_id": "c1",
            },
        ]
        conflicts = detect_timeline_conflicts(events)
        assert len(conflicts) == 0  # Same org = likely promotion


# ── Employer Mismatch Tests ─────────────────────────────────


class TestEmployerMismatch:
    """Tests for detect_employer_mismatch()."""

    def test_different_employers_in_bio(self):
        """Profiles claiming different employers are flagged."""
        profiles = [
            {"profile_id": "p1", "bio": "Software Engineer at Google"},
            {"profile_id": "p2", "bio": "Marketing Manager at Amazon"},
        ]
        conflicts = detect_employer_mismatch(profiles)
        assert len(conflicts) >= 1
        assert conflicts[0].conflict_type == ConflictType.EMPLOYER_MISMATCH

    def test_same_employer_ok(self):
        """Profiles at the same employer produce no mismatch."""
        profiles = [
            {"profile_id": "p1", "bio": "Engineer at Google"},
            {"profile_id": "p2", "bio": "Developer at Google"},
        ]
        conflicts = detect_employer_mismatch(profiles)
        assert len(conflicts) == 0

    def test_no_employer_in_bio(self):
        """Profiles without detectable employer are skipped."""
        profiles = [
            {"profile_id": "p1", "bio": "I love coding"},
            {"profile_id": "p2", "bio": "Open source enthusiast"},
        ]
        conflicts = detect_employer_mismatch(profiles)
        assert len(conflicts) == 0


# ── Bio Contradiction Tests ─────────────────────────────────


class TestBioContradictions:
    """Tests for detect_bio_contradictions()."""

    def test_opposite_domains_flagged(self):
        """Completely different expertise domains are flagged."""
        profiles = [
            {"profile_id": "p1", "bio": "AI researcher focusing on reinforcement learning and neural networks"},
            {"profile_id": "p2", "bio": "Professional chef specializing in Italian cuisine and pastry arts"},
        ]
        conflicts = detect_bio_contradictions(profiles, threshold=15.0)
        assert len(conflicts) >= 1
        assert conflicts[0].conflict_type == ConflictType.BIO_CONTRADICTION

    def test_similar_bios_ok(self):
        """Similar bios produce no contradiction."""
        profiles = [
            {"profile_id": "p1", "bio": "Software engineer working on distributed systems"},
            {"profile_id": "p2", "bio": "Senior software engineer building distributed platforms"},
        ]
        conflicts = detect_bio_contradictions(profiles, threshold=15.0)
        assert len(conflicts) == 0


# ── Name Variance Tests ────────────────────────────────────


class TestNameVariance:
    """Tests for detect_name_variance()."""

    def test_drastic_name_difference(self):
        """Very different names are flagged."""
        profiles = [
            {"profile_id": "p1", "display_name": "Alice Johnson"},
            {"profile_id": "p2", "display_name": "Zephyr Moonbeam"},
        ]
        conflicts = detect_name_variance(profiles, threshold=70.0)
        assert len(conflicts) >= 1
        assert conflicts[0].conflict_type == ConflictType.NAME_VARIANCE

    def test_similar_names_ok(self):
        """Similar names produce no variance conflict."""
        profiles = [
            {"profile_id": "p1", "display_name": "Alice Johnson"},
            {"profile_id": "p2", "display_name": "Alice J."},
        ]
        conflicts = detect_name_variance(profiles, threshold=70.0)
        assert len(conflicts) == 0


# ── Full Conflict Orchestrator Tests ────────────────────────


class TestDetectConflicts:
    """Tests for the main detect_conflicts orchestrator."""

    def test_clean_data_no_conflicts(self):
        """Consistent profiles produce no conflicts."""
        profiles = [
            {
                "profile_id": "p1",
                "display_name": "Alice Johnson",
                "bio": "Software engineer at TechCorp",
                "location": "San Francisco",
            },
            {
                "profile_id": "p2",
                "display_name": "Alice Johnson",
                "bio": "Senior software engineer at TechCorp",
                "location": "SF",
            },
        ]
        conflicts = detect_conflicts(profiles, [])
        # Should have no HIGH severity conflicts
        high = [c for c in conflicts if c.severity == Severity.HIGH]
        assert len(high) == 0

    def test_conflicts_sorted_by_severity(self):
        """Conflicts are returned sorted: HIGH first, then MEDIUM, then LOW."""
        profiles = [
            {"profile_id": "p1", "display_name": "Alice", "bio": "AI researcher", "location": "San Francisco"},
            {"profile_id": "p2", "display_name": "Zephyr", "bio": "Chef in Rome", "location": "Tokyo"},
        ]
        conflicts = detect_conflicts(profiles, [])
        if len(conflicts) >= 2:
            severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
            for i in range(len(conflicts) - 1):
                assert (
                    severity_order.get(conflicts[i].severity, 3)
                    <= severity_order.get(conflicts[i + 1].severity, 3)
                )

    def test_every_conflict_has_evidence(self):
        """Every conflict carries an Evidence object."""
        profiles = [
            {"profile_id": "p1", "display_name": "Alice", "location": "San Francisco"},
            {"profile_id": "p2", "display_name": "Bob", "location": "Tokyo"},
        ]
        conflicts = detect_conflicts(profiles, [])
        for conflict in conflicts:
            assert conflict.evidence is not None
            assert conflict.evidence.claim != ""
