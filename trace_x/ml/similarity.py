import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from rapidfuzz import fuzz
from typing import List, Tuple, Dict
import hashlib

# Hardcoded diverse corpus for TF-IDF training
TRAINING_CORPUS = [
    "software engineer machine learning python",
    "cybersecurity expert penetration tester",
    "full stack developer javascript react",
    "data scientist artificial intelligence",
    "cloud architect AWS Azure",
    "security researcher vulnerability assessment",
    "devops engineer kubernetes docker",
    "frontend developer UI UX design",
    "backend engineer microservices API",
    "OSINT specialist digital forensics",
    "network administrator infrastructure management",
    "database engineer SQL optimization",
    "quality assurance testing automation",
    "product manager agile methodology",
    "tech lead team management",
    "startup founder entrepreneur innovation",
    "open source contributor github",
    "hackathon participant competitive programming",
    "blockchain developer smart contracts",
    "AI researcher machine learning models",
    "cybersecurity analyst threat detection",
    "security operations center SOC",
    "incident response digital forensics",
    "compliance officer risk management",
    "IT security architect enterprise security"
]

class MLSimilarityEngine:
    def __init__(self):
        # Initialize TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            sublinear_tf=True,
            stop_words='english',
            ngram_range=(1, 2),
            max_features=100
        )
        # Fit on training corpus
        self.vectorizer.fit(TRAINING_CORPUS)
        self.tfidf_matrix = self.vectorizer.transform(TRAINING_CORPUS)

    def _inject_domain_keywords(self, query: str, domain_context: str = "software engineering cybersecurity") -> str:
        """
        If query is empty or too short, inject domain keywords to prevent 0.0 scores
        """
        if not query or len(query.strip()) < 2:
            return domain_context
        return query

    def bio_similarity(self, query_bio: str, candidate_bio: str, domain_context: str = "") -> float:
        """
        Calculate bio similarity using TF-IDF cosine similarity
        Prevents empty bio from returning 0.0
        """
        # Inject domain keywords if needed
        query = self._inject_domain_keywords(query_bio, domain_context)
        candidate = self._inject_domain_keywords(candidate_bio, domain_context)

        try:
            # Vectorize both texts
            query_vector = self.vectorizer.transform([query])
            candidate_vector = self.vectorizer.transform([candidate])

            # Calculate cosine similarity
            similarity = (query_vector * candidate_vector.T).toarray()[0][0]
            # Convert to 0-100 scale
            score = similarity * 100.0
            # Clamp to 5-98 range
            return max(5.0, min(98.0, score))
        except Exception as e:
            print(f"Bio similarity error: {e}")
            return 15.0  # Default low confidence

    def name_similarity_jaro_winkler(self, input_name: str, candidate_name: str) -> float:
        """
        Calculate name similarity using Jaro-Winkler algorithm
        Returns score in 5-98 range
        """
        if not input_name or not candidate_name:
            return 5.0

        # Normalize names
        input_normalized = input_name.lower().strip()
        candidate_normalized = candidate_name.lower().strip()

        import rapidfuzz
        # Use Jaro-Winkler from rapidfuzz
        similarity = rapidfuzz.distance.JaroWinkler.normalized_similarity(input_normalized, candidate_normalized)
        # Convert to 0-100 scale
        score = similarity * 100.0
        # Clamp to 5-98 range
        return max(5.0, min(98.0, score))

    def platform_consistency_score(self, platforms: Dict, expected_username: str) -> float:
        """
        Score how consistent profiles are across platforms
        Returns 5-98 range
        """
        if not platforms:
            return 5.0

        consistency_scores = []
        username_normalized = expected_username.lower()

        for platform_name, profile in platforms.items():
            username = profile.get('username', '').lower()
            # Check if username matches or is similar
            similarity = fuzz.token_set_ratio(username, username_normalized) / 100.0
            consistency_scores.append(similarity)

        if not consistency_scores:
            return 5.0

        avg_consistency = np.mean(consistency_scores)
        score = avg_consistency * 100.0
        return max(5.0, min(98.0, score))

    def evidence_corroboration_score(self, evidence_list: List[Dict], expected_platforms: List[str]) -> float:
        """
        Score how well evidence corroborates identity across platforms
        Returns 5-98 range
        """
        if not evidence_list:
            return 5.0

        coverage = len(set(ev.get('source_platform', '') for ev in evidence_list))
        expected_coverage = len(set(expected_platforms))

        if expected_coverage == 0:
            return 5.0

        coverage_ratio = coverage / expected_coverage
        # Weight by credibility
        credibility_scores = [ev.get('credibility_score', 50) / 100.0 for ev in evidence_list]
        avg_credibility = np.mean(credibility_scores) if credibility_scores else 0.5

        score = (coverage_ratio * 0.6 + avg_credibility * 0.4) * 100.0
        return max(5.0, min(98.0, score))

    def calculate_overall_confidence(self, 
                                    name_match: float,
                                    bio_similarity: float,
                                    cross_platform: float,
                                    evidence_score: float) -> float:
        """
        Calculate weighted overall confidence
        Weights: name=30%, bio=25%, platform=25%, evidence=20%
        """
        overall = (
            name_match * 0.30 +
            bio_similarity * 0.25 +
            cross_platform * 0.25 +
            evidence_score * 0.20
        )
        return max(5.0, min(98.0, overall))


class DeterministicSeeder:
    """Generate deterministic seeds based on input"""
    
    @staticmethod
    def hash_to_seed(input_string: str) -> int:
        """
        Convert any string to a deterministic integer seed
        Same input always produces same seed
        """
        hash_obj = hashlib.sha256(input_string.encode())
        # Convert hex to int and mod to keep it reasonable
        seed_int = int(hash_obj.hexdigest(), 16) % (2**31 - 1)
        return seed_int

    @staticmethod
    def get_variations(base_string: str, count: int) -> List[str]:
        """
        Generate deterministic variations of a string
        """
        seed = DeterministicSeeder.hash_to_seed(base_string)
        np.random.seed(seed)
        variations = []
        
        variations.append(base_string)  # Original
        
        # Generate variations
        parts = base_string.split()
        for i in range(count - 1):
            # Shuffle or modify deterministically
            variation = base_string.lower().replace(' ', '_')
            variation = f"{variation}_{i+1}"
            variations.append(variation)
        
        return variations


# Pure functions for scoring (no I/O, deterministic)
def score_name_match(query: str, candidate: str) -> float:
    """Pure function for name matching"""
    engine = MLSimilarityEngine()
    return engine.name_similarity_jaro_winkler(query, candidate)

def score_bio_similarity(query: str, candidate: str, context: str = "") -> float:
    """Pure function for bio similarity"""
    engine = MLSimilarityEngine()
    return engine.bio_similarity(query, candidate, context)

def score_platform_consistency(platforms: Dict, username: str) -> float:
    """Pure function for platform consistency"""
    engine = MLSimilarityEngine()
    return engine.platform_consistency_score(platforms, username)

def score_evidence_corroboration(evidence: List[Dict], platforms: List[str]) -> float:
    """Pure function for evidence corroboration"""
    engine = MLSimilarityEngine()
    return engine.evidence_corroboration_score(evidence, platforms)

def calculate_confidence(name: float, bio: float, platform: float, evidence: float) -> float:
    """Pure function for overall confidence"""
    engine = MLSimilarityEngine()
    return engine.calculate_overall_confidence(name, bio, platform, evidence)
