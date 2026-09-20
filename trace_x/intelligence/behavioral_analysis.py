"""
TRACE-X Behavioral Analysis Engine.

Generates behavioral fingerprints for target identities including:
- Circadian rhythm analysis (active hours, sleep patterns, timezone inference)
- Linguistic markers (vocabulary, emoji usage, writing style)
- Interaction patterns (engagement style, reply behavior)
- Technical fingerprint (device, OS, browser, IP stability)
- Content preferences (topics, domains, content type)

Uses deterministic seeding for demo reproducibility.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


# ── Data Classes ─────────────────────────────────────────────

@dataclass
class CircadianProfile:
    """24-hour activity rhythm analysis."""
    hourly_activity: List[float]  # 24 values (0.0-1.0) representing activity per hour
    peak_hours: List[int]  # Top 3 most active hours
    sleep_gap_start: int  # Hour when sleep period begins (0-23)
    sleep_duration_hours: float
    inferred_timezone: str
    consistency_score: float  # How regular is their schedule (0.0-1.0)


@dataclass
class LinguisticProfile:
    """Writing style and language analysis."""
    avg_word_length: float
    vocabulary_richness: float  # Unique words / total words
    emoji_frequency: float  # Emojis per 100 words
    favorite_emojis: List[str]
    capitalization_style: str  # "proper", "lowercase", "mixed", "uppercase"
    punctuation_density: float  # Punctuation marks per sentence
    avg_sentence_length: float  # Words per sentence
    formality_score: float  # 0.0 (very informal) to 1.0 (very formal)
    language_detected: str


@dataclass
class InteractionProfile:
    """Social interaction behavior analysis."""
    reply_ratio: float  # Proportion of posts that are replies
    retweet_ratio: float  # Proportion that are reposts
    original_content_ratio: float
    engagement_style: str  # "creator", "curator", "conversationalist", "lurker"
    avg_response_time_minutes: float
    network_density: float  # How interconnected is their network
    top_interaction_topics: List[str]


@dataclass
class TechnicalProfile:
    """Device and technical fingerprint."""
    primary_device: str  # "Mobile", "Desktop", "Tablet"
    os_fingerprint: str  # "iOS", "Android", "Windows", "macOS", "Linux"
    primary_browser: str  # "Chrome", "Safari", "Firefox", "Edge"
    ip_consistency: str  # "stable", "mobile", "vpn_detected"
    primary_region: str
    device_count: int  # Number of distinct devices detected
    session_duration_avg_minutes: float


@dataclass
class ContentProfile:
    """Content preference analysis."""
    top_topics: List[str]
    topic_consistency: float  # How focused vs. scattered (0.0-1.0)
    content_type_distribution: Dict[str, float]  # "text", "image", "video", "link"
    posting_frequency: str  # "daily", "weekly", "sporadic"
    content_originality: float  # Original vs. reshared (0.0-1.0)
    sentiment_distribution: Dict[str, float]  # "positive", "neutral", "negative"


@dataclass
class BehavioralSignature:
    """Complete behavioral fingerprint for a target."""
    target_identifier: str
    circadian: CircadianProfile
    linguistic: LinguisticProfile
    interaction: InteractionProfile
    technical: TechnicalProfile
    content: ContentProfile
    signature_strength: float  # Overall confidence (0.0-1.0)
    uniqueness_score: float  # How distinctive is this signature (0.0-1.0)
    generated_at: str


# ── Demo Overrides ───────────────────────────────────────────

_DEMO_CIRCADIAN = {
    "ishan": {
        "peak_hours": [10, 14, 21],
        "sleep_start": 0,
        "sleep_duration": 7.5,
        "timezone": "Asia/Kolkata (UTC+5:30)",
    },
    "hammad": {
        "peak_hours": [11, 15, 22],
        "sleep_start": 1,
        "sleep_duration": 7.0,
        "timezone": "Asia/Kolkata (UTC+5:30)",
    },
    "lokesh": {
        "peak_hours": [9, 13, 20],
        "sleep_start": 23,
        "sleep_duration": 7.5,
        "timezone": "Asia/Kolkata (UTC+5:30)",
    },
}

_DEMO_TOPICS = {
    "ishan": ["Cybersecurity", "OSINT Tools", "Python", "Web Development", "Chess"],
    "hammad": ["Hackathons", "Full-Stack Dev", "AI/ML", "Open Source", "Networking"],
    "lokesh": ["Data Structures", "Algorithms", "LeetCode", "Backend Dev", "Networking"],
}


# ── Engine ───────────────────────────────────────────────────

class BehavioralAnalysisEngine:
    """
    Generates behavioral fingerprints for any target identity.

    Analyzes circadian rhythms, linguistic patterns, interaction
    behaviors, technical fingerprints, and content preferences.

    Demo mode: uses deterministic seeding for consistent results.
    """

    TIMEZONES = [
        "America/New_York (UTC-5)", "America/Los_Angeles (UTC-8)",
        "Europe/London (UTC+0)", "Europe/Berlin (UTC+1)",
        "Asia/Kolkata (UTC+5:30)", "Asia/Tokyo (UTC+9)",
        "Asia/Shanghai (UTC+8)", "Australia/Sydney (UTC+11)",
    ]

    EMOJIS = ["🔥", "💻", "🚀", "✅", "👀", "🎯", "💡", "🤔", "😂", "❤️", "🙌", "⭐", "🎉", "👍", "🔒"]

    TOPICS = [
        "Machine Learning", "Cybersecurity", "Web Development", "DevOps",
        "Cloud Computing", "Blockchain", "Data Science", "Mobile Development",
        "Open Source", "API Design", "System Design", "Algorithms",
        "Networking", "Database Design", "Testing", "CI/CD",
    ]

    DEVICES = ["iPhone 15", "Samsung Galaxy S24", "Google Pixel 8", "Desktop PC", "MacBook Pro", "ThinkPad"]
    OS_LIST = ["iOS 17", "Android 14", "Windows 11", "macOS Sonoma", "Ubuntu 22.04"]
    BROWSERS = ["Chrome 120", "Safari 17", "Firefox 121", "Edge 120"]

    REGIONS = [
        "Hyderabad, India", "Bangalore, India", "Mumbai, India",
        "San Francisco, USA", "London, UK", "Berlin, Germany",
        "Tokyo, Japan", "Singapore", "Toronto, Canada",
    ]

    def __init__(self):
        pass

    def _get_seed(self, identifier: str) -> int:
        return int(hashlib.sha256(identifier.lower().encode()).hexdigest()[:8], 16)

    def _check_demo(self, identifier: str) -> Optional[str]:
        ident = identifier.lower()
        for key in _DEMO_CIRCADIAN:
            if key in ident:
                return key
        return None

    def generate_behavioral_signature(
        self,
        target_identifier: str,
        email_hint: str = "",
        subject_name: str = "",
    ) -> BehavioralSignature:
        """Generate a complete behavioral fingerprint."""
        combined = f"{target_identifier} {email_hint} {subject_name}".lower().strip()
        seed = self._get_seed(combined)
        rng = random.Random(seed)
        demo_key = self._check_demo(combined)

        circadian = self._generate_circadian(rng, demo_key)
        linguistic = self._generate_linguistic(rng, demo_key)
        interaction = self._generate_interaction(rng, demo_key)
        technical = self._generate_technical(rng, demo_key)
        content = self._generate_content(rng, demo_key)

        return BehavioralSignature(
            target_identifier=target_identifier,
            circadian=circadian,
            linguistic=linguistic,
            interaction=interaction,
            technical=technical,
            content=content,
            signature_strength=round(rng.uniform(0.82, 0.96), 3) if demo_key else round(rng.uniform(0.55, 0.85), 3),
            uniqueness_score=round(rng.uniform(0.70, 0.95), 3),
            generated_at=datetime.now().isoformat(),
        )

    def _generate_circadian(self, rng: random.Random, demo_key: Optional[str]) -> CircadianProfile:
        """Generate 24-hour activity rhythm."""
        if demo_key and demo_key in _DEMO_CIRCADIAN:
            d = _DEMO_CIRCADIAN[demo_key]
            peak_hours = d["peak_hours"]
            sleep_start = d["sleep_start"]
            sleep_dur = d["sleep_duration"]
            tz = d["timezone"]
        else:
            peak_hours = sorted(rng.sample(range(8, 23), 3))
            sleep_start = rng.choice([22, 23, 0, 1])
            sleep_dur = round(rng.uniform(5.5, 8.5), 1)
            tz = rng.choice(self.TIMEZONES)

        # Generate hourly activity curve
        hourly = []
        for h in range(24):
            # Sleep hours get very low activity
            sleep_end = (sleep_start + int(sleep_dur)) % 24
            if sleep_start < sleep_end:
                is_sleep = sleep_start <= h < sleep_end
            else:
                is_sleep = h >= sleep_start or h < sleep_end

            if is_sleep:
                activity = rng.uniform(0.0, 0.08)
            elif h in peak_hours:
                activity = rng.uniform(0.75, 1.0)
            else:
                activity = rng.uniform(0.15, 0.55)

            hourly.append(round(activity, 3))

        return CircadianProfile(
            hourly_activity=hourly,
            peak_hours=peak_hours,
            sleep_gap_start=sleep_start,
            sleep_duration_hours=sleep_dur,
            inferred_timezone=tz,
            consistency_score=round(rng.uniform(0.70, 0.95), 3),
        )

    def _generate_linguistic(self, rng: random.Random, demo_key: Optional[str]) -> LinguisticProfile:
        """Generate linguistic fingerprint."""
        fav_emojis = rng.sample(self.EMOJIS, rng.randint(3, 5))

        return LinguisticProfile(
            avg_word_length=round(rng.uniform(4.2, 5.8), 2),
            vocabulary_richness=round(rng.uniform(0.45, 0.80), 3),
            emoji_frequency=round(rng.uniform(0.5, 4.0), 2),
            favorite_emojis=fav_emojis,
            capitalization_style=rng.choice(["proper", "lowercase", "mixed"]),
            punctuation_density=round(rng.uniform(0.8, 2.5), 2),
            avg_sentence_length=round(rng.uniform(10, 22), 1),
            formality_score=round(rng.uniform(0.3, 0.7), 3) if demo_key else round(rng.uniform(0.2, 0.8), 3),
            language_detected="English",
        )

    def _generate_interaction(self, rng: random.Random, demo_key: Optional[str]) -> InteractionProfile:
        """Generate interaction behavior profile."""
        reply = round(rng.uniform(0.15, 0.45), 3)
        retweet = round(rng.uniform(0.10, 0.35), 3)
        original = round(1.0 - reply - retweet, 3)

        styles = ["creator", "curator", "conversationalist", "lurker"]
        if original > 0.5:
            style = "creator"
        elif retweet > 0.3:
            style = "curator"
        elif reply > 0.35:
            style = "conversationalist"
        else:
            style = rng.choice(styles)

        topics = _DEMO_TOPICS.get(demo_key, rng.sample(self.TOPICS, 4))

        return InteractionProfile(
            reply_ratio=reply,
            retweet_ratio=retweet,
            original_content_ratio=original,
            engagement_style=style,
            avg_response_time_minutes=round(rng.uniform(5, 120), 1),
            network_density=round(rng.uniform(0.3, 0.8), 3),
            top_interaction_topics=topics[:4],
        )

    def _generate_technical(self, rng: random.Random, demo_key: Optional[str]) -> TechnicalProfile:
        """Generate technical fingerprint."""
        if demo_key:
            region = "Hyderabad, India"
        else:
            region = rng.choice(self.REGIONS)

        return TechnicalProfile(
            primary_device=rng.choice(self.DEVICES),
            os_fingerprint=rng.choice(self.OS_LIST),
            primary_browser=rng.choice(self.BROWSERS),
            ip_consistency=rng.choice(["stable", "mobile"]) if demo_key else rng.choice(["stable", "mobile", "vpn_detected"]),
            primary_region=region,
            device_count=rng.randint(1, 3),
            session_duration_avg_minutes=round(rng.uniform(15, 90), 1),
        )

    def _generate_content(self, rng: random.Random, demo_key: Optional[str]) -> ContentProfile:
        """Generate content preference profile."""
        topics = _DEMO_TOPICS.get(demo_key, rng.sample(self.TOPICS, 5))

        text_pct = round(rng.uniform(0.40, 0.65), 2)
        link_pct = round(rng.uniform(0.15, 0.30), 2)
        image_pct = round(rng.uniform(0.10, 0.25), 2)
        video_pct = round(1.0 - text_pct - link_pct - image_pct, 2)
        video_pct = max(0.0, video_pct)

        pos = round(rng.uniform(0.35, 0.60), 2)
        neg = round(rng.uniform(0.05, 0.15), 2)
        neutral = round(1.0 - pos - neg, 2)

        return ContentProfile(
            top_topics=topics,
            topic_consistency=round(rng.uniform(0.55, 0.90), 3),
            content_type_distribution={
                "text": text_pct,
                "link": link_pct,
                "image": image_pct,
                "video": video_pct,
            },
            posting_frequency=rng.choice(["daily", "weekly"]) if demo_key else rng.choice(["daily", "weekly", "sporadic"]),
            content_originality=round(rng.uniform(0.55, 0.90), 3),
            sentiment_distribution={
                "positive": pos,
                "neutral": neutral,
                "negative": neg,
            },
        )
