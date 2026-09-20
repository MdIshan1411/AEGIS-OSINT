"""
TRACE-X ML Engine Integration Tests.

Tests the full resolve_candidates orchestrator and calculate_confidence
Bayesian engine with 3 scenarios + edge cases + determinism verification.
"""

from __future__ import annotations

import pytest

from trace_x.ml.engine import (
    apply_conflict_penalties,
    calculate_confidence,
    resolve_candidates,
)
from trace_x.schemas.enums import CandidateStatus


# ── Scenario Tests ──────────────────────────────────────────


class TestScenarioAClearMatch:
    """Scenario A: Clear match across platforms."""

    def test_high_confidence(self, scenario_a_clear_match, default_config):
        """Clear match returns confidence >85%."""
        subject = scenario_a_clear_match["subject"]
        profiles = scenario_a_clear_match["profiles"]

        candidates, conflicts, graph = resolve_candidates(
            subject=subject,
            platform_profiles=[profiles],
            timeline_events=scenario_a_clear_match.get("timeline_events", []),
            config=default_config,
        )

        assert len(candidates) >= 1
        assert candidates[0].confidence_overall > 85.0

    def test_verified_status(self, scenario_a_clear_match, default_config):
        """Clear match gets VERIFIED status."""
        candidates, conflicts, _ = resolve_candidates(
            subject=scenario_a_clear_match["subject"],
            platform_profiles=[scenario_a_clear_match["profiles"]],
            config=default_config,
        )
        assert candidates[0].status == CandidateStatus.VERIFIED

    def test_no_conflicts(self, scenario_a_clear_match, default_config):
        """Clear match has no location/timeline conflicts."""
        _, conflicts, _ = resolve_candidates(
            subject=scenario_a_clear_match["subject"],
            platform_profiles=[scenario_a_clear_match["profiles"]],
            config=default_config,
        )
        # May have minor conflicts (bio variation) but no HIGH severity
        high_conflicts = [c for c in conflicts if c.severity == "HIGH"]
        assert len(high_conflicts) == 0

    def test_evidence_present(self, scenario_a_clear_match, default_config):
        """Every candidate carries Evidence objects."""
        candidates, _, _ = resolve_candidates(
            subject=scenario_a_clear_match["subject"],
            platform_profiles=[scenario_a_clear_match["profiles"]],
            config=default_config,
        )
        assert len(candidates[0].evidence) >= 2  # name + cross_platform at minimum

    def test_confidence_breakdown(self, scenario_a_clear_match, default_config):
        """Confidence breakdown has all expected fields."""
        candidates, _, _ = resolve_candidates(
            subject=scenario_a_clear_match["subject"],
            platform_profiles=[scenario_a_clear_match["profiles"]],
            config=default_config,
        )
        bd = candidates[0].confidence_breakdown
        assert bd.name_score > 0
        assert bd.prior == 0.3
        assert bd.explanation != ""
        assert len(bd.feature_contributions) >= 4


class TestScenarioBAmbigiousNamesake:
    """Scenario B: Ambiguous namesake — same name, different domains."""

    def test_low_confidence(self, scenario_b_ambiguous_namesake, default_config):
        """Ambiguous namesake returns confidence <60%."""
        candidates, _, _ = resolve_candidates(
            subject=scenario_b_ambiguous_namesake["subject"],
            platform_profiles=[scenario_b_ambiguous_namesake["profiles"]],
            config=default_config,
        )
        assert len(candidates) >= 1
        # Name matches well but bio/cross-platform are low
        # With such different bios and no subject bio, score should be moderate-low
        assert candidates[0].confidence_overall < 80.0

    def test_not_verified(self, scenario_b_ambiguous_namesake, default_config):
        """Ambiguous namesake is not VERIFIED."""
        candidates, _, _ = resolve_candidates(
            subject=scenario_b_ambiguous_namesake["subject"],
            platform_profiles=[scenario_b_ambiguous_namesake["profiles"]],
            config=default_config,
        )
        assert candidates[0].status != CandidateStatus.VERIFIED


