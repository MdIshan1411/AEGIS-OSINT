"""
TRACE-X Knowledge Graph Builder.

Builds a NetworkX directed graph from candidate data and exports it as
React Flow JSON. Uses spring_layout(seed=42) for deterministic node
positions across runs. Pure functions — zero I/O.

Node Types & Colors:
- PERSON (blue #3B82F6)
- PROFILE (purple #8B5CF6)
- ORGANIZATION (green #10B981)
- EMPLOYMENT (amber #F59E0B)
- PROJECT (red #EF4444)
- PUBLICATION (cyan #06B6D4)
- EVENT (pink #EC4899)
- CONFLICT (red dashed #DC2626)
"""

from __future__ import annotations

from typing import Any

import networkx as nx

from trace_x.schemas.enums import ConflictType, EventType
from trace_x.schemas.models import (
    Candidate,
    Conflict,
    PlatformProfile,
    TimelineEvent,
)


# ── Node Style Presets ──────────────────────────────────────

NODE_STYLES: dict[str, dict[str, Any]] = {
    "PERSON": {
        "background": "#3B82F6",
        "color": "#FFFFFF",
        "borderRadius": "50%",
        "width": 80,
        "height": 80,
        "fontSize": 12,
        "fontWeight": "bold",
    },
    "PROFILE": {
        "background": "#8B5CF6",
        "color": "#FFFFFF",
        "borderRadius": 8,
        "width": 140,
        "height": 50,
        "fontSize": 11,
    },
    "ORGANIZATION": {
        "background": "#10B981",
        "color": "#FFFFFF",
        "borderRadius": 8,
        "width": 140,
        "height": 50,
        "fontSize": 11,
    },
    "EMPLOYMENT": {
        "background": "#F59E0B",
        "color": "#000000",
        "borderRadius": 8,
        "width": 160,
        "height": 50,
        "fontSize": 11,
    },
    "PROJECT": {
        "background": "#EF4444",
        "color": "#FFFFFF",
        "borderRadius": 8,
        "width": 140,
        "height": 50,
        "fontSize": 11,
    },
    "PUBLICATION": {
        "background": "#06B6D4",
        "color": "#FFFFFF",
        "borderRadius": 8,
        "width": 140,
        "height": 50,
        "fontSize": 11,
    },
    "EVENT": {
        "background": "#EC4899",
        "color": "#FFFFFF",
        "borderRadius": 8,
        "width": 140,
        "height": 50,
        "fontSize": 11,
    },
    "CONFLICT": {
        "background": "#FEE2E2",
        "color": "#DC2626",
        "border": "2px dashed #DC2626",
        "borderRadius": 8,
        "width": 160,
        "height": 60,
        "fontSize": 11,
    },
}

# ── Event Type → Node Type Mapping ──────────────────────────

EVENT_TYPE_TO_NODE: dict[str, str] = {
    EventType.EMPLOYMENT: "EMPLOYMENT",
    EventType.PROJECT: "PROJECT",
    EventType.PUBLICATION: "PUBLICATION",
    EventType.EVENT: "EVENT",
    EventType.CONTRIBUTION: "PROJECT",
}

# ── Event Type → Edge Label Mapping ─────────────────────────

EVENT_TYPE_TO_EDGE: dict[str, str] = {
    EventType.EMPLOYMENT: "WORKS_AT",
    EventType.PROJECT: "CONTRIBUTED_TO",
    EventType.PUBLICATION: "CREATED",
    EventType.EVENT: "ATTENDED",
    EventType.CONTRIBUTION: "CONTRIBUTED_TO",
}


# ── Graph Builder ───────────────────────────────────────────


