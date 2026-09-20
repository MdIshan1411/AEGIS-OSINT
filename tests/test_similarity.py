"""
TRACE-X Similarity Module Tests.

Tests for name normalization, handle normalization, name similarity
(Jaro-Winkler + token sort + initials), alias similarity, and
TF-IDF bio similarity.
"""

from __future__ import annotations

import pytest

from trace_x.ml.similarity import (
    alias_similarity,
    bio_similarity,
    multi_bio_similarity,
    name_similarity,
    normalize_handle,
    normalize_name,
)


# ── Name Normalization Tests ────────────────────────────────


class TestNormalizeName:
    """Tests for normalize_name()."""

    def test_basic_lowercase(self):
        """Basic names are lowercased and stripped."""
        assert normalize_name("John Doe") == "john doe"

    def test_diacritics_stripped(self):
        """Diacritics (accents) are removed."""
        result = normalize_name("José García")
        assert result == "jose garcia"

    def test_unicode_umlaut(self):
        """German umlauts are stripped to base letters."""
        result = normalize_name("Müller")
        assert "u" in result  # ü → u
        assert "ü" not in result

    def test_nickname_expansion(self):
        """Nicknames are expanded to canonical forms."""
        assert normalize_name("Bob Smith") == "robert smith"
        assert normalize_name("Bill Gates") == "william gates"
        assert normalize_name("Mike Johnson") == "michael johnson"

    def test_digits_removed(self):
        """Digits are stripped from names."""
        result = normalize_name("Alice42")
        assert "42" not in result

    def test_underscores_to_spaces(self):
        """Underscores are converted to spaces."""
        result = normalize_name("john_doe")
        assert "_" not in result
        assert "john" in result and "doe" in result

    def test_empty_string(self):
        """Empty input returns empty string."""
        assert normalize_name("") == ""

    def test_whitespace_collapse(self):
        """Multiple whitespace characters collapse to single space."""
        result = normalize_name("  John    Doe  ")
        assert result == "john doe"

    def test_hyphenated_names(self):
        """Hyphenated names preserve the hyphen."""
        result = normalize_name("Jean-Luc Picard")
        assert "jean-luc" in result


# ── Handle Normalization Tests ──────────────────────────────


class TestNormalizeHandle:
    """Tests for normalize_handle()."""

    def test_basic(self):
        """Basic handle normalization."""
        assert normalize_handle("john_doe_42") == "johndoe"

    def test_at_symbol(self):
        """Leading @ is stripped."""
        assert normalize_handle("@alice") == "alice"

    def test_dots_and_hyphens(self):
        """Dots and hyphens are removed."""
        assert normalize_handle("j.smith-dev") == "jsmithdev"

    def test_empty(self):
        """Empty handle returns empty string."""
        assert normalize_handle("") == ""

    def test_internal_digits_kept(self):
        """Digits in the middle are preserved."""
        result = normalize_handle("user2name")
        assert "2" in result


# ── Name Similarity Tests ───────────────────────────────────


class TestNameSimilarity:
    """Tests for name_similarity()."""

    def test_exact_match(self):
        """Identical names score very high."""
        score = name_similarity("Alice Johnson", "Alice Johnson")
        assert score > 95.0

    def test_reversed_names(self):
        """Token-reversed names still score high."""
        score = name_similarity("John Doe", "Doe, John")
        assert score > 85.0

    def test_initials_matching(self):
        """Initials match against full names."""
        score = name_similarity("J.D.", "John Doe")
        assert score > 50.0  # Should be a reasonable match

    def test_nickname_matching(self):
        """Nicknames are resolved before comparison."""
        score = name_similarity("Bob Smith", "Robert Smith")
        assert score > 95.0  # Bob → Robert

    def test_completely_different(self):
        """Completely different names score low."""
        score = name_similarity("Alice Johnson", "Zephyr Moonbeam")
        assert score < 55.0  # Jaro-Winkler baseline for same-length strings is ~50

    def test_empty_names(self):
        """Empty names return 0."""
        assert name_similarity("", "John") == 0.0
        assert name_similarity("John", "") == 0.0

    def test_unicode_names(self):
        """Unicode names normalize and compare correctly."""
        score = name_similarity("José García", "Jose Garcia")
        assert score > 90.0


# ── Alias Similarity Tests ──────────────────────────────────


class TestAliasSimilarity:
    """Tests for alias_similarity()."""

    def test_cross_platform_aliases(self):
        """Find best match across aliases and names."""
        score = alias_similarity(
            {"aliases": ["johndoe", "j.doe"], "username": "john_doe"},
            {"name": "John Doe", "username": "jdoe"},
        )
        assert score > 70.0

    def test_no_identifiers(self):
        """Empty profiles return 0."""
        assert alias_similarity({}, {}) == 0.0

    def test_username_only(self):
        """Match by username alone."""
        score = alias_similarity(
            {"username": "alice_johnson"},
            {"username": "alicejohnson"},
        )
        assert score > 70.0


# ── Bio Similarity Tests ────────────────────────────────────


class TestBioSimilarity:
    """Tests for bio_similarity() and multi_bio_similarity()."""

    def test_high_similarity(self):
        """Nearly identical bios score high."""
        score = bio_similarity(
            "Full-stack engineer at Google",
            "Full-stack engineer @ Google",
        )
        assert score > 60.0

    def test_low_similarity(self):
        """Completely different bios score low."""
        score = bio_similarity(
            "AI researcher focusing on reinforcement learning",
            "Professional chef specializing in Italian cuisine",
        )
        assert score < 30.0

    def test_empty_bios(self):
        """Empty bios return 0.0 without crashing."""
        assert bio_similarity("", "") == 0.0
        assert bio_similarity(None, None) == 0.0
        assert bio_similarity("Engineer", None) == 0.0
        assert bio_similarity(None, "Engineer") == 0.0

    def test_identical_bios(self):
        """Identical bios score very high."""
        bio = "Senior software engineer with 10 years of experience in Python and distributed systems"
        score = bio_similarity(bio, bio)
        assert score > 90.0

    def test_multi_bio(self):
        """Multi-bio similarity returns correct number of scores."""
        target = "Machine learning engineer"
        candidates = [
            "ML engineer at tech company",
            "Professional gardener and landscaper",
            "Deep learning researcher",
        ]
        scores = multi_bio_similarity(target, candidates)
        assert len(scores) == 3
        assert scores[0] > scores[1]  # ML engineer > gardener
