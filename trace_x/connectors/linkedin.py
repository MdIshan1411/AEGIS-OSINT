"""LinkedIn connector (synthetic demo data)."""

import random
from datetime import datetime
from typing import Optional
from trace_x.connectors.base import BaseConnector
from trace_x.schemas.models import PlatformProfile
from trace_x.schemas.enums import Platform
from trace_x.core.config import get_config
from trace_x.core.seeds import seed_scenario_alice_johnson, seed_scenario_bob_chen

config = get_config()


class LinkedInConnector(BaseConnector):
    """LinkedIn profile connector (DEMO_MODE: synthetic data only)."""

    platform = Platform.LINKEDIN

    def __init__(self):
        super().__init__()
        if not config.demo_mode:
            raise RuntimeError("LinkedIn connector only supports DEMO_MODE=true")

    async def search(
        self, query: dict, limit: int = 5
    ) -> list[PlatformProfile]:
        """Search LinkedIn by name (returns synthetic data)."""
        name = query.get("name", "")

        if "alice" in name.lower() and "johnson" in name.lower():
            seed_data = seed_scenario_alice_johnson()
            profiles = seed_data.get("linkedin", [])
        elif "bob" in name.lower() and "chen" in name.lower():
            seed_data = seed_scenario_bob_chen()
            profiles = seed_data.get("linkedin", [])
        else:
            profiles = self._generate_random_profile(name)

        return self._add_search_noise(profiles[:limit])

    async def get_profile_details(
        self, username: str
    ) -> Optional[PlatformProfile]:
        return None

    def _generate_random_profile(self, name: str) -> list[PlatformProfile]:
        """Generate synthetic random profiles (Dynamic OSINT Synthesizer)."""
        from faker import Faker
        from trace_x.ml.similarity import DeterministicSeeder, TRAINING_CORPUS
        
        seed_val = DeterministicSeeder.hash_to_seed(name)
        fake = Faker()
        random.seed(seed_val)
        Faker.seed(seed_val)

        profiles = []
        name_variations = [name, name.split()[0] + " " + fake.last_name(), name + " Esq"]
        
        for i, variation_name in enumerate(name_variations):
            username = variation_name.replace(" ", "-").lower() + f"-{random.randint(100, 999)}"
            keyword_sample = " ".join(random.sample(TRAINING_CORPUS, k=2))
            bio = f"{fake.sentence(nb_words=12)} {keyword_sample}"
            
            profile = PlatformProfile(
                profile_id=f"prof_{username}_li_{i}",
                platform=Platform.LINKEDIN,
                username=username,
                display_name=variation_name,
                aliases=[variation_name.replace(" ", ".").lower()],
                bio=bio,
                location=fake.city(),
                avatar_hash=f"sha256:{fake.sha256()}",
                urls=[f"https://linkedin.com/in/{username}"],
                created_at=datetime.combine(fake.date_this_decade(), datetime.min.time()),
                followers=random.randint(100, 2000),
                raw_metadata={
                    "current_role": fake.job(),
                    "company": fake.company(),
                    "education": f"{fake.word()} University",
                },
            )
            profiles.append(profile)
            
        return profiles

    def _add_search_noise(self, profiles: list[PlatformProfile]) -> list[PlatformProfile]:
        """Add realistic LinkedIn noise."""
        noisy = []
        for profile in profiles:
            # Some profiles missing location
            if random.random() < 0.15:
                profile.location = None

            # Some missing bio details
            if random.random() < 0.1:
                profile.bio = None

            noisy.append(profile)

        return noisy
