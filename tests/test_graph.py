"""
TRACE-X Knowledge Graph Tests.

Tests graph structure, React Flow JSON format, deterministic positions,
and node/edge type correctness.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from trace_x.ml.graph import build_knowledge_graph
from trace_x.schemas.enums import (
    CandidateStatus,
    ConflictType,
    EventType,
    Platform,
    Severity,
    VerificationMethod,
)
from trace_x.schemas.models import (
    Candidate,
    ConfidenceBreakdown,
    Conflict,
    Evidence,
    PlatformProfile,
    TimelineEvent,
)


# ── Fixtures ────────────────────────────────────────────────


@pytest.fixture
def sample_candidate():
    """A sample candidate for graph tests."""
    return Candidate(
        candidate_id="cand-graph-001",
        investigation_id="inv-graph-001",
        rank=1,
        confidence_overall=88.5,
        name="Alice Johnson",
        bio="Software Engineer",
        status=CandidateStatus.VERIFIED,
    )


@pytest.fixture
def sample_profiles():
    """Sample platform profiles for graph tests."""
    return [
        PlatformProfile(
            profile_id="prof-gh-001",
            platform=Platform.GITHUB,
            username="alice_johnson",
            display_name="Alice Johnson",
            bio="Engineer & OSS contributor",
            location="San Francisco",
        ),
        PlatformProfile(
            profile_id="prof-li-001",
            platform=Platform.LINKEDIN,
            username="alice-johnson-sf",
            display_name="Alice Johnson",
            bio="Senior Engineer at TechCorp",
        ),
    ]


@pytest.fixture
def sample_timeline():
    """Sample timeline events for graph tests."""
    return [
        TimelineEvent(
            event_id="evt-gh-001",
            candidate_id="cand-graph-001",
            investigation_id="inv-graph-001",
            event_type=EventType.EMPLOYMENT,
            title="Senior Engineer at TechCorp",
            start_date=date(2020, 6, 1),
            organization="TechCorp",
            confidence=90.0,
        ),
        TimelineEvent(
            event_id="evt-gh-002",
            candidate_id="cand-graph-001",
            investigation_id="inv-graph-001",
            event_type=EventType.PROJECT,
            title="Open Source CLI Tool",
            start_date=date(2021, 3, 1),
            confidence=75.0,
        ),
    ]


@pytest.fixture
def sample_conflicts():
    """Sample conflicts for graph tests."""
    return [
        Conflict(
            conflict_id="conf-001",
            conflict_type=ConflictType.LOCATION_OVERLAP,
            description="SF and Tokyo simultaneously",
            profiles_involved=["prof-gh-001", "prof-li-001"],
            severity=Severity.HIGH,
            evidence=Evidence(
                claim="Location overlap detected",
                verification_method=VerificationMethod.CROSS_REFERENCE,
                confidence=0.9,
            ),
        ),
    ]


# ── Graph Structure Tests ──────────────────────────────────


class TestGraphStructure:
    """Tests for knowledge graph structure."""

    def test_nodes_and_edges_present(
        self, sample_candidate, sample_profiles, sample_timeline, sample_conflicts
    ):
        """Graph has nodes and edges."""
        graph = build_knowledge_graph(
            sample_candidate, sample_profiles, sample_timeline, sample_conflicts
        )
        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) > 0
        assert len(graph["edges"]) > 0

    def test_person_node_exists(
        self, sample_candidate, sample_profiles, sample_timeline, sample_conflicts
    ):
        """Graph has a central PERSON node."""
        graph = build_knowledge_graph(
            sample_candidate, sample_profiles, sample_timeline, sample_conflicts
        )
        person_nodes = [n for n in graph["nodes"] if "person" in n["id"]]
        assert len(person_nodes) == 1
        assert sample_candidate.name in person_nodes[0]["data"]["label"]

    def test_profile_nodes(
        self, sample_candidate, sample_profiles, sample_timeline, sample_conflicts
    ):
        """Graph has a node for each platform profile."""
        graph = build_knowledge_graph(
            sample_candidate, sample_profiles, sample_timeline, sample_conflicts
        )
        profile_nodes = [n for n in graph["nodes"] if "profile" in n["id"]]
        assert len(profile_nodes) == len(sample_profiles)

    def test_conflict_nodes(
        self, sample_candidate, sample_profiles, sample_timeline, sample_conflicts
    ):
        """Graph has conflict nodes for each conflict."""
        graph = build_knowledge_graph(
            sample_candidate, sample_profiles, sample_timeline, sample_conflicts
        )
        conflict_nodes = [n for n in graph["nodes"] if "conflict" in n["id"]]
        assert len(conflict_nodes) == len(sample_conflicts)

    def test_organization_nodes(
        self, sample_candidate, sample_profiles, sample_timeline, sample_conflicts
    ):
        """Graph infers organization nodes from timeline events."""
        graph = build_knowledge_graph(
            sample_candidate, sample_profiles, sample_timeline, sample_conflicts
        )
        org_nodes = [n for n in graph["nodes"] if "org" in n["id"]]
        assert len(org_nodes) >= 1  # TechCorp

    def test_empty_inputs(self, sample_candidate):
        """Empty profiles/events/conflicts produce minimal graph."""
        graph = build_knowledge_graph(sample_candidate, [], [], [])
        assert len(graph["nodes"]) == 1  # Just the person node
        assert len(graph["edges"]) == 0


# ── React Flow Format Tests ─────────────────────────────────


class TestReactFlowFormat:
    """Tests for React Flow JSON compliance."""

    def test_node_structure(
        self, sample_candidate, sample_profiles, sample_timeline, sample_conflicts
    ):
        """Each node has required React Flow fields."""
        graph = build_knowledge_graph(
            sample_candidate, sample_profiles, sample_timeline, sample_conflicts
        )
        for node in graph["nodes"]:
            assert "id" in node
            assert "data" in node
            assert "label" in node["data"]
            assert "position" in node
            assert "x" in node["position"]
            assert "y" in node["position"]
            assert "style" in node

    def test_edge_structure(
        self, sample_candidate, sample_profiles, sample_timeline, sample_conflicts
    ):
        """Each edge has required React Flow fields."""
        graph = build_knowledge_graph(
            sample_candidate, sample_profiles, sample_timeline, sample_conflicts
        )
        for edge in graph["edges"]:
            assert "id" in edge
            assert "source" in edge
            assert "target" in edge
            assert "label" in edge

    def test_positions_are_numeric(
        self, sample_candidate, sample_profiles, sample_timeline, sample_conflicts
    ):
        """Node positions are numeric values."""
        graph = build_knowledge_graph(
            sample_candidate, sample_profiles, sample_timeline, sample_conflicts
        )
        for node in graph["nodes"]:
            assert isinstance(node["position"]["x"], (int, float))
            assert isinstance(node["position"]["y"], (int, float))


# ── Determinism Tests ───────────────────────────────────────


class TestGraphDeterminism:
    """Tests for layout determinism."""

    def test_same_positions_across_runs(
        self, sample_candidate, sample_profiles, sample_timeline, sample_conflicts
    ):
        """Same seed produces identical positions."""
        g1 = build_knowledge_graph(
            sample_candidate, sample_profiles, sample_timeline, sample_conflicts, seed=42
        )
        g2 = build_knowledge_graph(
            sample_candidate, sample_profiles, sample_timeline, sample_conflicts, seed=42
        )

        for n1, n2 in zip(g1["nodes"], g2["nodes"]):
            assert n1["id"] == n2["id"]
            assert n1["position"]["x"] == n2["position"]["x"]
            assert n1["position"]["y"] == n2["position"]["y"]

    def test_different_seeds_different_positions(
        self, sample_candidate, sample_profiles, sample_timeline, sample_conflicts
    ):
        """Different seeds produce different positions."""
        g1 = build_knowledge_graph(
            sample_candidate, sample_profiles, sample_timeline, sample_conflicts, seed=42
        )
        g2 = build_knowledge_graph(
            sample_candidate, sample_profiles, sample_timeline, sample_conflicts, seed=99
        )

        # At least some positions should differ
        any_diff = any(
            n1["position"]["x"] != n2["position"]["x"]
            or n1["position"]["y"] != n2["position"]["y"]
            for n1, n2 in zip(g1["nodes"], g2["nodes"])
        )
        assert any_diff