def build_knowledge_graph(
    candidate: Candidate,
    profiles: list[PlatformProfile],
    timeline_events: list[TimelineEvent],
    conflicts: list[Conflict],
    seed: int = 42,
) -> dict[str, Any]:
    """
    Build a knowledge graph and export as React Flow JSON.

    Algorithm:
    1. Create central PERSON node for the candidate
    2. Add PROFILE nodes for each platform profile + HAS_PROFILE edges
    3. Add timeline event nodes (EMPLOYMENT, PROJECT, etc.) + typed edges
    4. Extract ORGANIZATION nodes from timeline events + WORKS_AT edges
    5. Add CONFLICT nodes (dashed red) + MENTIONS edges
    6. Apply spring_layout(seed=42) for deterministic positions
    7. Scale positions to pixel coordinates for React Flow

    Args:
        candidate: The resolved candidate.
        profiles: Platform profiles associated with this candidate.
        timeline_events: Chronological events.
        conflicts: Detected conflicts.
        seed: Random seed for deterministic layout. Default 42.

    Returns:
        React Flow JSON dict: {"nodes": [...], "edges": [...]}.
    """
    G = nx.DiGraph()

    # ── 1. Central person node ──────────────────────────────
    person_id = f"person_{candidate.candidate_id[:8]}"
    G.add_node(
        person_id,
        label=candidate.name,
        node_type="PERSON",
        data={
            "confidence": candidate.confidence_overall,
            "status": candidate.status,
        },
    )

    # ── 2. Platform profile nodes ───────────────────────────
    for profile in profiles:
        profile_node_id = f"profile_{profile.profile_id[:8]}"
        label = f"{profile.platform.value}\n@{profile.username}"
        G.add_node(
            profile_node_id,
            label=label,
            node_type="PROFILE",
            data={
                "platform": profile.platform.value,
                "username": profile.username,
                "bio": profile.bio,
                "location": profile.location,
                "followers": profile.followers,
            },
        )
        G.add_edge(
            person_id,
            profile_node_id,
            label="HAS_PROFILE",
            data={"platform": profile.platform.value},
        )

    # ── 3. Timeline event nodes ─────────────────────────────
    organizations_seen: set[str] = set()

    for event in timeline_events:
        event_node_id = f"event_{event.event_id[:8]}"
        node_type = EVENT_TYPE_TO_NODE.get(event.event_type, "EVENT")
        edge_label = EVENT_TYPE_TO_EDGE.get(event.event_type, "MENTIONS")

        date_range = ""
        if event.start_date:
            date_range = str(event.start_date)
            if event.end_date:
                date_range += f" – {event.end_date}"
            else:
                date_range += " – Present"

        G.add_node(
            event_node_id,
            label=f"{event.title}\n{date_range}",
            node_type=node_type,
            data={
                "event_type": event.event_type,
                "organization": event.organization,
                "confidence": event.confidence,
            },
        )
        G.add_edge(
            person_id,
            event_node_id,
            label=edge_label,
            data={"event_type": event.event_type},
        )

        # ── 4. Organization nodes ──────────────────────────
        if event.organization and event.organization not in organizations_seen:
            organizations_seen.add(event.organization)
            org_node_id = f"org_{event.organization[:12].lower().replace(' ', '_')}"
            G.add_node(
                org_node_id,
                label=event.organization,
                node_type="ORGANIZATION",
                data={"name": event.organization},
            )
            G.add_edge(
                event_node_id,
                org_node_id,
                label="AT_ORG",
                data={},
            )

    # ── 5. Conflict nodes ──────────────────────────────────
    for conflict in conflicts:
        conflict_node_id = f"conflict_{conflict.conflict_id[:8]}"
        G.add_node(
            conflict_node_id,
            label=f"⚠ {conflict.conflict_type.value}\n{conflict.severity.value}",
            node_type="CONFLICT",
            data={
                "type": conflict.conflict_type.value,
                "severity": conflict.severity.value,
                "description": conflict.description,
            },
        )
        G.add_edge(
            person_id,
            conflict_node_id,
            label="HAS_CONFLICT",
            data={"severity": conflict.severity.value},
        )

    # ── 6. Layout (deterministic) ──────────────────────────
    if len(G.nodes) == 0:
        return {"nodes": [], "edges": []}

    pos = nx.spring_layout(G, seed=seed, k=2.0, iterations=50)

    # Scale to pixel coordinates (center at 400, 300; scale factor 300)
    scale = 300.0
    center_x, center_y = 400.0, 300.0

    # ── 7. Export as React Flow JSON ────────────────────────
    react_nodes: list[dict[str, Any]] = []
    for node_id, attrs in G.nodes(data=True):
        node_type = attrs.get("node_type", "EVENT")
        style = NODE_STYLES.get(node_type, NODE_STYLES["EVENT"]).copy()
        px, py = pos.get(node_id, (0, 0))

        react_nodes.append({
            "id": node_id,
            "data": {
                "label": attrs.get("label", node_id),
                **(attrs.get("data", {})),
            },
            "position": {
                "x": round(center_x + px * scale, 1),
                "y": round(center_y + py * scale, 1),
            },
            "style": style,
            "type": "default",
        })

    react_edges: list[dict[str, Any]] = []
    for i, (source, target, attrs) in enumerate(G.edges(data=True)):
        edge_style: dict[str, Any] = {}
        # Dashed edges for conflicts
        if "conflict" in source or "conflict" in target:
            edge_style = {"strokeDasharray": "5 5", "stroke": "#DC2626"}

        react_edges.append({
            "id": f"edge_{i}",
            "source": source,
            "target": target,
            "label": attrs.get("label", ""),
            "data": attrs.get("data", {}),
            "style": edge_style,
            "animated": "conflict" in source or "conflict" in target,
        })

    return {"nodes": react_nodes, "edges": react_edges}