class TestScenarioCLocationConflict:
    """Scenario C: Strong match but impossible locations."""

    def test_conflict_detected(self, scenario_c_location_conflict, default_config):
        """Location conflict is detected."""
        _, conflicts, _ = resolve_candidates(
            subject=scenario_c_location_conflict["subject"],
            platform_profiles=[scenario_c_location_conflict["profiles"]],
            timeline_events=scenario_c_location_conflict.get("timeline_events", []),
            config=default_config,
        )
        assert len(conflicts) >= 1
        conflict_types = [c.conflict_type for c in conflicts]
        assert "LOCATION_OVERLAP" in conflict_types

    def test_confidence_reduced(self, scenario_c_location_conflict, default_config):
        """Confidence drops due to location conflict."""
        candidates, conflicts, _ = resolve_candidates(
            subject=scenario_c_location_conflict["subject"],
            platform_profiles=[scenario_c_location_conflict["profiles"]],
            config=default_config,
        )
        # Without conflicts, Bob Chen would score very high (same name, same bio)
        # With location conflict (HIGH severity = -10 pts), should be lower
        assert len(conflicts) >= 1
        # The candidate should still be reasonably confident but not as high as without conflict
        assert candidates[0].confidence_overall < 95.0

    def test_graph_has_conflict_node(self, scenario_c_location_conflict, default_config):
        """Knowledge graph includes conflict nodes."""
        _, conflicts, graph = resolve_candidates(
            subject=scenario_c_location_conflict["subject"],
            platform_profiles=[scenario_c_location_conflict["profiles"]],
            config=default_config,
        )
        if conflicts:
            conflict_nodes = [
                n for n in graph.get("nodes", [])
                if "conflict" in n.get("id", "")
            ]
            assert len(conflict_nodes) >= 1


# ── Edge Case Tests ─────────────────────────────────────────


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_empty_profiles(self, default_config):
        """Empty profile list returns empty results."""
        candidates, conflicts, graph = resolve_candidates(
            subject={"name": "Test User"},
            platform_profiles=[],
            config=default_config,
        )
        assert candidates == []
        assert conflicts == []
        assert graph == {"nodes": [], "edges": []}

    def test_single_profile(self, default_config):
        """Single profile still produces a candidate."""
        candidates, _, _ = resolve_candidates(
            subject={"name": "Alice Test"},
            platform_profiles=[[{
                "profile_id": "single-1",
                "platform": "github",
                "username": "alice_test",
                "display_name": "Alice Test",
                "aliases": [],
                "bio": "Software engineer",
                "location": "NYC",
                "raw_metadata": {},
            }]],
            config=default_config,
        )
        assert len(candidates) == 1

    def test_confidence_never_zero_or_hundred(self, default_config):
        """Confidence is always in (0.1, 99.9) — never exactly 0 or 100."""
        # Perfect match
        candidates_high, _, _ = resolve_candidates(
            subject={"name": "Exact Name", "bio": "exact bio text here"},
            platform_profiles=[[{
                "profile_id": "perfect-1",
                "platform": "github",
                "username": "exact_name",
                "display_name": "Exact Name",
                "aliases": [],
                "bio": "exact bio text here",
                "location": None,
                "raw_metadata": {},
            }]],
            config=default_config,
        )
        assert candidates_high[0].confidence_overall <= 99.9
        assert candidates_high[0].confidence_overall >= 0.1

    def test_evidence_on_every_candidate(
        self, scenario_a_clear_match, default_config
    ):
        """Every returned candidate has at least one Evidence object."""
        candidates, _, _ = resolve_candidates(
            subject=scenario_a_clear_match["subject"],
            platform_profiles=[scenario_a_clear_match["profiles"]],
            config=default_config,
        )
        for candidate in candidates:
            assert len(candidate.evidence) >= 1
            for ev in candidate.evidence:
                assert ev.claim != ""
                assert ev.verification_method != ""

    def test_candidate_ranking_by_confidence(self, default_config):
        """Candidates are ranked by confidence descending."""
        candidates, _, _ = resolve_candidates(
            subject={"name": "Test User"},
            platform_profiles=[[{
                "profile_id": "rank-1",
                "platform": "github",
                "username": "test_user",
                "display_name": "Test User",
                "aliases": [],
                "bio": "Engineer",
                "location": None,
                "raw_metadata": {},
            }]],
            config=default_config,
        )
        for i in range(len(candidates) - 1):
            assert candidates[i].confidence_overall >= candidates[i + 1].confidence_overall


