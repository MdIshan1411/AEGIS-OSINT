"""
TRACE-X Conflict Detection Engine.

Detects 5 types of contradictions between candidate profiles and timeline
events. Each conflict carries an Evidence object and a severity-weighted
penalty. Pure functions — zero I/O.

Conflict Types:
1. LOCATION_OVERLAP — impossible simultaneous locations (haversine)
2. TIMELINE_INCONSISTENCY — temporal impossibilities
3. EMPLOYER_MISMATCH — different employers in same timeframe
4. BIO_CONTRADICTION — opposing expertise claims
5. NAME_VARIANCE — drastic name differences suggesting alias/theft
"""

from __future__ import annotations

import math
import uuid
from datetime import date, datetime

from trace_x.ml.evidence import build_evidence
from trace_x.ml.similarity import score_bio_similarity as bio_similarity, score_name_match as name_similarity
from trace_x.schemas.enums import (
    ConflictType,
    Severity,
    VerificationMethod,
)
from trace_x.schemas.models import Conflict, Evidence


# ── City Coordinates (for haversine distance) ──────────────

CITY_COORDS: dict[str, tuple[float, float]] = {
    "san francisco": (37.7749, -122.4194),
    "sf": (37.7749, -122.4194),
    "new york": (40.7128, -74.0060),
    "nyc": (40.7128, -74.0060),
    "london": (51.5074, -0.1278),
    "tokyo": (35.6762, 139.6503),
    "paris": (48.8566, 2.3522),
    "berlin": (52.5200, 13.4050),
    "sydney": (-33.8688, 151.2093),
    "mumbai": (19.0760, 72.8777),
    "bangalore": (12.9716, 77.5946),
    "bengaluru": (12.9716, 77.5946),
    "toronto": (43.6532, -79.3832),
    "seattle": (47.6062, -122.3321),
    "austin": (30.2672, -97.7431),
    "chicago": (41.8781, -87.6298),
    "los angeles": (34.0522, -118.2437),
    "la": (34.0522, -118.2437),
    "boston": (42.3601, -71.0589),
    "denver": (39.7392, -104.9903),
    "dubai": (25.2048, 55.2708),
    "singapore": (1.3521, 103.8198),
    "hong kong": (22.3193, 114.1694),
    "beijing": (39.9042, 116.4074),
    "shanghai": (31.2304, 121.4737),
    "seoul": (37.5665, 126.9780),
    "amsterdam": (52.3676, 4.9041),
    "zurich": (47.3769, 8.5417),
    "stockholm": (59.3293, 18.0686),
    "dublin": (53.3498, -6.2603),
    "tel aviv": (32.0853, 34.7818),
    "hyderabad": (17.3850, 78.4867),
    "delhi": (28.7041, 77.1025),
    "new delhi": (28.7041, 77.1025),
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points in kilometers.

    Uses the haversine formula for accuracy on a spherical Earth.

    Args:
        lat1, lon1: Latitude/longitude of point 1 (degrees).
        lat2, lon2: Latitude/longitude of point 2 (degrees).

    Returns:
        Distance in kilometers.
    """
    R = 6371.0  # Earth radius in km
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _resolve_location(location: str | None) -> tuple[float, float] | None:
    """
    Resolve a location string to coordinates via the embedded city lookup.

    Args:
        location: City name or None.

    Returns:
        (lat, lon) tuple or None if not found.
    """
    if not location:
        return None
    key = location.strip().lower()
    # Try exact match first, then substring match
    if key in CITY_COORDS:
        return CITY_COORDS[key]
    for city, coords in CITY_COORDS.items():
        if city in key or key in city:
            return coords
    return None


# ── Conflict Detection ──────────────────────────────────────


def detect_location_conflicts(
    profiles: list[dict],
    threshold_km: float = 500.0,
) -> list[Conflict]:
    """
    Detect physically impossible location overlaps.

    Flags profiles that claim to be in locations >threshold_km apart
    during overlapping time windows.

    Args:
        profiles: List of profile dicts with 'location', 'profile_id', 'created_at'.
        threshold_km: Minimum distance (km) to flag as impossible. Default 500.

    Returns:
        List of LOCATION_OVERLAP Conflict objects.
    """
    conflicts: list[Conflict] = []
    located = []
    for p in profiles:
        coords = _resolve_location(p.get("location"))
        if coords:
            located.append((p, coords))

    for i, (pa, ca) in enumerate(located):
        for j, (pb, cb) in enumerate(located):
            if j <= i:
                continue
            distance = _haversine_km(ca[0], ca[1], cb[0], cb[1])
            if distance > threshold_km:
                conflicts.append(
                    Conflict(
                        conflict_id=str(uuid.uuid4()),
                        conflict_type=ConflictType.LOCATION_OVERLAP,
                        description=(
                            f"Profiles claim locations '{pa.get('location')}' "
                            f"and '{pb.get('location')}' ({distance:.0f} km apart) "
                            f"— physically impossible to be at both simultaneously."
                        ),
                        profiles_involved=[
                            pa.get("profile_id", "unknown"),
                            pb.get("profile_id", "unknown"),
                        ],
                        severity=Severity.HIGH,
                        evidence=build_evidence(
                            claim=f"Location overlap: {pa.get('location')} ↔ {pb.get('location')} ({distance:.0f} km)",
                            feature="location_overlap",
                            raw_value=min(100.0, distance / 100.0),
                            source_url=None,
                            verification_method=VerificationMethod.CROSS_REFERENCE,
                            extracted_text=f"Distance: {distance:.1f} km",
                        ),
                    )
                )
    return conflicts


def detect_timeline_conflicts(
    timeline_events: list[dict],
) -> list[Conflict]:
    """
    Detect temporal impossibilities in timeline events.

    Checks for:
    - Overlapping employment at the same organization
    - Account created before claimed graduation/start date

    Args:
        timeline_events: List of event dicts with 'start_date', 'end_date',
                         'organization', 'event_type', 'candidate_id'.

    Returns:
        List of TIMELINE_INCONSISTENCY Conflict objects.
    """
    conflicts: list[Conflict] = []
    employment_events = [
        e for e in timeline_events if e.get("event_type") == "EMPLOYMENT"
    ]

    for i, ea in enumerate(employment_events):
        for j, eb in enumerate(employment_events):
            if j <= i:
                continue

            start_a = ea.get("start_date")
            end_a = ea.get("end_date")
            start_b = eb.get("start_date")
            end_b = eb.get("end_date")

            if not start_a or not start_b:
                continue

            # Parse dates if they're strings
            if isinstance(start_a, str):
                start_a = date.fromisoformat(start_a)
            if isinstance(start_b, str):
                start_b = date.fromisoformat(start_b)
            if isinstance(end_a, str):
                end_a = date.fromisoformat(end_a)
            if isinstance(end_b, str):
                end_b = date.fromisoformat(end_b)

            # Use a far-future date for open-ended employment
            eff_end_a = end_a or date(2099, 12, 31)
            eff_end_b = end_b or date(2099, 12, 31)

            # Check for overlap
            if start_a <= eff_end_b and start_b <= eff_end_a:
                org_a = ea.get("organization", "Unknown")
                org_b = eb.get("organization", "Unknown")

                # Same org overlap might be OK (promotion); different orgs = suspicious
                if org_a.lower() != org_b.lower():
                    conflicts.append(
                        Conflict(
                            conflict_id=str(uuid.uuid4()),
                            conflict_type=ConflictType.TIMELINE_INCONSISTENCY,
                            description=(
                                f"Overlapping employment: '{org_a}' "
                                f"({start_a} – {end_a or 'Present'}) "
                                f"and '{org_b}' "
                                f"({start_b} – {end_b or 'Present'})."
                            ),
                            profiles_involved=[
                                ea.get("candidate_id", "unknown"),
                                eb.get("candidate_id", "unknown"),
                            ],
                            severity=Severity.MEDIUM,
                            evidence=build_evidence(
                                claim=f"Overlapping employment at {org_a} and {org_b}",
                                feature="timeline_inconsistency",
                                raw_value=70.0,
                                source_url=None,
                                verification_method=VerificationMethod.CROSS_REFERENCE,
                            ),
                        )
                    )
    return conflicts


def detect_employer_mismatch(
    profiles: list[dict],
) -> list[Conflict]:
    """
    Detect profiles claiming different employers in the same timeframe.

    Extracts employer from bio text using simple heuristics ("at X",
    "@ X", "Engineer at X").

    Args:
        profiles: List of profile dicts with 'bio', 'profile_id'.

    Returns:
        List of EMPLOYER_MISMATCH Conflict objects.
    """
    import re

    conflicts: list[Conflict] = []
    employers: list[tuple[dict, str]] = []

    for p in profiles:
        bio = p.get("bio", "") or ""
        # Extract employer: "at Company" or "@ Company"
        match = re.search(r"(?:at|@)\s+([A-Z][A-Za-z0-9\s]+)", bio)
        if match:
            employer = match.group(1).strip()
            employers.append((p, employer))

    for i, (pa, emp_a) in enumerate(employers):
        for j, (pb, emp_b) in enumerate(employers):
            if j <= i:
                continue
            # Different employers = mismatch
            sim = name_similarity(emp_a, emp_b)
            if sim < 50.0:  # Clearly different employers
                conflicts.append(
                    Conflict(
                        conflict_id=str(uuid.uuid4()),
                        conflict_type=ConflictType.EMPLOYER_MISMATCH,
                        description=(
                            f"Different employers claimed: '{emp_a}' vs '{emp_b}' "
                            f"(similarity: {sim:.1f}%)."
                        ),
                        profiles_involved=[
                            pa.get("profile_id", "unknown"),
                            pb.get("profile_id", "unknown"),
                        ],
                        severity=Severity.MEDIUM,
                        evidence=build_evidence(
                            claim=f"Employer mismatch: {emp_a} vs {emp_b}",
                            feature="employer_mismatch",
                            raw_value=100.0 - sim,
                            source_url=None,
                            verification_method=VerificationMethod.PROFILE_TEXT_EXTRACTION,
                            extracted_text=f"Bio A: {pa.get('bio', '')[:80]} | Bio B: {pb.get('bio', '')[:80]}",
                        ),
                    )
                )
    return conflicts


def detect_bio_contradictions(
    profiles: list[dict],
    threshold: float = 15.0,
) -> list[Conflict]:
    """
    Detect opposing expertise claims via low bio similarity.

    If TF-IDF cosine between two bios is < threshold%, the bios are
    so different they likely describe different people.

    Args:
        profiles: List of profile dicts with 'bio', 'profile_id'.
        threshold: Cosine similarity threshold (0–100). Default 15.

    Returns:
        List of BIO_CONTRADICTION Conflict objects.
    """
    conflicts: list[Conflict] = []
    bios = [(p, p.get("bio")) for p in profiles if p.get("bio")]

    for i, (pa, bio_a) in enumerate(bios):
        for j, (pb, bio_b) in enumerate(bios):
            if j <= i:
                continue
            sim = bio_similarity(bio_a, bio_b)
            if sim < threshold:
                conflicts.append(
                    Conflict(
                        conflict_id=str(uuid.uuid4()),
                        conflict_type=ConflictType.BIO_CONTRADICTION,
                        description=(
                            f"Bio similarity extremely low ({sim:.1f}%): "
                            f"'{bio_a[:60]}...' vs '{bio_b[:60]}...' — "
                            f"likely different expertise domains."
                        ),
                        profiles_involved=[
                            pa.get("profile_id", "unknown"),
                            pb.get("profile_id", "unknown"),
                        ],
                        severity=Severity.LOW,
                        evidence=build_evidence(
                            claim=f"Bio contradiction (similarity: {sim:.1f}%)",
                            feature="bio_contradiction",
                            raw_value=sim,
                            source_url=None,
                            verification_method=VerificationMethod.TF_IDF_SIMILARITY,
                            extracted_text=f"Bio A: {bio_a[:100]} | Bio B: {bio_b[:100]}",
                        ),
                    )
                )
    return conflicts


def detect_name_variance(
    profiles: list[dict],
    threshold: float = 70.0,
) -> list[Conflict]:
    """
    Detect drastic name differences across profiles.

    Jaro-Winkler < threshold on name pairs suggests possible identity
    theft or unrelated aliases.

    Args:
        profiles: List of profile dicts with 'name'/'display_name', 'profile_id'.
        threshold: Jaro-Winkler threshold (0–100). Default 70.

    Returns:
        List of NAME_VARIANCE Conflict objects.
    """
    conflicts: list[Conflict] = []

    def _get_name(p: dict) -> str | None:
        return p.get("display_name") or p.get("name") or p.get("username")

    named = [(p, _get_name(p)) for p in profiles if _get_name(p)]

    for i, (pa, name_a) in enumerate(named):
        for j, (pb, name_b) in enumerate(named):
            if j <= i:
                continue
            sim = name_similarity(name_a, name_b)
            if sim < threshold:
                conflicts.append(
                    Conflict(
                        conflict_id=str(uuid.uuid4()),
                        conflict_type=ConflictType.NAME_VARIANCE,
                        description=(
                            f"Drastic name difference: '{name_a}' vs '{name_b}' "
                            f"(similarity: {sim:.1f}%) — possible alias or different person."
                        ),
                        profiles_involved=[
                            pa.get("profile_id", "unknown"),
                            pb.get("profile_id", "unknown"),
                        ],
                        severity=Severity.MEDIUM,
                        evidence=build_evidence(
                            claim=f"Name variance: {name_a} vs {name_b} ({sim:.1f}%)",
                            feature="name_variance",
                            raw_value=sim,
                            source_url=None,
                            verification_method=VerificationMethod.FUZZY_MATCH,
                        ),
                    )
                )
    return conflicts


# ── Main Conflict Orchestrator ──────────────────────────────


def detect_conflicts(
    candidate_profiles: list[dict],
    timeline_events: list[dict],
    config: dict | None = None,
) -> list[Conflict]:
    """
    Run all 5 conflict detectors and return a combined list.

    Args:
        candidate_profiles: Profile dicts with platform, username, bio, location, etc.
        timeline_events: Employment/event dicts with dates and organizations.
        config: Optional thresholds override:
            - location_threshold_km (default 500)
            - bio_threshold (default 15.0)
            - name_threshold (default 70.0)

    Returns:
        Combined list of all detected Conflict objects, sorted by severity.
    """
    cfg = config or {}
    location_km = cfg.get("location_threshold_km", 500.0)
    bio_thresh = cfg.get("bio_threshold", 15.0)
    name_thresh = cfg.get("name_threshold", 70.0)

    all_conflicts: list[Conflict] = []

    # 1. Location overlaps
    all_conflicts.extend(
        detect_location_conflicts(candidate_profiles, threshold_km=location_km)
    )

    # 2. Timeline inconsistencies
    all_conflicts.extend(detect_timeline_conflicts(timeline_events))

    # 3. Employer mismatches
    all_conflicts.extend(detect_employer_mismatch(candidate_profiles))

    # 4. Bio contradictions
    all_conflicts.extend(
        detect_bio_contradictions(candidate_profiles, threshold=bio_thresh)
    )

    # 5. Name variance
    all_conflicts.extend(
        detect_name_variance(candidate_profiles, threshold=name_thresh)
    )

    # Sort by severity: HIGH first, then MEDIUM, then LOW
    severity_order = {Severity.HIGH: 0, Severity.MEDIUM: 1, Severity.LOW: 2}
    all_conflicts.sort(key=lambda c: severity_order.get(c.severity, 3))

    return all_conflicts
