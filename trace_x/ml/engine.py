"""
TRACE-X Bayesian Entity Resolution Engine.

Core orchestrator: takes a subject query + platform profiles and returns
ranked candidates with explainable Bayesian confidence scores, detected
conflicts, and a knowledge graph. Pure functions — zero I/O.

Bayesian Scoring Formula:
1. Prior P(same_person) = 0.3 (configurable)
2. Per-feature likelihood ratios mapped via sigmoid
3. Log-odds accumulation with weighted features
4. Posterior = sigmoid(log_odds), scaled to [0, 100], clamped (0.1, 99.9)
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any

from trace_x.ml.conflicts import detect_conflicts
from trace_x.ml.evidence import build_evidence, build_feature_contribution
from trace_x.ml.graph import build_knowledge_graph
from trace_x.schemas.enums import (
    CandidateStatus,
    Severity,
    SEVERITY_PENALTY,
    VerificationMethod,
)
from trace_x.schemas.models import (
    Candidate,
    ConfidenceBreakdown,
    Conflict,
    Evidence,
    FeatureContribution,
    PlatformProfile,
    TimelineEvent,
    MatchStatus,
)


# ── Default Configuration ───────────────────────────────────

DEFAULT_WEIGHTS: dict[str, float] = {
    "name": 0.35,
    "bio": 0.25,
    "cross_platform": 0.25,
    "evidence": 0.10,
    "conflict_penalty": 0.05,
}

DEFAULT_PRIOR: float = 0.3


# ── Sigmoid Helper ──────────────────────────────────────────


def _sigmoid(x: float) -> float:
    """
    Numerically stable sigmoid function.

    Args:
        x: Input value.

    Returns:
        Sigmoid output in (0, 1).
    """
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    else:
        z = math.exp(x)
        return z / (1.0 + z)


def _score_to_likelihood_ratio(
    score: float, steepness: float = 0.08, midpoint: float = 50.0
) -> float:
    """
    Convert a 0–100 score to a likelihood ratio via sigmoid mapping.

    High scores → LR >> 1 (evidence for same person).
    Low scores → LR << 1 (evidence against same person).

    Args:
        score: Feature score (0–100).
        steepness: Sigmoid steepness. Higher = sharper transition.
        midpoint: Score at which LR = 1 (neutral evidence).

    Returns:
        Likelihood ratio P(data|same) / P(data|different).
    """
    # Map score to log-odds space
    x = steepness * (score - midpoint)
    lr = math.exp(x)
    # Clamp to avoid infinity
    return max(0.01, min(100.0, lr))


# ── Bayesian Confidence Calculation ─────────────────────────


def calculate_confidence(
    name_score: float,
    bio_score: float,
    cross_platform_consistency: float,
    evidence_count: int,
    conflict_count: int,
    weights: dict[str, float] | None = None,
    prior: float | None = None,
) -> tuple[float, ConfidenceBreakdown]:
    """
    Calculate Bayesian confidence score with full explainability.

    Algorithm:
    1. Start with prior P(same_person) → convert to log-odds
    2. For each feature, compute likelihood ratio via sigmoid mapping
    3. Weight the log-likelihood by feature weight
    4. Accumulate in log-odds space
    5. Add evidence boost (+1% per source, capped +10%)
    6. Apply conflict penalty (-2% per conflict, capped -15%)
    7. Convert back to probability, scale to [0, 100], clamp (0.1, 99.9)

    Args:
        name_score: Name similarity (0–100).
        bio_score: Bio similarity (0–100).
        cross_platform_consistency: Cross-platform agreement (0–100).
        evidence_count: Number of corroborating sources.
        conflict_count: Number of detected contradictions.
        weights: Override default feature weights.
        prior: Override default prior P(same_person).

    Returns:
        Tuple of (overall_confidence, ConfidenceBreakdown).
    """
    w = weights or DEFAULT_WEIGHTS.copy()
    p = prior if prior is not None else DEFAULT_PRIOR

    # Step 1: Prior → log-odds
    prior_odds = p / (1.0 - p)
    log_odds = math.log(max(prior_odds, 1e-10))

    contributions: list[FeatureContribution] = []

    # Step 2–3: Per-feature likelihood ratios
    features = [
        ("name_match", name_score, w.get("name", 0.35)),
        ("bio_similarity", bio_score, w.get("bio", 0.25)),
        ("cross_platform", cross_platform_consistency, w.get("cross_platform", 0.25)),
    ]

    for feat_name, score, weight in features:
        lr = _score_to_likelihood_ratio(score)
        # Weight the log-likelihood
        log_lr = math.log(max(lr, 1e-10)) * weight * 3.0  # Scale factor for sensitivity
        log_odds += log_lr

        contributions.append(
            build_feature_contribution(
                feature=feat_name,
                raw_value=score,
                weight=weight,
                likelihood_ratio=round(lr, 4),
                log_odds_delta=round(log_lr, 4),
                explanation=_explain_feature(feat_name, score, lr),
            )
        )

    # Step 5: Evidence boost
    evidence_boost = min(evidence_count * 1.0, 10.0)
    evidence_log_delta = (evidence_boost / 100.0) * 2.0
    log_odds += evidence_log_delta

    contributions.append(
        build_feature_contribution(
            feature="evidence_boost",
            raw_value=evidence_boost,
            weight=w.get("evidence", 0.10),
            likelihood_ratio=1.0 + evidence_boost / 100.0,
            log_odds_delta=round(evidence_log_delta, 4),
            explanation=f"{evidence_count} corroborating source(s) → +{evidence_boost:.0f}% boost.",
        )
    )

    # Step 6: Conflict penalty
    conflict_penalty = min(conflict_count * 2.0, 15.0)
    conflict_log_delta = -(conflict_penalty / 100.0) * 3.0
    log_odds += conflict_log_delta

    contributions.append(
        build_feature_contribution(
            feature="conflict_penalty",
            raw_value=-conflict_penalty,
            weight=w.get("conflict_penalty", 0.05),
            likelihood_ratio=max(0.01, 1.0 - conflict_penalty / 100.0),
            log_odds_delta=round(conflict_log_delta, 4),
            explanation=f"{conflict_count} conflict(s) detected → -{conflict_penalty:.0f}% penalty.",
        )
    )

    # Step 7: Convert back to probability
    posterior = _sigmoid(log_odds)
    overall = posterior * 100.0

    # Clamp to (0.1, 99.9)
    overall = max(0.1, min(99.9, overall))

    # Generate detailed explanation breakdown
    details = _generate_detailed_explanation(
        overall, name_score, bio_score, cross_platform_consistency,
        evidence_count, conflict_count,
    )

    breakdown = ConfidenceBreakdown(
        name_match=round(name_score, 2),
        bio_similarity=round(bio_score, 2),
        cross_platform_consistency=round(cross_platform_consistency, 2),
        evidence_corroboration=round(evidence_boost * 10, 2), # Multiply by 10 to put in 0-100 range roughly, or just pass evidence_boost if it's already properly scaled. Wait, evidence_boost is max 10.0, so scaling it up by 10 gives up to 100%.
        conflict_penalty=round(conflict_penalty, 2),
        prior=p,
        posterior=round(posterior, 6),
        log_odds=round(log_odds, 4),
        feature_contributions=contributions,
        **details
    )

    return round(overall, 2), breakdown


def _explain_feature(feature: str, score: float, lr: float) -> str:
    """Generate a human-readable explanation for a feature contribution."""
    strength = "strong" if score > 75 else "moderate" if score > 50 else "weak"
    direction = "supports" if lr > 1.0 else "opposes"
    return (
        f"{feature.replace('_', ' ').title()} score of {score:.1f}% "
        f"provides {strength} evidence that {direction} identity match "
        f"(LR={lr:.2f})."
    )


def _generate_detailed_explanation(
    overall: float,
    name_score: float,
    bio_score: float,
    cross_platform: float,
    evidence_count: int,
    conflict_count: int,
) -> dict:
    """Generate a detailed breakdown of matching reasons."""
    match_reasons = []
    mismatch_reasons = []
    supporting_evidence = []
    contradicting_evidence = []
    missing_evidence = []

    if overall >= 80:
        match_status = MatchStatus.STRONG_MATCH
    elif overall >= 60:
        match_status = MatchStatus.POSSIBLE_MATCH
    elif conflict_count > 0:
        match_status = MatchStatus.CONFLICTING_EVIDENCE
    elif overall >= 40:
        match_status = MatchStatus.INSUFFICIENT_EVIDENCE
    else:
        match_status = MatchStatus.LOW_CONFIDENCE

    # Name Match Logic
    if name_score >= 80:
        match_reasons.append(f"Strong name match ({name_score:.1f}%)")
    elif name_score <= 40:
        mismatch_reasons.append(f"Weak name match ({name_score:.1f}%)")
    else:
        match_reasons.append(f"Partial name match ({name_score:.1f}%)")

    # Bio Alignment
    if bio_score >= 60:
        match_reasons.append(f"High bio similarity ({bio_score:.1f}%)")
    elif bio_score <= 20:
        if bio_score <= 10.0:
            missing_evidence.append("No significant bio overlap found across platforms.")
        else:
            mismatch_reasons.append(f"Low bio similarity ({bio_score:.1f}%)")
    else:
        match_reasons.append(f"Moderate bio alignment ({bio_score:.1f}%)")

    # Cross-Platform Consistency
    if cross_platform >= 70:
        supporting_evidence.append(f"Consistent cross-platform presence ({cross_platform:.1f}%)")
    elif cross_platform <= 30:
        if cross_platform <= 10.0:
            missing_evidence.append("Insufficient data for cross-platform comparison.")
        else:
            contradicting_evidence.append(f"Inconsistent cross-platform presence ({cross_platform:.1f}%)")
    else:
        supporting_evidence.append(f"Moderate cross-platform overlap ({cross_platform:.1f}%)")

    # Evidence & Conflicts
    if evidence_count > 0:
        supporting_evidence.append(f"Found {evidence_count} corroborating evidence claims.")
    else:
        missing_evidence.append("No strong supporting evidence claims discovered.")

    if conflict_count > 0:
        contradicting_evidence.append(f"Detected {conflict_count} severe identity conflicts.")
        mismatch_reasons.append("Conflicting information present.")

    # Build summary string
    explanation = " — ".join([match_status.replace("_", " ").title()] + match_reasons[:2]) + "."

    return {
        "match_status": match_status,
        "match_reasons": match_reasons,
        "mismatch_reasons": mismatch_reasons,
        "supporting_evidence": supporting_evidence,
        "contradicting_evidence": contradicting_evidence,
        "missing_evidence": missing_evidence,
        "explanation": explanation
    }


# ── Cross-Platform Consistency ──────────────────────────────


def _calculate_cross_platform_consistency(
    profiles: list[dict],
) -> float:
    """
    Calculate how consistently profiles agree on key fields.

    Checks agreement on: name, bio keywords, location.
    Score = average pairwise agreement across all profile pairs.

    Args:
        profiles: List of profile dicts.

    Returns:
        Consistency score 0–100.
    """
    if len(profiles) < 2:
        return 50.0  # Single source = neutral

    total_score = 0.0
    pair_count = 0

    for i in range(len(profiles)):
        for j in range(i + 1, len(profiles)):
            pa, pb = profiles[i], profiles[j]
            pair_score = 0.0
            checks = 0

            # Name agreement
            name_a = pa.get("display_name") or pa.get("name") or pa.get("username", "")
            name_b = pb.get("display_name") or pb.get("name") or pb.get("username", "")
            if name_a and name_b:
                pair_score += name_similarity(name_a, name_b)
                checks += 1

            # Bio agreement
            bio_a = pa.get("bio")
            bio_b = pb.get("bio")
            if bio_a and bio_b:
                pair_score += bio_similarity(bio_a, bio_b)
                checks += 1

            # Location agreement
            loc_a = (pa.get("location") or "").lower().strip()
            loc_b = (pb.get("location") or "").lower().strip()
            if loc_a and loc_b:
                if loc_a == loc_b:
                    pair_score += 100.0
                elif loc_a in loc_b or loc_b in loc_a:
                    pair_score += 75.0
                else:
                    pair_score += 10.0
                checks += 1

            if checks > 0:
                total_score += pair_score / checks
                pair_count += 1

    if pair_count == 0:
        return 50.0

    return total_score / pair_count


# ── Status Assignment ───────────────────────────────────────


def _assign_status(
    confidence: float, conflict_count: int
) -> CandidateStatus:
    """
    Assign candidate status based on confidence and conflict count.

    Args:
        confidence: Overall confidence (0–100).
        conflict_count: Number of detected conflicts.

    Returns:
        CandidateStatus enum value.
    """
    if conflict_count > 0 and confidence < 70:
        return CandidateStatus.CONFLICT
    if confidence > 80:
        return CandidateStatus.VERIFIED
    if confidence >= 40:
        return CandidateStatus.AMBIGUOUS
    return CandidateStatus.LOW_CONFIDENCE


# ── Apply Severity Penalties ────────────────────────────────


def apply_conflict_penalties(
    base_confidence: float,
    conflicts: list[Conflict],
) -> float:
    """
    Reduce confidence based on conflict severities.

    HIGH: -10 points, MEDIUM: -5 points, LOW: -2 points.

    Args:
        base_confidence: Confidence before penalties.
        conflicts: List of detected conflicts.

    Returns:
        Adjusted confidence, clamped to (0.1, 99.9).
    """
    penalty = 0.0
    for conflict in conflicts:
        penalty += SEVERITY_PENALTY.get(conflict.severity, 0.0)

    adjusted = base_confidence - penalty
    return max(0.1, min(99.9, adjusted))


# ── Main Orchestrator ───────────────────────────────────────


def resolve_candidates(
    subject: dict[str, Any],
    platform_profiles: list[list[dict[str, Any]]],
    timeline_events: list[dict[str, Any]] | None = None,
    config: dict[str, Any] | None = None,
) -> tuple[list[Candidate], list[Conflict], dict[str, Any]]:
    """
    Main orchestrator: resolve a subject against platform profiles.

    Algorithm:
    1. Flatten all profiles into a candidate pool
    2. Calculate pairwise name similarity, bio similarity, alias matching
    3. Aggregate cross-platform consistency
    4. Detect conflicts (location, timeline, employer, bio, name)
    5. Calculate Bayesian confidence for each candidate group
    6. Apply severity-weighted conflict penalties
    7. Rank by confidence, assign status
    8. Build knowledge graph (React Flow JSON)
    9. Return (candidates, conflicts, graph)

    Args:
        subject: Dict with 'name', 'email' (optional), 'bio' (optional), 'context' (optional).
        platform_profiles: Grouped profiles per platform/search — list of lists.
        timeline_events: Optional timeline events for conflict detection.
        config: Optional config override with 'weights', 'prior', etc.

    Returns:
        Tuple of (ranked_candidates, conflicts, relationship_graph).
    """
    cfg = config or {}
    weights = cfg.get("weights", DEFAULT_WEIGHTS)
    prior = cfg.get("prior", DEFAULT_PRIOR)
    investigation_id = cfg.get("investigation_id", str(uuid.uuid4()))
    timeline = timeline_events or []

    subject_name = subject.get("name", "")
    subject_bio = subject.get("bio") or subject.get("context") or ""

    # ── 1. Flatten profiles ─────────────────────────────────
    all_profiles: list[dict[str, Any]] = []
    for group in platform_profiles:
        all_profiles.extend(group)

    if not all_profiles:
        return [], [], {"nodes": [], "edges": []}

    # ── 2. Pairwise scoring ─────────────────────────────────
    # Score each profile against the subject
    profile_scores: list[dict[str, Any]] = []

    for profile in all_profiles:
        prof_name = (
            profile.get("display_name")
            or profile.get("name")
            or profile.get("username", "")
        )
        prof_bio = profile.get("bio", "")

        # Name similarity
        n_score = name_similarity(subject_name, prof_name)

        # Alias similarity
        subject_as_profile = {
            "name": subject_name,
            "aliases": [],
            "username": subject_name.lower().replace(" ", "_"),
        }
        a_score = alias_similarity(subject_as_profile, profile)
        n_score = max(n_score, a_score)

        # Bio similarity
        b_score = bio_similarity(subject_bio, prof_bio) if subject_bio else 0.0

        profile_scores.append({
            "profile": profile,
            "name_score": n_score,
            "bio_score": b_score,
        })

    # ── 3. Cross-platform consistency ───────────────────────
    cross_platform = _calculate_cross_platform_consistency(all_profiles)

    # ── 4. Detect conflicts ─────────────────────────────────
    conflicts = detect_conflicts(
        candidate_profiles=all_profiles,
        timeline_events=timeline,
        config=cfg.get("conflict_config"),
    )

    # ── 5 & 6. Bayesian confidence + penalties ──────────────
    # Aggregate scores across all profiles (use best scores)
    best_name = max((ps["name_score"] for ps in profile_scores), default=0.0)
    best_bio = max((ps["bio_score"] for ps in profile_scores), default=0.0)
    evidence_count = len(all_profiles)

    base_confidence, breakdown = calculate_confidence(
        name_score=best_name,
        bio_score=best_bio,
        cross_platform_consistency=cross_platform,
        evidence_count=evidence_count,
        conflict_count=len(conflicts),
        weights=weights,
        prior=prior,
    )

    # Apply severity-specific penalties
    final_confidence = apply_conflict_penalties(base_confidence, conflicts)

    # ── 7. Build candidate ──────────────────────────────────
    status = _assign_status(final_confidence, len(conflicts))

    # Build evidence objects for the candidate
    candidate_evidence: list[Evidence] = []

    candidate_evidence.append(
        build_evidence(
            claim=f"Name '{subject_name}' matches profile names",
            feature="name_match",
            raw_value=best_name,
            source_url=None,
            verification_method=(
                VerificationMethod.EXACT_MATCH if best_name > 99
                else VerificationMethod.FUZZY_MATCH
            ),
            extracted_text=f"Best name score: {best_name:.1f}%",
        )
    )

    if best_bio > 0:
        candidate_evidence.append(
            build_evidence(
                claim=f"Bio similarity across profiles",
                feature="bio_similarity",
                raw_value=best_bio,
                source_url=None,
                verification_method=VerificationMethod.TF_IDF_SIMILARITY,
                extracted_text=f"Best bio score: {best_bio:.1f}%",
            )
        )

    candidate_evidence.append(
        build_evidence(
            claim=f"Cross-platform consistency: {cross_platform:.1f}%",
            feature="cross_platform",
            raw_value=cross_platform,
            source_url=None,
            verification_method=VerificationMethod.CROSS_REFERENCE,
        )
    )

    # Convert profile dicts to PlatformProfile objects (if not already)
    platform_profile_objs: list[PlatformProfile] = []
    for p in all_profiles:
        if isinstance(p, PlatformProfile):
            platform_profile_objs.append(p)
        elif isinstance(p, dict):
            try:
                platform_profile_objs.append(PlatformProfile.model_validate(p))
            except Exception:
                # Skip profiles that don't validate
                pass

    # Build candidate aliases from all profiles
    all_aliases: list[str] = []
    for p in all_profiles:
        if isinstance(p, dict):
            aliases = p.get("aliases", [])
            username = p.get("username", "")
            display = p.get("display_name", "")
        else:
            aliases = p.aliases
            username = p.username
            display = p.display_name or ""
        all_aliases.extend(aliases)
        if username:
            all_aliases.append(username)
        if display:
            all_aliases.append(display)
    # De-duplicate
    all_aliases = list(dict.fromkeys(all_aliases))

    now = datetime.now(tz=timezone.utc)
    candidate = Candidate(
        candidate_id=str(uuid.uuid4()),
        investigation_id=investigation_id,
        rank=1,
        confidence_overall=final_confidence,
        name=subject_name,
        bio=subject_bio or None,
        aliases=all_aliases,
        profiles=platform_profile_objs,
        confidence_breakdown=breakdown,
        evidence=candidate_evidence,
        status=status,
        created_at=now,
        updated_at=now,
    )

    candidates = [candidate]

    # ── 8. Build knowledge graph ────────────────────────────
    # Convert timeline dicts to TimelineEvent objects
    timeline_objs: list[TimelineEvent] = []
    for te in timeline:
        if isinstance(te, TimelineEvent):
            timeline_objs.append(te)
        elif isinstance(te, dict):
            try:
                timeline_objs.append(TimelineEvent.model_validate(te))
            except Exception:
                pass

    graph = build_knowledge_graph(
        candidate=candidate,
        profiles=platform_profile_objs,
        timeline_events=timeline_objs,
        conflicts=conflicts,
        seed=42,
    )

    return candidates, conflicts, graph
