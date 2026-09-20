import pytest
import numpy as np
from datetime import datetime
from trace_x.ml.similarity import (
    MLSimilarityEngine, DeterministicSeeder,
    score_name_match, score_bio_similarity
)
from trace_x.services.discovery import DynamicOSINTGenerator
from trace_x.schemas.models import (
    ConfidenceBreakdown, Candidate, PlatformProfile, Evidence,
    InvestigationRequest, InvestigationResponse
)

class TestDeterministicSeeding:
    """Test that seeding produces reproducible results"""

    def test_same_name_produces_same_seed(self):
        """Verify same input name always produces same seed"""
        seed1 = DeterministicSeeder.hash_to_seed("Mohammed Ishan")
        seed2 = DeterministicSeeder.hash_to_seed("Mohammed Ishan")
        assert seed1 == seed2, "Same input should produce identical seeds"

    def test_different_names_produce_different_seeds(self):
        """Verify different names produce different seeds"""
        seed1 = DeterministicSeeder.hash_to_seed("Mohammed Ishan")
        seed2 = DeterministicSeeder.hash_to_seed("Bob Chen")
        assert seed1 != seed2, "Different inputs should produce different seeds"

    def test_seed_is_deterministic_integer(self):
        """Verify seed is always a valid integer"""
        seed = DeterministicSeeder.hash_to_seed("Test Name")
        assert isinstance(seed, int), "Seed should be integer type"
        assert 0 <= seed < 2**31 - 1, "Seed should be in valid range"

class TestMLSimilarityEngine:
    """Test ML similarity scoring functions"""

    @pytest.fixture
    def engine(self):
        return MLSimilarityEngine()

    def test_name_similarity_jaro_winkler_perfect_match(self, engine):
        """Perfect name match should score high"""
        score = engine.name_similarity_jaro_winkler("Alice Johnson", "Alice Johnson")
        assert score > 90, "Perfect match should score > 90"
        assert score <= 98.0, "Score should not exceed 98"

    def test_name_similarity_partial_match(self, engine):
        """Partial name match should score moderately"""
        score = engine.name_similarity_jaro_winkler("Alice Johnson", "alice johnsen")
        assert score > 50, "Similar name should score > 50"
        assert score <= 98.0, "Score clamping should work"

    def test_name_similarity_different_names(self, engine):
        """Different names should score low but not 0"""
        score = engine.name_similarity_jaro_winkler("Alice", "Zoe")
        assert score >= 5.0, "Should be clamped to minimum 5.0"
        assert score < 50, "Very different names should score < 50"

    def test_name_similarity_empty_string_handling(self, engine):
        """Empty strings should return min score"""
        score = engine.name_similarity_jaro_winkler("", "Alice")
        assert score == 5.0, "Empty string should return minimum score"

    def test_bio_similarity_prevents_zero_score(self, engine):
        """Empty bio should not return 0.0"""
        score = engine.bio_similarity("", "", "software engineering")
        assert score >= 5.0, "Empty bio should be clamped to minimum 5.0"
        assert score <= 98.0, "Score should not exceed 98"

    def test_bio_similarity_matching_content(self, engine):
        """Similar bios should score high"""
        bio1 = "software engineer machine learning python"
        bio2 = "engineer software python machine learning"
        score = engine.bio_similarity(bio1, bio2)
        assert score > 50, "Similar bios should score > 50"

    def test_platform_consistency_no_platforms(self, engine):
        """No platforms should return min score"""
        score = engine.platform_consistency_score({}, "username")
        assert score == 5.0, "No platforms should return minimum"

    def test_platform_consistency_matching_usernames(self, engine):
        """Consistent usernames should score high"""
        platforms = {
            "github": {"username": "alice_dev"},
            "twitter": {"username": "alice_dev"}
        }
        score = engine.platform_consistency_score(platforms, "alice_dev")
        assert score > 60, "Consistent platforms should score high"

    def test_overall_confidence_calculation(self, engine):
        """Overall confidence should be weighted average"""
        overall = engine.calculate_overall_confidence(
            name_match=90.0,
            bio_similarity=80.0,
            cross_platform=85.0,
            evidence_score=75.0
        )
        # Weights: name=30%, bio=25%, platform=25%, evidence=20%
        expected = (90 * 0.30 + 80 * 0.25 + 85 * 0.25 + 75 * 0.20)
        assert abs(overall - expected) < 1, "Overall should match weighted average"
        assert overall >= 5.0 and overall <= 98.0, "Should be clamped"

    def test_all_scores_clamped_to_range(self, engine):
        """All scoring functions should clamp to 5-98 range"""
        # Test with edge values
        for score_func in [
            lambda: engine.name_similarity_jaro_winkler("a", ""),
            lambda: engine.bio_similarity("", ""),
            lambda: engine.platform_consistency_score({}, ""),
        ]:
            score = score_func()
            assert 5.0 <= score <= 98.0, f"Score {score} out of bounds"

