"""
Deterministic synthetic data seeds for reproducible demo scenarios.
Each scenario returns profiles with realistic noise and intentional edge cases.
"""

import random
from datetime import datetime, timedelta
from typing import Any
from trace_x.schemas.models import PlatformProfile
from trace_x.schemas.enums import Platform
from faker import Faker


def seed_scenario_alice_johnson() -> dict[str, list[PlatformProfile]]:
    """
    Scenario A: Clear match across GitHub/LinkedIn/X
    - Same person, overlapping bios, consistent timeline
    - Expected: confidence >85%, status VERIFIED
    """
    fake = Faker()
    random.seed(42)  # Deterministic
    Faker.seed(42)

    base_name = "Alice Johnson"
    base_bio_fragment = "Full-stack engineer"
    
    github_profile = PlatformProfile(
        profile_id="prof_alice_gh_001",
        platform=Platform.GITHUB,
        username="alice_johnson",
        display_name="Alice Johnson",
        aliases=["alice.johnson", "ajohnson"],
        bio="Full-stack engineer | Python | React | Open source",
        location="San Francisco, CA",
        avatar_hash="sha256:alice_avatar_hash_001",
        urls=["https://alice-johnson.dev", "https://github.com/alice_johnson"],
        created_at=datetime(2018, 3, 15),
        followers=342,
        raw_metadata={
            "public_repos": 87,
            "verified": True,
            "company": "TechCorp",
            "last_activity": (datetime.now() - timedelta(hours=2)).isoformat(),
        },
    )

    linkedin_profile = PlatformProfile(
        profile_id="prof_alice_li_001",
        platform=Platform.LINKEDIN,
        username="alice-johnson-tech",
        display_name="Alice Johnson",
        aliases=["alice.johnson@techcorp.com"],
        bio="Full-stack engineer at TechCorp | Mentor | Speaker",
        location="San Francisco Bay Area",
        avatar_hash="sha256:alice_avatar_hash_001",  # Same hash = same person
        urls=["https://linkedin.com/in/alice-johnson-tech"],
        created_at=datetime(2015, 6, 1),
        followers=1250,
        raw_metadata={
            "current_role": "Senior Software Engineer",
            "company": "TechCorp",
            "education": "UC Berkeley (CS)",
            "verified": True,
        },
    )

    x_profile = PlatformProfile(
        profile_id="prof_alice_x_001",
        platform=Platform.X,
        username="alice_johnson",
        display_name="Alice Johnson",
        aliases=["@alice_johnson"],
        bio="Engineer, open source, tech talks | she/her",
        location="SF",
        avatar_hash="sha256:alice_avatar_hash_001",
        urls=["https://twitter.com/alice_johnson"],
        created_at=datetime(2016, 11, 20),
        followers=5840,
        raw_metadata={
            "verified": True,
            "followers_count": 5840,
            "created_at": "Sat Nov 20 00:00:00 +0000 2016",
        },
    )

    return {
        "github": [github_profile],
        "linkedin": [linkedin_profile],
        "x": [x_profile],
        "instagram": [],
    }


def seed_scenario_john_smith() -> dict[str, list[PlatformProfile]]:
    """
    Scenario B: Ambiguous namesake (low confidence)
    - Same name, different bios (AI researcher vs. fitness coach), no overlap
    - Expected: confidence <40%, status LOW_CONFIDENCE
    """
    random.seed(43)
    Faker.seed(43)

    github_profile = PlatformProfile(
        profile_id="prof_john_smith_gh_001",
        platform=Platform.GITHUB,
        username="john_smith_ai",
        display_name="John Smith",
        aliases=["jsmith_ai", "j.smith"],
        bio="AI researcher | ML engineer | Deep learning enthusiast",
        location="Boston, MA",
        avatar_hash="sha256:john_smith_ai_hash",
        urls=["https://github.com/john_smith_ai"],
        created_at=datetime(2017, 8, 12),
        followers=156,
        raw_metadata={
            "public_repos": 42,
            "company": "AILabs",
            "last_activity": (datetime.now() - timedelta(hours=5)).isoformat(),
        },
    )

    linkedin_profile = PlatformProfile(
        profile_id="prof_john_smith_li_001",
        platform=Platform.LINKEDIN,
        username="john-smith-marketing",
        display_name="John Smith",
        aliases=["john.smith@startup.com"],
        bio="Marketing Manager at StartupX | Growth Hacker | SaaS",
        location="Austin, TX",
        avatar_hash="sha256:john_smith_marketing_hash",  # Different hash
        urls=["https://linkedin.com/in/john-smith-marketing"],
        created_at=datetime(2014, 2, 5),
        followers=487,
        raw_metadata={
            "current_role": "Marketing Manager",
            "company": "StartupX",
            "education": "University of Texas (Business)",
        },
    )

    x_profile = PlatformProfile(
        profile_id="prof_john_smith_x_001",
        platform=Platform.X,
        username="j_smith_fitness",
        display_name="J. Smith",
        aliases=["jsmith88"],
        bio="Fitness coach | Nutrition | Wellness lifestyle 💪",
        location="Denver, CO",
        avatar_hash="sha256:john_smith_fitness_hash",  # Different again
        urls=["https://twitter.com/j_smith_fitness"],
        created_at=datetime(2019, 5, 10),
        followers=3210,
        raw_metadata={
            "verified": False,
            "followers_count": 3210,
        },
    )

    return {
        "github": [github_profile],
        "linkedin": [linkedin_profile],
        "x": [x_profile],
        "instagram": [],
    }


