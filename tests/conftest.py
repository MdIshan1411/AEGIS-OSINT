"""
TRACE-X Test Fixtures.

Three synthetic scenarios with full PlatformProfile data:
- Scenario A: Clear match (Alice Johnson) → expect >85% confidence
- Scenario B: Ambiguous namesake (John Smith) → expect <40% confidence
- Scenario C: Location conflict (Bob Chen) → expect conflict flagged, -15pts

All fixtures produce deterministic data for reproducible test runs.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

from trace_x.schemas.enums import EventType, Platform


# ── Fixed UUIDs for determinism ─────────────────────────────

FIXED_IDS = {
    "alice_gh": "a1111111-1111-1111-1111-111111111111",
    "alice_li": "a2222222-2222-2222-2222-222222222222",
    "alice_x": "a3333333-3333-3333-3333-333333333333",
    "john_gh": "b1111111-1111-1111-1111-111111111111",
    "john_li": "b2222222-2222-2222-2222-222222222222",
    "john_x": "b3333333-3333-3333-3333-333333333333",
    "bob_gh": "c1111111-1111-1111-1111-111111111111",
    "bob_li": "c2222222-2222-2222-2222-222222222222",
    "bob_x": "c3333333-3333-3333-3333-333333333333",
}

FIXED_TS = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


# ── Scenario A: Clear Match ────────────────────────────────


@pytest.fixture
def scenario_a_clear_match():
    """
    Scenario A: Clear match across GitHub, LinkedIn, X.

    Same name, overlapping bios, consistent timeline, same location.
    Expected confidence: >85%.
    """
    return {
        "subject": {
            "name": "Alice Johnson",
            "email": "alice.johnson@techcorp.com",
            "bio": "Senior Software Engineer specializing in distributed systems",
        },
        "profiles": [
            {
                "profile_id": FIXED_IDS["alice_gh"],
                "platform": Platform.GITHUB,
                "username": "alice_johnson",
                "display_name": "Alice Johnson",
                "aliases": ["alicejohnson", "a.johnson"],
                "bio": "Senior Software Engineer | Distributed systems & cloud architecture",
                "location": "San Francisco",
                "avatar_hash": "abc123hash",
                "urls": ["https://github.com/alice_johnson"],
                "created_at": datetime(2018, 3, 15, tzinfo=timezone.utc),
                "followers": 1250,
                "raw_metadata": {"repos": 42, "stars": 890},
            },
            {
                "profile_id": FIXED_IDS["alice_li"],
                "platform": Platform.LINKEDIN,
                "username": "alice-johnson-sf",
                "display_name": "Alice Johnson",
                "aliases": [],
                "bio": "Senior Software Engineer at TechCorp | Ex-Google | Stanford CS",
                "location": "San Francisco Bay Area",
                "avatar_hash": "abc123hash",
                "urls": ["https://linkedin.com/in/alice-johnson-sf"],
                "created_at": datetime(2020, 1, 10, tzinfo=timezone.utc),
                "followers": 3500,
                "raw_metadata": {"connections": 500},
            },
            {
                "profile_id": FIXED_IDS["alice_x"],
                "platform": Platform.X,
                "username": "alice_eng",
                "display_name": "Alice Johnson 🚀",
                "aliases": ["aliceeng"],
                "bio": "Engineer & open source contributor. Building distributed systems at TechCorp.",
                "location": "SF",
                "avatar_hash": "abc123hash",
                "urls": ["https://x.com/alice_eng"],
                "created_at": datetime(2019, 6, 1, tzinfo=timezone.utc),
                "followers": 8900,
                "raw_metadata": {},
            },
        ],
        "timeline_events": [
            {
                "event_id": "evt-a1",
                "candidate_id": FIXED_IDS["alice_gh"],
                "investigation_id": "inv-a",
                "event_type": EventType.EMPLOYMENT,
                "title": "Senior Software Engineer at TechCorp",
                "start_date": date(2020, 6, 1),
                "end_date": None,
                "organization": "TechCorp",
                "description": "Building distributed data pipelines",
                "evidence": [],
                "confidence": 90.0,
            },
            {
                "event_id": "evt-a2",
                "candidate_id": FIXED_IDS["alice_gh"],
                "investigation_id": "inv-a",
                "event_type": EventType.EMPLOYMENT,
                "title": "Software Engineer at Google",
                "start_date": date(2018, 8, 1),
                "end_date": date(2020, 5, 31),
                "organization": "Google",
                "description": "Cloud infrastructure team",
                "evidence": [],
                "confidence": 85.0,
            },
        ],
    }


# ── Scenario B: Ambiguous Namesake ──────────────────────────


@pytest.fixture
def scenario_b_ambiguous_namesake():
    """
    Scenario B: Ambiguous namesake — same name, wildly different domains.

    GitHub profile is an AI researcher, LinkedIn is a Marketing Manager,
    X is about fitness. Expected confidence: <40%.
    """
    return {
        "subject": {
            "name": "John Smith",
            "email": None,
            "bio": None,
        },
        "profiles": [
            {
                "profile_id": FIXED_IDS["john_gh"],
                "platform": Platform.GITHUB,
                "username": "john_smith_dev",
                "display_name": "John Smith",
                "aliases": ["jsmith_ai"],
                "bio": "AI researcher focusing on reinforcement learning and neural architecture search",
                "location": "Boston",
                "avatar_hash": "def456hash",
                "urls": ["https://github.com/john_smith_dev"],
                "created_at": datetime(2016, 9, 1, tzinfo=timezone.utc),
                "followers": 340,
                "raw_metadata": {},
            },
            {
                "profile_id": FIXED_IDS["john_li"],
                "platform": Platform.LINKEDIN,
                "username": "john-smith-marketing",
                "display_name": "John Smith",
                "aliases": [],
                "bio": "Marketing Manager at StartupX | Brand Strategy | Growth Hacking",
                "location": "Austin",
                "avatar_hash": "ghi789hash",
                "urls": ["https://linkedin.com/in/john-smith-marketing"],
                "created_at": datetime(2019, 3, 15, tzinfo=timezone.utc),
                "followers": 1200,
                "raw_metadata": {},
            },
            {
                "profile_id": FIXED_IDS["john_x"],
                "platform": Platform.X,
                "username": "j_smith88",
                "display_name": "John S.",
                "aliases": ["jsmith88"],
                "bio": "Fitness & nutrition content 💪 | Personal trainer | Meal prep tips",
                "location": "Miami",
                "avatar_hash": "jkl012hash",
                "urls": ["https://x.com/j_smith88"],
                "created_at": datetime(2020, 1, 1, tzinfo=timezone.utc),
                "followers": 15000,
                "raw_metadata": {},
            },
        ],
        "timeline_events": [],
    }


# ── Scenario C: Location Conflict ──────────────────────────


@pytest.fixture
def scenario_c_location_conflict():
    """
    Scenario C: Strong name/bio match but impossible locations.

    GitHub + LinkedIn both say "Bob Chen, ML Engineer at BigTech, SF",
    but X says "Just landed in Tokyo!" on the same date as an SF event.
    Expected: conflict flagged, confidence drops ≥15 points.
    """
    return {
        "subject": {
            "name": "Bob Chen",
            "email": "bob.chen@bigtech.com",
            "bio": "ML Engineer specializing in deep learning and computer vision",
        },
        "profiles": [
            {
                "profile_id": FIXED_IDS["bob_gh"],
                "platform": Platform.GITHUB,
                "username": "bob_chen",
                "display_name": "Bob Chen",
                "aliases": ["bobchen", "b.chen"],
                "bio": "ML Engineer at BigTech | Deep learning & computer vision",
                "location": "San Francisco",
                "avatar_hash": "mno345hash",
                "urls": ["https://github.com/bob_chen"],
                "created_at": datetime(2019, 1, 15, tzinfo=timezone.utc),
                "followers": 560,
                "raw_metadata": {},
            },
            {
                "profile_id": FIXED_IDS["bob_li"],
                "platform": Platform.LINKEDIN,
                "username": "bob-chen-ml",
                "display_name": "Bob Chen",
                "aliases": [],
                "bio": "ML Engineer at BigTech | Stanford MS CS | Computer Vision",
                "location": "San Francisco, CA",
                "avatar_hash": "mno345hash",
                "urls": ["https://linkedin.com/in/bob-chen-ml"],
                "created_at": datetime(2019, 6, 1, tzinfo=timezone.utc),
                "followers": 2100,
                "raw_metadata": {},
            },
            {
                "profile_id": FIXED_IDS["bob_x"],
                "platform": Platform.X,
                "username": "bob_chen_ml",
                "display_name": "Bob Chen 🤖",
                "aliases": ["bobchenml"],
                "bio": "Just landed in Tokyo! 🇯🇵 ML engineer exploring AI in Asia",
                "location": "Tokyo",
                "avatar_hash": "pqr678hash",
                "urls": ["https://x.com/bob_chen_ml"],
                "created_at": datetime(2019, 2, 1, tzinfo=timezone.utc),
                "followers": 4300,
                "raw_metadata": {},
            },
        ],
        "timeline_events": [
            {
                "event_id": "evt-c1",
                "candidate_id": FIXED_IDS["bob_gh"],
                "investigation_id": "inv-c",
                "event_type": EventType.EMPLOYMENT,
                "title": "ML Engineer at BigTech",
                "start_date": date(2019, 1, 15),
                "end_date": None,
                "organization": "BigTech",
                "description": "Computer vision team",
                "evidence": [],
                "confidence": 88.0,
            },
        ],
    }


# ── Default Config Fixture ──────────────────────────────────


@pytest.fixture
def default_config():
    """Default ML configuration for tests."""
    return {
        "weights": {
            "name": 0.35,
            "bio": 0.25,
            "cross_platform": 0.25,
            "evidence": 0.10,
            "conflict_penalty": 0.05,
        },
        "prior": 0.3,
        "investigation_id": "test-investigation-001",
    }
