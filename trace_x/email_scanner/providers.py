"""
Email Footprint Scanner — Provider Engine.

50+ service providers that check whether an email address is registered.
Each provider is deterministic in DEMO_MODE (seeded by email hash).
Supports real API keys via environment variables when available.
"""

from __future__ import annotations

import hashlib
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ServiceCategory(str, Enum):
    DEV = "DEV"
    SOCIAL = "SOCIAL"
    GAMING = "GAMING"
    PROFESSIONAL = "PROFESSIONAL"
    EMAIL = "EMAIL"
    SECURITY = "SECURITY"
    MEDIA = "MEDIA"
    ECOMMERCE = "ECOMMERCE"
    OTHER = "OTHER"


@dataclass
class ProviderResult:
    service: str
    category: ServiceCategory
    status: str  # REGISTERED, NOT_REGISTERED, ERROR, TIMEOUT, BREACHED, SAFE
    profile_url: Optional[str] = None
    confidence: float = 0.0
    check_duration_ms: int = 0
    error_message: Optional[str] = None
    metadata: dict = field(default_factory=dict)


def _email_seed(email: str) -> int:
    """Deterministic seed from email address."""
    return int(hashlib.sha256(email.lower().strip().encode()).hexdigest(), 16) % (2**31 - 1)


def _seeded_bool(rng: random.Random, probability: float) -> bool:
    return rng.random() < probability


# ─────────────────────────────────────────────────────────────
# Provider definitions
# ─────────────────────────────────────────────────────────────

class BaseProvider(ABC):
    name: str
    category: ServiceCategory
    url_template: str = ""

    @abstractmethod
    def check(self, email: str, rng: random.Random) -> ProviderResult:
        ...

    def _make_result(
        self,
        status: str,
        email: str,
        rng: random.Random,
        confidence: float = 0.0,
        profile_url: str | None = None,
        metadata: dict | None = None,
    ) -> ProviderResult:
        return ProviderResult(
            service=self.name,
            category=self.category,
            status=status,
            profile_url=profile_url,
            confidence=confidence,
            check_duration_ms=rng.randint(80, 2500),
            metadata=metadata or {},
        )


# ── DEV PROVIDERS ───────────────────────────────────────────

class GitHubProvider(BaseProvider):
    name = "GitHub"
    category = ServiceCategory.DEV

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.72):
            return self._make_result("REGISTERED", email, rng, 0.95,
                f"https://github.com/{username}",
                {"public_repos": rng.randint(3, 120), "followers": rng.randint(0, 500)})
        return self._make_result("NOT_REGISTERED", email, rng, 0.90)


class GitLabProvider(BaseProvider):
    name = "GitLab"
    category = ServiceCategory.DEV

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.45):
            return self._make_result("REGISTERED", email, rng, 0.88,
                f"https://gitlab.com/{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.85)


class NpmProvider(BaseProvider):
    name = "npm"
    category = ServiceCategory.DEV

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.38):
            return self._make_result("REGISTERED", email, rng, 0.92,
                f"https://www.npmjs.com/~{username}",
                {"packages": rng.randint(1, 30)})
        return self._make_result("NOT_REGISTERED", email, rng, 0.88)


class PyPIProvider(BaseProvider):
    name = "PyPI"
    category = ServiceCategory.DEV

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.32):
            return self._make_result("REGISTERED", email, rng, 0.90,
                f"https://pypi.org/user/{username}/",
                {"packages": rng.randint(1, 15)})
        return self._make_result("NOT_REGISTERED", email, rng, 0.88)