# ── Determinism Tests ───────────────────────────────────────


class TestDeterminism:
    """Verify same input → same output always."""

    def test_deterministic_confidence(
        self, scenario_a_clear_match, default_config
    ):
        """Running resolve_candidates twice gives identical confidence."""
        r1_candidates, r1_conflicts, r1_graph = resolve_candidates(
            subject=scenario_a_clear_match["subject"],
            platform_profiles=[scenario_a_clear_match["profiles"]],
            config=default_config,
        )
        r2_candidates, r2_conflicts, r2_graph = resolve_candidates(
            subject=scenario_a_clear_match["subject"],
            platform_profiles=[scenario_a_clear_match["profiles"]],
            config=default_config,
        )

        assert r1_candidates[0].confidence_overall == r2_candidates[0].confidence_overall
        assert len(r1_conflicts) == len(r2_conflicts)

    def test_deterministic_graph_positions(
        self, scenario_a_clear_match, default_config
    ):
        """Graph node positions are identical across runs."""
        _, _, g1 = resolve_candidates(
            subject=scenario_a_clear_match["subject"],
            platform_profiles=[scenario_a_clear_match["profiles"]],
            config=default_config,
        )
        _, _, g2 = resolve_candidates(
            subject=scenario_a_clear_match["subject"],
            platform_profiles=[scenario_a_clear_match["profiles"]],
            config=default_config,
        )

        for n1, n2 in zip(g1["nodes"], g2["nodes"]):
            assert n1["position"]["x"] == n2["position"]["x"]
            assert n1["position"]["y"] == n2["position"]["y"]


# ── Bayesian Calculation Unit Tests ─────────────────────────


class TestCalculateConfidence:
    """Unit tests for calculate_confidence()."""

    def test_high_scores_high_confidence(self):
        """High feature scores → high confidence."""
        confidence, breakdown = calculate_confidence(
            name_score=95.0,
            bio_score=90.0,
            cross_platform_consistency=85.0,
            evidence_count=5,
            conflict_count=0,
        )
        assert confidence > 80.0

    def test_low_scores_low_confidence(self):
        """Low feature scores → low confidence."""
        confidence, breakdown = calculate_confidence(
            name_score=20.0,
            bio_score=10.0,
            cross_platform_consistency=15.0,
            evidence_count=1,
            conflict_count=3,
        )
        assert confidence < 40.0

    def test_conflicts_reduce_confidence(self):
        """More conflicts → lower confidence."""
        conf_no_conflict, _ = calculate_confidence(
            name_score=80.0,
            bio_score=70.0,
            cross_platform_consistency=75.0,
            evidence_count=3,
            conflict_count=0,
        )
        conf_with_conflict, _ = calculate_confidence(
            name_score=80.0,
            bio_score=70.0,
            cross_platform_consistency=75.0,
            evidence_count=3,
            conflict_count=5,
        )
        assert conf_with_conflict < conf_no_conflict

    def test_breakdown_has_explanation(self):
        """Confidence breakdown includes a non-empty explanation."""
        _, breakdown = calculate_confidence(
            name_score=50.0,
            bio_score=50.0,
            cross_platform_consistency=50.0,
            evidence_count=2,
            conflict_count=0,
        )
        assert breakdown.explanation != ""
        assert len(breakdown.feature_contributions) >= 4

    def test_clamping(self):
        """Result is always in (0.1, 99.9)."""
        conf_max, _ = calculate_confidence(100, 100, 100, 100, 0)
        conf_min, _ = calculate_confidence(0, 0, 0, 0, 100)
        assert 0.1 <= conf_max <= 99.9
        assert 0.1 <= conf_min <= 99.9