class TestDynamicOSINTGenerator:
    """Test OSINT data generation"""

    def test_generator_creates_three_candidates(self):
        """Generator should always create exactly 3 candidates"""
        generator = DynamicOSINTGenerator("Test User")
        candidates = generator.generate_candidates()
        assert len(candidates) == 3, "Should generate exactly 3 candidates"

    def test_first_candidate_high_confidence(self):
        """First candidate (true target) should have 85-95% confidence"""
        generator = DynamicOSINTGenerator("Alice Johnson")
        candidates = generator.generate_candidates()
        assert 85 <= candidates[0].overall_confidence <= 95, \
            "True target should have 85-95% confidence"

    def test_second_candidate_ambiguous_confidence(self):
        """Second candidate (namesake) should have 30-45% confidence"""
        generator = DynamicOSINTGenerator("Alice Johnson")
        candidates = generator.generate_candidates()
        assert 30 <= candidates[1].overall_confidence <= 45, \
            "Namesake should have 30-45% confidence"

    def test_third_candidate_anomaly_confidence(self):
        """Third candidate (anomaly) should have 50-65% confidence"""
        generator = DynamicOSINTGenerator("Alice Johnson")
        candidates = generator.generate_candidates()
        assert 50 <= candidates[2].overall_confidence <= 65, \
            "Anomaly should have 50-65% confidence"

    def test_deterministic_generation_same_result(self):
        """Same name should always generate identical candidates"""
        gen1 = DynamicOSINTGenerator("Bob Chen")
        gen2 = DynamicOSINTGenerator("Bob Chen")

        cands1 = gen1.generate_candidates()
        cands2 = gen2.generate_candidates()

        # Compare key attributes
        assert cands1[0].name == cands2[0].name
        assert cands1[0].overall_confidence == cands2[0].overall_confidence
        assert len(cands1[0].evidence) == len(cands2[0].evidence)

    def test_candidates_have_platforms(self):
        """Each candidate should have 6-8 platforms"""
        generator = DynamicOSINTGenerator("Test User")
        candidates = generator.generate_candidates()

        for candidate in candidates:
            assert 6 <= len(candidate.platforms) <= 8, \
                "Each candidate should have 6-8 platforms"

    def test_candidates_have_evidence(self):
        """Each candidate should have 8+ evidence items"""
        generator = DynamicOSINTGenerator("Test User")
        candidates = generator.generate_candidates()

        for candidate in candidates:
            assert len(candidate.evidence) >= 8, \
                "Each candidate should have 8+ evidence items"

    def test_candidates_have_timeline_events(self):
        """Each candidate should have timeline events"""
        generator = DynamicOSINTGenerator("Test User")
        candidates = generator.generate_candidates()

        for candidate in candidates:
            assert len(candidate.timeline_events) > 0, \
                "Each candidate should have timeline events"

    def test_evidence_timestamps_are_valid_rfc3339(self):
        """All timestamps should be valid RFC-3339 format"""
        generator = DynamicOSINTGenerator("Test User")
        candidates = generator.generate_candidates()

        for candidate in candidates:
            for evidence in candidate.evidence:
                # Should not raise exception
                datetime.fromisoformat(evidence.timestamp.replace('Z', '+00:00'))

    def test_third_candidate_has_conflicts(self):
        """Third candidate should have conflicts"""
        generator = DynamicOSINTGenerator("Test User")
        candidates = generator.generate_candidates()
        
        assert len(candidates[2].conflicts) > 0, \
            "Third candidate (anomaly) should have conflicts"

    def test_knowledge_graph_generation(self):
        """Knowledge graph should have nodes and edges"""
        generator = DynamicOSINTGenerator("Test User")
        candidates = generator.generate_candidates()
        nodes, edges = generator.build_knowledge_graph(candidates)

        assert len(nodes) > 0, "Should have nodes"
        assert len(edges) > 0, "Should have edges"
        # Should have nodes for candidates and platforms
        assert len(nodes) >= 3, "Should have at least 3 candidate nodes"