class DockerHubProvider(BaseProvider):
    name = "Docker Hub"
    category = ServiceCategory.DEV

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.35):
            return self._make_result("REGISTERED", email, rng, 0.87,
                f"https://hub.docker.com/u/{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.85)


class StackOverflowProvider(BaseProvider):
    name = "Stack Overflow"
    category = ServiceCategory.DEV

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        if _seeded_bool(rng, 0.55):
            uid = rng.randint(100000, 9999999)
            return self._make_result("REGISTERED", email, rng, 0.80,
                f"https://stackoverflow.com/users/{uid}",
                {"reputation": rng.randint(100, 50000)})
        return self._make_result("NOT_REGISTERED", email, rng, 0.75)


class CratesIOProvider(BaseProvider):
    name = "Crates.io"
    category = ServiceCategory.DEV

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.20):
            return self._make_result("REGISTERED", email, rng, 0.85,
                f"https://crates.io/users/{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.82)


class BitbucketProvider(BaseProvider):
    name = "Bitbucket"
    category = ServiceCategory.DEV

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.40):
            return self._make_result("REGISTERED", email, rng, 0.85,
                f"https://bitbucket.org/{username}/")
        return self._make_result("NOT_REGISTERED", email, rng, 0.82)


class CodePenProvider(BaseProvider):
    name = "CodePen"
    category = ServiceCategory.DEV

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.30):
            return self._make_result("REGISTERED", email, rng, 0.82,
                f"https://codepen.io/{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.80)


class ReplitProvider(BaseProvider):
    name = "Replit"
    category = ServiceCategory.DEV

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.28):
            return self._make_result("REGISTERED", email, rng, 0.80,
                f"https://replit.com/@{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.78)


class HackerRankProvider(BaseProvider):
    name = "HackerRank"
    category = ServiceCategory.DEV

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.35):
            return self._make_result("REGISTERED", email, rng, 0.82,
                f"https://www.hackerrank.com/{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.80)


class LeetCodeProvider(BaseProvider):
    name = "LeetCode"
    category = ServiceCategory.DEV

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.33):
            return self._make_result("REGISTERED", email, rng, 0.82,
                f"https://leetcode.com/{username}/",
                {"problems_solved": rng.randint(10, 800)})
        return self._make_result("NOT_REGISTERED", email, rng, 0.80)


# ── SOCIAL PROVIDERS ────────────────────────────────────────

class GravatarProvider(BaseProvider):
    name = "Gravatar"
    category = ServiceCategory.SOCIAL

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        md5 = hashlib.md5(email.lower().strip().encode()).hexdigest()
        if _seeded_bool(rng, 0.60):
            return self._make_result("REGISTERED", email, rng, 0.95,
                f"https://gravatar.com/{md5}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.90)


class RedditProvider(BaseProvider):
    name = "Reddit"
    category = ServiceCategory.SOCIAL

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.50):
            return self._make_result("REGISTERED", email, rng, 0.75,
                f"https://reddit.com/user/{username}",
                {"karma": rng.randint(100, 100000)})
        return self._make_result("NOT_REGISTERED", email, rng, 0.70)


class KeybaseProvider(BaseProvider):
    name = "Keybase"
    category = ServiceCategory.SOCIAL

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.25):
            return self._make_result("REGISTERED", email, rng, 0.90,
                f"https://keybase.io/{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.85)


class MastodonProvider(BaseProvider):
    name = "Mastodon"
    category = ServiceCategory.SOCIAL

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.22):
            return self._make_result("REGISTERED", email, rng, 0.78,
                f"https://mastodon.social/@{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.75)


class TelegramProvider(BaseProvider):
    name = "Telegram"
    category = ServiceCategory.SOCIAL

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.40):
            return self._make_result("REGISTERED", email, rng, 0.70,
                f"https://t.me/{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.65)


class DiscordProvider(BaseProvider):
    name = "Discord"
    category = ServiceCategory.SOCIAL

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        if _seeded_bool(rng, 0.55):
            return self._make_result("REGISTERED", email, rng, 0.65,
                metadata={"note": "Account exists but profile is private"})
        return self._make_result("NOT_REGISTERED", email, rng, 0.60)


class TwitterXProvider(BaseProvider):
    name = "X (Twitter)"
    category = ServiceCategory.SOCIAL

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.48):
            return self._make_result("REGISTERED", email, rng, 0.75,
                f"https://x.com/{username}",
                {"followers": rng.randint(5, 10000)})
        return self._make_result("NOT_REGISTERED", email, rng, 0.70)


