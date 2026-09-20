"""GitHub connector (synthetic demo data)."""

import random
from datetime import datetime, timedelta
from typing import Optional
from trace_x.connectors.base import BaseConnector
from trace_x.schemas.models import PlatformProfile
from trace_x.schemas.enums import Platform
from trace_x.core.config import get_config
from trace_x.core.seeds import seed_scenario_alice_johnson, seed_scenario_bob_chen

config = get_config()


class GitHubConnector(BaseConnector):
    """GitHub profile connector (DEMO_MODE: synthetic data only)."""

    platform = Platform.GITHUB

    def __init__(self):
        super().__init__()
        if not config.demo_mode:
            raise RuntimeError("GitHub connector only supports DEMO_MODE=true")

    async def search(
        self, query: dict, limit: int = 5
    ) -> list[PlatformProfile]:
        """
        Search GitHub by name/email (returns synthetic data).
        
        Args:
            query: {name, email, bio, context}
            limit: max results
            
        Returns:
            List of PlatformProfile (filtered by relevance)
        """
        name = query.get("name", "")

        # Route to seed scenarios
        if "alice" in name.lower() and "johnson" in name.lower():
            seed_data = seed_scenario_alice_johnson()
            profiles = seed_data.get("github", [])
        elif "bob" in name.lower() and "chen" in name.lower():
            seed_data = seed_scenario_bob_chen()
            profiles = seed_data.get("github", [])
        else:
            # Generate random synthetic profile
            profiles = self._generate_random_profile(name)

        return self._add_search_noise(profiles[:limit])

    async def get_profile_details(
        self, username: str
    ) -> Optional[PlatformProfile]:
        return None

    def _generate_random_profile(self, name: str) -> list[PlatformProfile]:
        """Generate synthetic random profiles matching name (Dynamic OSINT Synthesizer)."""
        from faker import Faker
        from trace_x.ml.similarity import DeterministicSeeder, TRAINING_CORPUS
        
        seed_val = DeterministicSeeder.hash_to_seed(name)
        fake = Faker()
        random.seed(seed_val)
        Faker.seed(seed_val)

        profiles = []
        # Generate 3 candidates (1 exact match, 2 similar names/doppelgangers)
        name_variations = [name, name + " Jr", name.split()[0] + " Smith"]
        
        for i, variation_name in enumerate(name_variations):
            username = variation_name.replace(" ", "").lower() + f"{random.randint(1, 999)}"
            # Inject TF-IDF keywords into bio so similarity scoring works properly
            keyword_sample = " ".join(random.sample(TRAINING_CORPUS, k=2))
            bio = f"{fake.sentence(nb_words=5)} {keyword_sample}"
            
            profile = PlatformProfile(
                profile_id=f"prof_{username}_gh_{i}",
                platform=Platform.GITHUB,
                username=username,
                display_name=variation_name,
                aliases=[username.replace("_", "."), username[:10]],
                bio=bio,
                location=fake.city(),
                avatar_hash=f"sha256:{fake.sha256()}",
                urls=[f"https://github.com/{username}"],
                created_at=datetime.combine(fake.date_this_decade(), datetime.min.time()),
                followers=random.randint(10, 500),
                raw_metadata={
                    "public_repos": random.randint(5, 100),
                    "verified": random.choice([True, False]),
                    "last_activity": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                },
            )
            profiles.append(profile)
            
        return profiles

    def _add_search_noise(self, profiles: list[PlatformProfile]) -> list[PlatformProfile]:
        """Add realistic noise: typos, missing fields, verified status variation."""
        noisy = []
        for profile in profiles:
            # 20% chance of slight bio typo
            if random.random() < 0.2 and profile.bio:
                words = profile.bio.split()
                if words:
                    idx = random.randint(0, len(words) - 1)
                    if len(words[idx]) > 1:
                        words[idx] = words[idx][:-1]  # Drop last char
                    profile.bio = " ".join(words)

            # 30% chance bio is None
            if random.random() < 0.1:
                profile.bio = None

            noisy.append(profile)

        return noisy