class TestPydanticModels:
    """Test Pydantic model validation and schema enforcement"""

    def test_confidence_breakdown_score_clamping(self):
        """Scores should be clamped to 5-98 range"""
        cb = ConfidenceBreakdown(
            name_match=150.0,  # Should be clamped
            bio_similarity=-10.0,  # Should be clamped
            cross_platform_consistency=50.0,
            evidence_corroboration=75.0
        )
        assert cb.name_match <= 98.0, "name_match should be clamped"
        assert cb.bio_similarity >= 5.0, "bio_similarity should be clamped"

    def test_candidate_creates_successfully(self):
        """Candidate model should create with valid data"""
        candidate = Candidate(
            candidate_id="test_123",
            name="Test User",
            overall_confidence=85.0,
            confidence_breakdown=ConfidenceBreakdown(
                name_match=90.0,
                bio_similarity=80.0,
                cross_platform_consistency=85.0,
                evidence_corroboration=75.0
            ),
            aliases=["test_user", "testuser"]
        )
        assert candidate.name == "Test User"
        assert candidate.overall_confidence == 85.0

    def test_platform_profile_validation(self):
        """Platform profile should validate correctly"""
        profile = PlatformProfile(
            platform="github",
            username="testuser",
            url="https://github.com/testuser",
            follower_count=1000,
            verification_status=True
        )
        assert profile.platform == "github"
        assert profile.verification_status is True

class TestPureFunctions:
    """Test pure scoring functions"""

    def test_pure_score_name_match(self):
        """Pure function should return valid score"""
        score = score_name_match("Alice", "Alice")
        assert 5.0 <= score <= 98.0, "Score should be in valid range"

    def test_pure_score_bio_similarity(self):
        """Pure function should return valid score"""
        score = score_bio_similarity("software engineer", "engineer software")
        assert 5.0 <= score <= 98.0, "Score should be in valid range"

    def test_pure_functions_are_deterministic(self):
        """Pure functions should produce same output for same input"""
        score1 = score_name_match("Test", "Test")
        score2 = score_name_match("Test", "Test")
        assert score1 == score2, "Pure functions should be deterministic"

class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_empty_name_handling(self):
        """Empty names should be handled gracefully"""
        generator = DynamicOSINTGenerator("")
        # Should not crash
        candidates = generator.generate_candidates()
        assert len(candidates) == 3

    def test_very_long_name_handling(self):
        """Very long names should be handled"""
        long_name = "A" * 500
        generator = DynamicOSINTGenerator(long_name)
        candidates = generator.generate_candidates()
        assert len(candidates) == 3

    def test_special_characters_in_name(self):
        """Special characters in name should be handled"""
        special_name = "José García-Martínez"
        generator = DynamicOSINTGenerator(special_name)
        candidates = generator.generate_candidates()
        assert len(candidates) == 3

class TestInvestigationFlow:
    """Test complete investigation flow"""

    def test_investigation_request_validation(self):
        """InvestigationRequest should validate"""
        request = InvestigationRequest(
            subject_name="Alice Johnson",
            email_hint="alice@example.com",
            domain_context="tech industry"
        )
        assert request.subject_name == "Alice Johnson"

    def test_full_investigation_generation(self):
        """Complete investigation should generate all components"""
        generator = DynamicOSINTGenerator(
            subject_name="Full Test User",
            email_hint="test@example.com",
            domain_context="cybersecurity"
        )
        
        candidates = generator.generate_candidates()
        nodes, edges = generator.build_knowledge_graph(candidates)

        # Verify all components exist
        assert len(candidates) == 3
        assert all(c.confidence_breakdown for c in candidates)
        assert all(c.platforms for c in candidates)
        assert all(c.evidence for c in candidates)
        assert all(c.timeline_events for c in candidates)
        assert len(nodes) > 0
        assert len(edges) > 0