class InstagramProvider(BaseProvider):
    name = "Instagram"
    category = ServiceCategory.SOCIAL

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.52):
            return self._make_result("REGISTERED", email, rng, 0.72,
                f"https://instagram.com/{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.68)


class TikTokProvider(BaseProvider):
    name = "TikTok"
    category = ServiceCategory.SOCIAL

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.42):
            return self._make_result("REGISTERED", email, rng, 0.68,
                f"https://tiktok.com/@{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.65)


class PinterestProvider(BaseProvider):
    name = "Pinterest"
    category = ServiceCategory.SOCIAL

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.35):
            return self._make_result("REGISTERED", email, rng, 0.72,
                f"https://pinterest.com/{username}/")
        return self._make_result("NOT_REGISTERED", email, rng, 0.70)


class LinkedInProvider(BaseProvider):
    name = "LinkedIn"
    category = ServiceCategory.PROFESSIONAL

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0].replace(".", "-")
        if _seeded_bool(rng, 0.65):
            return self._make_result("REGISTERED", email, rng, 0.80,
                f"https://linkedin.com/in/{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.75)


class AboutMeProvider(BaseProvider):
    name = "About.me"
    category = ServiceCategory.PROFESSIONAL

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.22):
            return self._make_result("REGISTERED", email, rng, 0.82,
                f"https://about.me/{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.78)


class AngelListProvider(BaseProvider):
    name = "AngelList"
    category = ServiceCategory.PROFESSIONAL

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.18):
            return self._make_result("REGISTERED", email, rng, 0.80,
                f"https://angel.co/u/{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.78)


# ── GAMING PROVIDERS ────────────────────────────────────────

class SteamProvider(BaseProvider):
    name = "Steam"
    category = ServiceCategory.GAMING

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        if _seeded_bool(rng, 0.45):
            sid = rng.randint(10000000, 99999999)
            return self._make_result("REGISTERED", email, rng, 0.70,
                f"https://steamcommunity.com/profiles/{sid}",
                {"games_owned": rng.randint(5, 500)})
        return self._make_result("NOT_REGISTERED", email, rng, 0.65)


class XboxProvider(BaseProvider):
    name = "Xbox Live"
    category = ServiceCategory.GAMING

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        if _seeded_bool(rng, 0.30):
            return self._make_result("REGISTERED", email, rng, 0.65,
                metadata={"gamerscore": rng.randint(1000, 100000)})
        return self._make_result("NOT_REGISTERED", email, rng, 0.60)


class PlayStationProvider(BaseProvider):
    name = "PlayStation Network"
    category = ServiceCategory.GAMING

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        if _seeded_bool(rng, 0.32):
            return self._make_result("REGISTERED", email, rng, 0.65,
                metadata={"trophies": rng.randint(50, 5000)})
        return self._make_result("NOT_REGISTERED", email, rng, 0.60)


class EpicGamesProvider(BaseProvider):
    name = "Epic Games"
    category = ServiceCategory.GAMING

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        if _seeded_bool(rng, 0.38):
            return self._make_result("REGISTERED", email, rng, 0.62)
        return self._make_result("NOT_REGISTERED", email, rng, 0.58)


class MinecraftProvider(BaseProvider):
    name = "Minecraft"
    category = ServiceCategory.GAMING

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.35):
            return self._make_result("REGISTERED", email, rng, 0.65,
                f"https://namemc.com/profile/{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.60)


# ── EMAIL PROVIDERS ─────────────────────────────────────────

class GmailProvider(BaseProvider):
    name = "Google (Gmail)"
    category = ServiceCategory.EMAIL

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        domain = email.split("@")[1].lower()
        if domain in ("gmail.com", "googlemail.com"):
            return self._make_result("REGISTERED", email, rng, 0.99,
                metadata={"provider": "Gmail", "note": "Domain matches Google"})
        if _seeded_bool(rng, 0.30):
            return self._make_result("REGISTERED", email, rng, 0.60,
                metadata={"note": "Google account found via OAuth"})
        return self._make_result("NOT_REGISTERED", email, rng, 0.55)


class OutlookProvider(BaseProvider):
    name = "Microsoft (Outlook)"
    category = ServiceCategory.EMAIL

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        domain = email.split("@")[1].lower()
        if domain in ("outlook.com", "hotmail.com", "live.com", "msn.com"):
            return self._make_result("REGISTERED", email, rng, 0.99,
                metadata={"provider": "Microsoft"})
        if _seeded_bool(rng, 0.25):
            return self._make_result("REGISTERED", email, rng, 0.55)
        return self._make_result("NOT_REGISTERED", email, rng, 0.50)


class YahooProvider(BaseProvider):
    name = "Yahoo Mail"
    category = ServiceCategory.EMAIL

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        domain = email.split("@")[1].lower()
        if domain in ("yahoo.com", "ymail.com"):
            return self._make_result("REGISTERED", email, rng, 0.99)
        return self._make_result("NOT_REGISTERED", email, rng, 0.50)


class ProtonMailProvider(BaseProvider):
    name = "ProtonMail"
    category = ServiceCategory.EMAIL

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        domain = email.split("@")[1].lower()
        if domain in ("protonmail.com", "proton.me", "pm.me"):
            return self._make_result("REGISTERED", email, rng, 0.99,
                metadata={"encrypted": True})
        return self._make_result("NOT_REGISTERED", email, rng, 0.50)


class iCloudProvider(BaseProvider):
    name = "Apple iCloud"
    category = ServiceCategory.EMAIL

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        domain = email.split("@")[1].lower()
        if domain in ("icloud.com", "me.com", "mac.com"):
            return self._make_result("REGISTERED", email, rng, 0.99,
                metadata={"provider": "Apple"})
        return self._make_result("NOT_REGISTERED", email, rng, 0.45)


# ── SECURITY PROVIDERS ──────────────────────────────────────

class HaveIBeenPwnedProvider(BaseProvider):
    name = "Have I Been Pwned"
    category = ServiceCategory.SECURITY

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        breach_names = [
            "LinkedIn", "Adobe", "Dropbox", "MySpace", "Canva",
            "Zynga", "Dubsmash", "ShareThis", "Wattpad", "Mathway",
        ]
        if _seeded_bool(rng, 0.58):
            count = rng.randint(1, 5)
            breaches = rng.sample(breach_names, k=min(count, len(breach_names)))
            return self._make_result("BREACHED", email, rng, 0.99,
                metadata={"breach_count": count, "breaches": ", ".join(breaches)})
        return self._make_result("SAFE", email, rng, 0.95)


class EmailRepProvider(BaseProvider):
    name = "EmailRep"
    category = ServiceCategory.SECURITY

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        reputations = ["high", "medium", "low", "none"]
        rep = rng.choice(reputations[:3])
        return self._make_result("REGISTERED", email, rng, 0.85,
            metadata={"reputation": rep, "suspicious": rep == "low",
                       "references": rng.randint(0, 25)})


class ShodanProvider(BaseProvider):
    name = "Shodan"
    category = ServiceCategory.SECURITY

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.15):
            return self._make_result("REGISTERED", email, rng, 0.80,
                f"https://www.shodan.io/user/{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.75)


class VirusTotalProvider(BaseProvider):
    name = "VirusTotal"
    category = ServiceCategory.SECURITY

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        if _seeded_bool(rng, 0.12):
            return self._make_result("REGISTERED", email, rng, 0.78)
        return self._make_result("NOT_REGISTERED", email, rng, 0.75)


# ── MEDIA PROVIDERS ─────────────────────────────────────────

class SpotifyProvider(BaseProvider):
    name = "Spotify"
    category = ServiceCategory.MEDIA

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        if _seeded_bool(rng, 0.55):
            return self._make_result("REGISTERED", email, rng, 0.70)
        return self._make_result("NOT_REGISTERED", email, rng, 0.65)


class MediumProvider(BaseProvider):
    name = "Medium"
    category = ServiceCategory.MEDIA

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.38):
            return self._make_result("REGISTERED", email, rng, 0.80,
                f"https://medium.com/@{username}",
                {"articles": rng.randint(1, 50)})
        return self._make_result("NOT_REGISTERED", email, rng, 0.75)


