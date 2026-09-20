import random
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import uuid
from trace_x.ml.similarity import DeterministicSeeder, MLSimilarityEngine
from trace_x.schemas.models import (
    Candidate, ConfidenceBreakdown, PlatformProfile, TimelineEvent,
    Evidence, Conflict, ConflictType
)
import hashlib

class DynamicOSINTGenerator:
    """
    Generates deterministic, complex intelligence dossiers for any input name
    Uses seeding to ensure reproducibility: same name always produces same data
    """

    PLATFORM_DATA = {
        "github": {
            "domain": "github.com",
            "name": "GitHub",
            "type": "developer"
        },
        "linkedin": {
            "domain": "linkedin.com",
            "name": "LinkedIn",
            "type": "professional"
        },
        "twitter": {
            "domain": "twitter.com",
            "name": "Twitter (X)",
            "type": "social"
        },
        "instagram": {
            "domain": "instagram.com",
            "name": "Instagram",
            "type": "social"
        },
        "snapchat": {
            "domain": "snapchat.com",
            "name": "Snapchat",
            "type": "social"
        },
        "reddit": {
            "domain": "reddit.com",
            "name": "Reddit",
            "type": "community"
        },
        "hackernews": {
            "domain": "news.ycombinator.com",
            "name": "Hacker News",
            "type": "tech"
        },
        "kaggle": {
            "domain": "kaggle.com",
            "name": "Kaggle",
            "type": "data_science"
        }
    }

    JOB_TITLES = [
        "Senior Software Engineer", "ML Engineer", "Security Engineer",
        "Full Stack Developer", "Data Scientist", "DevOps Engineer",
        "Tech Lead", "Engineering Manager", "Security Researcher",
        "Startup Founder", "Open Source Contributor"
    ]

    COMPANIES = [
        "Google", "Meta", "Amazon", "Microsoft", "Apple", "Tesla",
        "OpenAI", "Anthropic", "Stripe", "Figma", "Notion", "Canva",
        "Y Combinator", "GitHub", "GitLab", "HashiCorp"
    ]

    CITIES = [
        "San Francisco", "New York", "London", "Berlin", "Singapore",
        "Tokyo", "Toronto", "Seattle", "Austin", "Boston"
    ]

    EVENT_TEMPLATES = [
        ("Graduated from {university}", "education"),
        ("Joined {company} as {title}", "job"),
        ("Published paper on {topic}", "research"),
        ("Won {hackathon} hackathon", "hackathon"),
        ("Open-sourced {project} on GitHub", "project"),
        ("Speaking at {conference}", "conference"),
        ("Shipped {product} to production", "project"),
        ("Achieved {achievement}", "milestone"),
        ("Collaborated on {initiative}", "collaboration"),
        ("Passed {certification}", "certification")
    ]

    UNIVERSITIES = [
        "MIT", "Stanford", "CMU", "Berkeley", "Caltech",
        "Oxford", "Cambridge", "ETH Zurich", "NUS Singapore",
        "Tokyo University"
    ]

    def __init__(self, subject_name: str, email_hint: str = None, domain_context: str = None):
        self.subject_name = subject_name
        self.email_hint = email_hint
        self.domain_context = domain_context or "software engineering cybersecurity AI"

        # Generate deterministic seed from subject name
        self.seed = DeterministicSeeder.hash_to_seed(subject_name)
        random.seed(self.seed)
        np.random.seed(self.seed)

    def _generate_username_variations(self, base_name: str) -> List[str]:
        """Generate deterministic username variations"""
        random.seed(self.seed)
        parts = base_name.lower().split()
        if not parts:
            parts = ["unknown"]
        
        variations = [
            parts[0],  # first name
            parts[-1] if len(parts) > 1 else parts[0],  # last name
            f"{parts[0]}{parts[-1]}" if len(parts) > 1 else parts[0],  # firstlast
            f"{parts[0]}_{parts[-1]}" if len(parts) > 1 else parts[0],  # first_last
            f"{parts[0]}.{parts[-1]}" if len(parts) > 1 else parts[0],  # first.last
            f"{parts[0]}{random.randint(1, 99)}",  # name + number
        ]
        
        return variations

    def _generate_platforms(self, username_base: str) -> Dict[str, PlatformProfile]:
        """Generate realistic platform profiles with actual usernames"""
        random.seed(self.seed)
        platforms = {}
        
        # Generate 6-8 platform profiles
        num_platforms = random.randint(6, 8)
        platform_keys = list(self.PLATFORM_DATA.keys())
        selected_platforms = random.sample(platform_keys, min(num_platforms, len(platform_keys)))

        for platform_key in selected_platforms:
            platform_info = self.PLATFORM_DATA[platform_key]
            username = self._select_deterministic_username(username_base, platform_key)
            
            platforms[platform_key] = PlatformProfile(
                platform=platform_key,
                username=username,
                url=f"https://{platform_info['domain']}/{username}",
                follower_count=random.randint(50, 50000),
                verification_status=random.random() > 0.7,
                last_activity=self._random_recent_date()
            )

        return platforms

    def _select_deterministic_username(self, base: str, platform: str) -> str:
        """Deterministically select username for platform"""
        random.seed(self.seed + hash(platform) % 1000)
        variations = self._generate_username_variations(base)
        return random.choice(variations)

    def _generate_timeline_events(self, name: str, num_events: int = 8) -> List[TimelineEvent]:
        """Generate 6-8 timeline events with RFC-3339 timestamps"""
        random.seed(self.seed)
        events = []
        
        # Generate events over past 5 years
        now = datetime.now()
        
        for i in range(num_events):
            days_ago = random.randint(30, 1825)  # 1 month to 5 years ago
            event_date = now - timedelta(days=days_ago)
            
            # Select random event template
            template, event_type = random.choice(self.EVENT_TEMPLATES)
            
            # Fill in template with random data
            context = {
                "company": random.choice(self.COMPANIES),
                "title": random.choice(self.JOB_TITLES),
                "university": random.choice(self.UNIVERSITIES),
                "topic": random.choice(["machine learning", "security", "distributed systems", "cryptography"]),
                "hackathon": f"{'AI' if random.random() > 0.5 else 'Cyber'} Hackathon 2024",
                "project": f"open-source-{random.choice(['framework', 'tool', 'library'])}",
                "conference": random.choice(["Black Hat", "DEFCON", "PyCon", "SRECon"]),
                "product": random.choice(["feature", "tool", "service", "integration"]),
                "achievement": random.choice(["1000 GitHub stars", "5 CVEs disclosed", "first place"]),
                "initiative": random.choice(["security team", "AI research", "open source community"]),
                "certification": random.choice(["OSCP", "CEH", "CISSP", "CKA"])
            }
            
            description = template.format(**context)
            
            events.append(TimelineEvent(
                timestamp=event_date.isoformat() + "Z",
                event_type=event_type,
                title=description[:50],
                description=description,
                platform=random.choice(list(self.PLATFORM_DATA.keys())),
                location=random.choice(self.CITIES) if random.random() > 0.3 else None
            ))

        return sorted(events, key=lambda x: x.timestamp, reverse=True)

    def _generate_evidence(self, username_base: str, platforms: Dict) -> List[Evidence]:
        """Generate 8+ evidence objects with RFC-3339 timestamps"""
        random.seed(self.seed)
        evidence_list = []
        
        num_evidence = random.randint(8, 15)
        
        for i in range(num_evidence):
            source_platform = random.choice(list(platforms.keys()))
            now = datetime.now()
            days_ago = random.randint(1, 365)
            evidence_date = now - timedelta(days=days_ago)
            
            evidence_type = random.choice([
                "bio_match", "username_consistency", "activity_pattern",
                "connection_overlap", "content_analysis", "temporal_pattern",
                "credential_reuse", "identifier_correlation"
            ])
            
            evidence_list.append(Evidence(
                id=str(uuid.uuid4()),
                source_platform=source_platform,
                evidence_type=evidence_type,
                content=f"{evidence_type.title()}: {username_base} identified on {source_platform}",
                timestamp=evidence_date.isoformat() + "Z",
                credibility_score=random.uniform(60, 95),
                url=f"https://{self.PLATFORM_DATA[source_platform]['domain']}/{username_base}",
                metadata={
                    "collection_method": "osint",
                    "confidence": str(round(random.uniform(0.7, 0.99), 2)),
                    "corroboration_count": str(random.randint(1, 5))
                }
            ))

        return evidence_list

    def _random_recent_date(self) -> str:
        """Generate recent date in RFC-3339 format"""
        now = datetime.now()
        days_ago = random.randint(1, 30)
        date = now - timedelta(days=days_ago)
        return date.isoformat() + "Z"

    def generate_candidates(self) -> List[Candidate]:
        """
        Generate exactly 3 candidate profiles with realistic data
        Candidate 1: True Target (85-95% confidence)
        Candidate 2: Ambiguous Namesake (30-45% confidence)
        Candidate 3: Anomaly/Conflict (50-65% confidence)
        """
        candidates = []

        # CANDIDATE 1: The True Target (85-95% confidence)
        name_parts = self.subject_name.split()
        if not name_parts:
            name_parts = ["Unknown"]
            
        username_base_1 = name_parts[0].lower()

        platforms_1 = self._generate_platforms(username_base_1)
        events_1 = self._generate_timeline_events(self.subject_name, 8)
        evidence_1 = self._generate_evidence(username_base_1, platforms_1)
        
        bio_text_1 = f"Senior {random.choice(self.JOB_TITLES)} at {random.choice(self.COMPANIES)}"

        # ── DEMO OVERRIDES ──────────────────────────────────────────────────
        email = (self.email_hint or "").lower().strip()
        subj = self.subject_name.lower()
        is_demo_override = False
        
        if "hammadyousuf" in email or "hammad" in subj:
            is_demo_override = True
            bio_text_1 = "Student at JBIET | Hackathon Winner"
            events_1 = [
                TimelineEvent(
                    timestamp="2027-05-15T00:00:00Z",
                    event_type="education",
                    title="Expected Graduation from JBIET (B.Tech)",
                    description="B.Tech passing out 2027 at JBIET",
                    platform="linkedin",
                    location=None
                ),
                TimelineEvent(
                    timestamp="2024-08-10T00:00:00Z",
                    event_type="hackathon",
                    title="Hackathon Winner at HackX",
                    description="Won first place at HackX hackathon.",
                    platform="github",
                    location=None
                ),
                TimelineEvent(
                    timestamp="2023-05-15T00:00:00Z",
                    event_type="education",
                    title="Passed out from Krishnaveni (Inter)",
                    description="Completed Intermediate at Krishnaveni",
                    platform="linkedin",
                    location=None
                ),
                TimelineEvent(
                    timestamp="2021-05-15T00:00:00Z",
                    event_type="education",
                    title="Passed out from Triveni School",
                    description="Completed Schooling at Triveni",
                    platform="linkedin",
                    location=None
                )
            ]
        elif "dlokeshrao" in email or "lokesh" in subj:
            is_demo_override = True
            bio_text_1 = "Student at JBREC | NetworkWorks Intern"
            events_1 = [
                TimelineEvent(
                    timestamp="2028-05-15T00:00:00Z",
                    event_type="education",
                    title="Expected Graduation from JBREC (B.Tech)",
                    description="B.Tech passing out 2028 at JBREC",
                    platform="linkedin",
                    location=None
                ),
                TimelineEvent(
                    timestamp="2024-07-01T00:00:00Z",
                    event_type="job",
                    title="NetworkWorks Internship",
                    description="Completed internship at NetworkWorks.",
                    platform="linkedin",
                    location=None
                ),
                TimelineEvent(
                    timestamp="2024-05-15T00:00:00Z",
                    event_type="education",
                    title="Passed out from Vector College (Inter)",
                    description="Completed Intermediate at Vector College",
                    platform="linkedin",
                    location=None
                ),
                TimelineEvent(
                    timestamp="2022-05-15T00:00:00Z",
                    event_type="education",
                    title="Passed out from Vishvodaya School",
                    description="Completed Schooling at Vishvodaya",
                    platform="linkedin",
                    location=None
                )
            ]
        elif "ishan" in email or "ishan" in subj:
            is_demo_override = True
            bio_text_1 = "Student at JBIET"
            events_1 = [
                TimelineEvent(
                    timestamp="2024-05-15T00:00:00Z",
                    event_type="education",
                    title="Passed out from Govt Polytechnic (Diploma)",
                    description="Completed Diploma at Govt Polytechnic",
                    platform="linkedin",
                    location=None
                ),
                TimelineEvent(
                    timestamp="2021-05-15T00:00:00Z",
                    event_type="education",
                    title="Passed out from SHA School (10th)",
                    description="Completed 10th at SHA School",
                    platform="linkedin",
                    location=None
                )
            ]
        # ────────────────────────────────────────────────────────────────────

        engine = MLSimilarityEngine()
        name_score_1 = 92.0  # Very high for true target
        bio_score_1 = engine.bio_similarity(
            f"{self.subject_name} is a {random.choice(self.JOB_TITLES)}",
            f"{random.choice(self.JOB_TITLES)} working on {random.choice(['AI', 'Security', 'Systems'])}",
            self.domain_context
        )
        platform_score_1 = engine.platform_consistency_score(
            {k: v.model_dump() for k, v in platforms_1.items()},
            username_base_1
        )
        evidence_score_1 = engine.evidence_corroboration_score(
            [e.model_dump() for e in evidence_1],
            list(platforms_1.keys())
        )

        overall_1 = engine.calculate_overall_confidence(
            name_score_1, bio_score_1, platform_score_1, evidence_score_1
        )

        candidates.append(Candidate(
            candidate_id=f"cand_{uuid.uuid4().hex[:8]}",
            name=self.subject_name,
            bio=bio_text_1,
            overall_confidence=min(95.0, max(85.0, overall_1)),

            confidence_breakdown=ConfidenceBreakdown(
                name_match=92.0,
                bio_similarity=max(5.0, min(98.0, bio_score_1)),
                cross_platform_consistency=max(5.0, min(98.0, platform_score_1)),
                evidence_corroboration=max(5.0, min(98.0, evidence_score_1))
            ),
            aliases=self._generate_username_variations(username_base_1)[:3],
            platforms=platforms_1,
            timeline_events=events_1,
            evidence=evidence_1,
            conflicts=[],
            investigation_tags=["verified", "active", "high_confidence"],
            risk_level="LOW"
        ))
        
        if is_demo_override:
            return candidates

        # CANDIDATE 2: Ambiguous Namesake (30-45% confidence)
        # Same name but completely different industry
        platforms_2 = self._generate_platforms(name_parts[-1].lower() if len(name_parts) > 1 else name_parts[0])
        events_2 = self._generate_timeline_events(f"{self.subject_name} (Alternative)", 6)
        evidence_2 = self._generate_evidence(name_parts[-1].lower(), platforms_2)

        name_score_2 = 85.0  # Full name match
        bio_score_2 = engine.bio_similarity(
            f"{self.subject_name} is a musician",
            "musician recording artist producer",
            "music entertainment"
        )
        platform_score_2 = engine.platform_consistency_score(
            {k: v.model_dump() for k, v in platforms_2.items()},
            name_parts[-1].lower() if len(name_parts) > 1 else name_parts[0]
        )
        evidence_score_2 = engine.evidence_corroboration_score(
            [e.model_dump() for e in evidence_2],
            list(platforms_2.keys())
        )

        overall_2 = engine.calculate_overall_confidence(
            name_score_2, bio_score_2, platform_score_2, evidence_score_2
        )

        candidates.append(Candidate(
            candidate_id=f"cand_{uuid.uuid4().hex[:8]}",
            name=self.subject_name,
            bio=f"Musician and Creative Professional",
            overall_confidence=max(30.0, min(45.0, overall_2)),
            confidence_breakdown=ConfidenceBreakdown(
                name_match=85.0,
                bio_similarity=max(5.0, min(98.0, bio_score_2)),
                cross_platform_consistency=max(5.0, min(98.0, platform_score_2)),
                evidence_corroboration=max(5.0, min(98.0, evidence_score_2))
            ),
            aliases=[name_parts[-1].lower()] if len(name_parts) > 1 else [],
            platforms=platforms_2,
            timeline_events=events_2,
            evidence=evidence_2,
            conflicts=[],
            investigation_tags=["name_only_match", "different_industry"],
            risk_level="MEDIUM"
        ))

        # CANDIDATE 3: Anomaly/Conflict (50-65% confidence)
        platforms_3 = self._generate_platforms(f"{name_parts[0]}_alt")
        events_3 = self._generate_timeline_events(f"{self.subject_name} (Anomaly)", 5)
        evidence_3 = self._generate_evidence(f"{name_parts[0]}_alt", platforms_3)

        # Create conflict: location overlap
        conflict = Conflict(
            conflict_id=str(uuid.uuid4()),
            conflict_type=ConflictType.LOCATION_OVERLAP,
            severity="high",
            description="Claims to be in London and Tokyo within 6 hours",
            affected_platforms=["twitter", "linkedin"],
            evidence_ids=[e.id for e in evidence_3[:2]]
        )

        name_score_3 = 45.0  # Similar but not exact
        bio_score_3 = engine.bio_similarity(
            f"{self.subject_name} variant",
            f"{random.choice(self.JOB_TITLES)} in {random.choice(self.CITIES)}",
            self.domain_context
        )
        platform_score_3 = engine.platform_consistency_score(
            {k: v.model_dump() for k, v in platforms_3.items()},
            f"{name_parts[0]}_alt"
        )
        evidence_score_3 = engine.evidence_corroboration_score(
            [e.model_dump() for e in evidence_3],
            list(platforms_3.keys())
        )

        overall_3 = engine.calculate_overall_confidence(
            name_score_3, bio_score_3, platform_score_3, evidence_score_3
        )

        candidates.append(Candidate(
            candidate_id=f"cand_{uuid.uuid4().hex[:8]}",
            name=f"{self.subject_name} (Anomaly)",
            bio=f"Similar profile with inconsistencies",
            overall_confidence=max(50.0, min(65.0, overall_3)),
            confidence_breakdown=ConfidenceBreakdown(
                name_match=45.0,
                bio_similarity=max(5.0, min(98.0, bio_score_3)),
                cross_platform_consistency=max(5.0, min(98.0, platform_score_3)),
                evidence_corroboration=max(5.0, min(98.0, evidence_score_3))
            ),
            aliases=[f"{name_parts[0]}_alt"],
            platforms=platforms_3,
            timeline_events=events_3,
            evidence=evidence_3,
            conflicts=[conflict],
            investigation_tags=["suspicious_activity", "location_anomaly"],
            risk_level="HIGH"
        ))

        return candidates

    def build_knowledge_graph(self, candidates: List[Candidate]) -> Tuple[List[Dict], List[Dict]]:
        """Build knowledge graph nodes and edges from candidates"""
        nodes = []
        edges = []

        # Add candidate nodes
        for candidate in candidates:
            nodes.append({
                "id": candidate.candidate_id,
                "label": candidate.name,
                "node_type": "candidate",
                "confidence": candidate.overall_confidence,
                "metadata": {
                    "risk_level": candidate.risk_level,
                    "investigation_tags": ",".join(candidate.investigation_tags)
                }
            })

            # Add platform nodes
            for platform_name, profile in candidate.platforms.items():
                platform_node_id = f"plat_{candidate.candidate_id}_{platform_name}"
                nodes.append({
                    "id": platform_node_id,
                    "label": f"{profile.username}@{platform_name}",
                    "node_type": "platform",
                    "confidence": 85.0,
                    "metadata": {
                        "platform": platform_name,
                        "url": profile.url,
                        "verification": str(profile.verification_status)
                    }
                })

                # Edge from candidate to platform
                edges.append({
                    "source": candidate.candidate_id,
                    "target": platform_node_id,
                    "relationship": "has_profile",
                    "strength": 0.9,
                    "evidence_ids": [e.id for e in candidate.evidence if e.source_platform == platform_name]
                })

        return nodes, edges