def seed_scenario_bob_chen() -> dict[str, list[PlatformProfile]]:
    """
    Scenario C: Location conflict (impossible travel)
    - Strong name/bio match but claimed to be in 2 places simultaneously
    - Expected: conflict flagged, confidence drops >15 points
    """
    random.seed(44)
    Faker.seed(44)

    github_profile = PlatformProfile(
        profile_id="prof_bob_chen_gh_001",
        platform=Platform.GITHUB,
        username="bob_chen_ml",
        display_name="Bob Chen",
        aliases=["bobchen", "b.chen"],
        bio="ML engineer at BigTech | Computer Vision | PyTorch",
        location="San Francisco, CA",
        avatar_hash="sha256:bob_chen_hash",
        urls=["https://github.com/bob_chen_ml"],
        created_at=datetime(2019, 3, 22),
        followers=289,
        raw_metadata={
            "public_repos": 64,
            "company": "BigTech",
            "last_activity": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
    )

    linkedin_profile = PlatformProfile(
        profile_id="prof_bob_chen_li_001",
        platform=Platform.LINKEDIN,
        username="bob-chen-ml",
        display_name="Bob Chen",
        aliases=["bob.chen@bigtech.com"],
        bio="ML Engineer at BigTech | Computer Vision | NLP",
        location="San Francisco Bay Area",
        avatar_hash="sha256:bob_chen_hash",  # Same hash
        urls=["https://linkedin.com/in/bob-chen-ml"],
        created_at=datetime(2019, 1, 15),
        followers=892,
        raw_metadata={
            "current_role": "Senior ML Engineer",
            "company": "BigTech",
            "education": "Stanford (MS CS)",
            "start_date": "2019-03-01",
        },
    )

    # X profile with CONFLICTING location (posted from Tokyo same day as SF event)
    x_profile = PlatformProfile(
        profile_id="prof_bob_chen_x_001",
        platform=Platform.X,
        username="bob_chen_ai",
        display_name="Bob Chen",
        aliases=["@bob_chen_ai"],
        bio="ML engineer, AI researcher | Tweets from around the world 🌍",
        location="Tokyo, Japan",  # Conflicting with SF
        avatar_hash="sha256:bob_chen_hash",
        urls=["https://twitter.com/bob_chen_ai"],
        created_at=datetime(2018, 7, 5),
        followers=4120,
        raw_metadata={
            "verified": False,
            "followers_count": 4120,
            "recent_tweet": {
                "text": "Just landed in Tokyo! Excited for the conference 🇯🇵",
                "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
            },
        },
    )

    return {
        "github": [github_profile],
        "linkedin": [linkedin_profile],
        "x": [x_profile],
        "instagram": [],
    }


def generate_random_profiles(subject_name: str) -> dict[str, list[PlatformProfile]]:
    """
    Generate realistic random profiles for unknown subject names.
    Used for testing with arbitrary inputs.
    """
    fake = Faker()
    random.seed(hash(subject_name) % (2**32))  # Deterministic based on name
    Faker.seed(hash(subject_name) % (2**32))

    profiles = {}
    for platform in [Platform.GITHUB, Platform.LINKEDIN, Platform.X]:
        username = subject_name.replace(" ", "_").lower() + f"_{random.randint(1, 99)}"
        profile = PlatformProfile(
            profile_id=f"prof_{username}_{platform.value}_001",
            platform=platform,
            username=username,
            display_name=subject_name,
            aliases=[username.replace("_", "."), username[:10]],
            bio=fake.sentence(nb_words=10),
            location=fake.city(),
            avatar_hash=f"sha256:{fake.sha256()}",
            urls=[f"https://{platform.value}.com/{username}"],
            created_at=datetime.combine(fake.date_this_decade(), datetime.min.time()),
            followers=random.randint(50, 5000),
            raw_metadata={},
        )
        profiles[platform.value] = [profile]

    return profiles


def get_seed_by_name(subject_name: str) -> dict[str, list[PlatformProfile]]:
    """
    Route to appropriate seed based on subject name.
    Falls back to generating random data for unknown subjects.
    """
    if "alice" in subject_name.lower() and "johnson" in subject_name.lower():
        return seed_scenario_alice_johnson()
    elif "john" in subject_name.lower() and "smith" in subject_name.lower():
        return seed_scenario_john_smith()
    elif "bob" in subject_name.lower() and "chen" in subject_name.lower():
        return seed_scenario_bob_chen()
    else:
        # Generate random profiles (placeholder for unknown subjects)
        return generate_random_profiles(subject_name)