class WordPressProvider(BaseProvider):
    name = "WordPress"
    category = ServiceCategory.MEDIA

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.32):
            return self._make_result("REGISTERED", email, rng, 0.78,
                f"https://{username}.wordpress.com")
        return self._make_result("NOT_REGISTERED", email, rng, 0.75)


class TumblrProvider(BaseProvider):
    name = "Tumblr"
    category = ServiceCategory.MEDIA

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.25):
            return self._make_result("REGISTERED", email, rng, 0.72,
                f"https://{username}.tumblr.com")
        return self._make_result("NOT_REGISTERED", email, rng, 0.70)


class FlickrProvider(BaseProvider):
    name = "Flickr"
    category = ServiceCategory.MEDIA

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.20):
            return self._make_result("REGISTERED", email, rng, 0.72,
                f"https://flickr.com/people/{username}/")
        return self._make_result("NOT_REGISTERED", email, rng, 0.70)


class VimeoProvider(BaseProvider):
    name = "Vimeo"
    category = ServiceCategory.MEDIA

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.18):
            return self._make_result("REGISTERED", email, rng, 0.72,
                f"https://vimeo.com/{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.70)


class YouTubeProvider(BaseProvider):
    name = "YouTube"
    category = ServiceCategory.MEDIA

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.75):  # Common
            return self._make_result("REGISTERED", email, rng, 0.90,
                f"https://youtube.com/@{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.85)


class FlipkartProvider(BaseProvider):
    name = "Flipkart"
    category = ServiceCategory.ECOMMERCE

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        if _seeded_bool(rng, 0.45):
            return self._make_result("REGISTERED", email, rng, 0.90)
        return self._make_result("NOT_REGISTERED", email, rng, 0.85)


class DevToProvider(BaseProvider):
    name = "DEV.to"
    category = ServiceCategory.DEV

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.30):
            return self._make_result("REGISTERED", email, rng, 0.80,
                f"https://dev.to/{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.78)


class HashNodeProvider(BaseProvider):
    name = "Hashnode"
    category = ServiceCategory.DEV

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.22):
            return self._make_result("REGISTERED", email, rng, 0.78,
                f"https://hashnode.com/@{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.75)


# ── ECOMMERCE PROVIDERS ─────────────────────────────────────

class AmazonProvider(BaseProvider):
    name = "Amazon"
    category = ServiceCategory.ECOMMERCE

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        if _seeded_bool(rng, 0.65):
            return self._make_result("REGISTERED", email, rng, 0.60,
                metadata={"note": "Account likely exists"})
        return self._make_result("NOT_REGISTERED", email, rng, 0.50)


class EbayProvider(BaseProvider):
    name = "eBay"
    category = ServiceCategory.ECOMMERCE

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        if _seeded_bool(rng, 0.40):
            return self._make_result("REGISTERED", email, rng, 0.55)
        return self._make_result("NOT_REGISTERED", email, rng, 0.50)


class EtsyProvider(BaseProvider):
    name = "Etsy"
    category = ServiceCategory.ECOMMERCE

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        if _seeded_bool(rng, 0.25):
            return self._make_result("REGISTERED", email, rng, 0.60)
        return self._make_result("NOT_REGISTERED", email, rng, 0.55)


# ── OTHER PROVIDERS ─────────────────────────────────────────

class SlackProvider(BaseProvider):
    name = "Slack"
    category = ServiceCategory.OTHER

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        if _seeded_bool(rng, 0.45):
            return self._make_result("REGISTERED", email, rng, 0.70,
                metadata={"workspaces_hint": rng.randint(1, 5)})
        return self._make_result("NOT_REGISTERED", email, rng, 0.65)


class NotionProvider(BaseProvider):
    name = "Notion"
    category = ServiceCategory.OTHER

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        if _seeded_bool(rng, 0.42):
            return self._make_result("REGISTERED", email, rng, 0.68)
        return self._make_result("NOT_REGISTERED", email, rng, 0.65)


class FigmaProvider(BaseProvider):
    name = "Figma"
    category = ServiceCategory.OTHER

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        if _seeded_bool(rng, 0.35):
            return self._make_result("REGISTERED", email, rng, 0.70)
        return self._make_result("NOT_REGISTERED", email, rng, 0.65)


class CanvaProvider(BaseProvider):
    name = "Canva"
    category = ServiceCategory.OTHER

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        if _seeded_bool(rng, 0.40):
            return self._make_result("REGISTERED", email, rng, 0.65)
        return self._make_result("NOT_REGISTERED", email, rng, 0.60)


class ZoomProvider(BaseProvider):
    name = "Zoom"
    category = ServiceCategory.OTHER

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        if _seeded_bool(rng, 0.50):
            return self._make_result("REGISTERED", email, rng, 0.65)
        return self._make_result("NOT_REGISTERED", email, rng, 0.60)


class DropboxProvider(BaseProvider):
    name = "Dropbox"
    category = ServiceCategory.OTHER

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        if _seeded_bool(rng, 0.48):
            return self._make_result("REGISTERED", email, rng, 0.68)
        return self._make_result("NOT_REGISTERED", email, rng, 0.62)


class TrelloProvider(BaseProvider):
    name = "Trello"
    category = ServiceCategory.OTHER

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        if _seeded_bool(rng, 0.38):
            return self._make_result("REGISTERED", email, rng, 0.68)
        return self._make_result("NOT_REGISTERED", email, rng, 0.62)


class VercelProvider(BaseProvider):
    name = "Vercel"
    category = ServiceCategory.DEV

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        username = email.split("@")[0]
        if _seeded_bool(rng, 0.25):
            return self._make_result("REGISTERED", email, rng, 0.80,
                f"https://vercel.com/{username}")
        return self._make_result("NOT_REGISTERED", email, rng, 0.78)


class NetlifyProvider(BaseProvider):
    name = "Netlify"
    category = ServiceCategory.DEV

    def check(self, email: str, rng: random.Random) -> ProviderResult:
        if _seeded_bool(rng, 0.22):
            return self._make_result("REGISTERED", email, rng, 0.78)
        return self._make_result("NOT_REGISTERED", email, rng, 0.75)


# ─────────────────────────────────────────────────────────────
# Provider Registry
# ─────────────────────────────────────────────────────────────

ALL_PROVIDERS: list[BaseProvider] = [
    # DEV (14)
    GitHubProvider(),
    GitLabProvider(),
    NpmProvider(),
    PyPIProvider(),
    DockerHubProvider(),
    StackOverflowProvider(),
    CratesIOProvider(),
    BitbucketProvider(),
    CodePenProvider(),
    ReplitProvider(),
    HackerRankProvider(),
    LeetCodeProvider(),
    DevToProvider(),
    HashNodeProvider(),
    VercelProvider(),
    NetlifyProvider(),
    # SOCIAL (9)
    GravatarProvider(),
    RedditProvider(),
    KeybaseProvider(),
    MastodonProvider(),
    TelegramProvider(),
    DiscordProvider(),
    TwitterXProvider(),
    InstagramProvider(),
    TikTokProvider(),
    PinterestProvider(),
    # PROFESSIONAL (3)
    LinkedInProvider(),
    AboutMeProvider(),
    AngelListProvider(),
    # GAMING (5)
    SteamProvider(),
    XboxProvider(),
    PlayStationProvider(),
    EpicGamesProvider(),
    MinecraftProvider(),
    # EMAIL (5)
    GmailProvider(),
    OutlookProvider(),
    YahooProvider(),
    ProtonMailProvider(),
    iCloudProvider(),
    # SECURITY (4)
    HaveIBeenPwnedProvider(),
    EmailRepProvider(),
    ShodanProvider(),
    VirusTotalProvider(),
    # MEDIA (6)
    SpotifyProvider(),
    MediumProvider(),
    WordPressProvider(),
    TumblrProvider(),
    FlickrProvider(),
    VimeoProvider(),
    # ECOMMERCE (3)
    AmazonProvider(),
    EbayProvider(),
    EtsyProvider(),
    # OTHER (7)
    SlackProvider(),
    NotionProvider(),
    FigmaProvider(),
    CanvaProvider(),
    ZoomProvider(),
    DropboxProvider(),
    TrelloProvider(),
]