# Performance tests
class TestPerformance:
    """Test performance characteristics"""

    def test_generation_speed(self):
        """Generation should complete in reasonable time"""
        import time
        start = time.time()
        
        generator = DynamicOSINTGenerator("Performance Test")
        candidates = generator.generate_candidates()
        
        elapsed = time.time() - start
        assert elapsed < 5.0, f"Generation took {elapsed}s, should be < 5s"

    def test_deterministic_generation_consistency(self):
        """Multiple generations of same name should be identical"""
        results = []
        for _ in range(5):
            gen = DynamicOSINTGenerator("Consistency Test")
            candidates = gen.generate_candidates()
            results.append(candidates[0].overall_confidence)
        
        # All results should be identical
        assert len(set(results)) == 1, "Deterministic generation should be consistent"

class TestEntityResolutionExplanations:
    """Test detailed explanation generation for Candidates"""
    
    def test_strong_match_explanation(self):
        from trace_x.ml.engine import _generate_detailed_explanation
        from trace_x.schemas.models import MatchStatus
        
        # High scores across the board
        explanation = _generate_detailed_explanation(
            overall=92.5, name_score=95.0, bio_score=85.0, 
            cross_platform=90.0, evidence_count=3, conflict_count=0
        )
        
        assert explanation["match_status"] == MatchStatus.STRONG_MATCH
        assert any("Strong name match" in reason for reason in explanation["match_reasons"])
        assert any("High bio similarity" in reason for reason in explanation["match_reasons"])
        assert any("corroborating evidence" in ev for ev in explanation["supporting_evidence"])
        assert len(explanation["contradicting_evidence"]) == 0
        assert len(explanation["missing_evidence"]) == 0
        assert "Strong Match" in explanation["explanation"]

    def test_namesake_low_confidence_explanation(self):
        from trace_x.ml.engine import _generate_detailed_explanation
        from trace_x.schemas.models import MatchStatus
        
        # High name match, but low everything else
        explanation = _generate_detailed_explanation(
            overall=35.0, name_score=85.0, bio_score=15.0, 
            cross_platform=20.0, evidence_count=0, conflict_count=0
        )
        
        assert explanation["match_status"] == MatchStatus.LOW_CONFIDENCE
        assert any("Strong name match" in reason for reason in explanation["match_reasons"])
        assert any("Low bio similarity" in reason for reason in explanation["mismatch_reasons"])
        assert any("Inconsistent cross-platform" in ev for ev in explanation["contradicting_evidence"])
        assert any("No strong supporting" in ev for ev in explanation["missing_evidence"])
        assert "Low Confidence" in explanation["explanation"]

    def test_conflicting_evidence_explanation(self):
        from trace_x.ml.engine import _generate_detailed_explanation
        from trace_x.schemas.models import MatchStatus
        
        # Conflicting information
        explanation = _generate_detailed_explanation(
            overall=55.0, name_score=80.0, bio_score=65.0, 
            cross_platform=75.0, evidence_count=1, conflict_count=2
        )
        
        assert explanation["match_status"] == MatchStatus.CONFLICTING_EVIDENCE
        assert any("2 severe identity conflicts" in ev for ev in explanation["contradicting_evidence"])
        assert any("Conflicting information present" in reason for reason in explanation["mismatch_reasons"])
        assert "Conflicting Evidence" in explanation["explanation"]

    def test_missing_data_explanation(self):
        from trace_x.ml.engine import _generate_detailed_explanation
        from trace_x.schemas.models import MatchStatus
        
        # No bio or platform (scores clamped to 5.0)
        explanation = _generate_detailed_explanation(
            overall=65.0, name_score=90.0, bio_score=5.0, 
            cross_platform=5.0, evidence_count=1, conflict_count=0
        )
        
        assert explanation["match_status"] == MatchStatus.POSSIBLE_MATCH
        assert any("No significant bio overlap" in ev for ev in explanation["missing_evidence"])
        assert any("Insufficient data" in ev for ev in explanation["missing_evidence"])
        assert not any("Low bio similarity" in ev for ev in explanation["mismatch_reasons"])

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
