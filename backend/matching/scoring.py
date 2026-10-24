# backend/matching/scoring.py
"""Precision-first candidate scoring.

Given a canonical source track and a list of target-platform candidates, this
module ranks candidates and decides whether the best one is safe to accept.

The policy is intentionally conservative: it is better to leave a track
unmatched than to silently replace it with a live version, remix, cover, or a
different song by the same artist.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from fuzzywuzzy import fuzz

from models.canonical import CanonicalTrack
from .normalization import (
    ParsedTitle,
    normalize_text,
    parse_title,
    split_artists,
)


# A candidate needs at least this combined score to be accepted.
DEFAULT_THRESHOLD = 0.82
# Title similarity is the strongest signal; never accept on artist alone.
MIN_TITLE_SCORE = 0.85


@dataclass
class CandidateScore:
    """Scored target-platform candidate."""

    candidate: Dict[str, Any]
    title: str
    artists: List[str]
    parsed: ParsedTitle
    score: float
    title_score: float
    artist_score: float
    duration_score: Optional[float]
    accepted: bool
    flags: List[str] = field(default_factory=list)


def has_blocking_variant(track: CanonicalTrack) -> bool:
    """Return True when the source track is a non-studio variant.

    Source variants are rejected outright.  This directly protects precision
    on live/remix/acoustic/karaoke/sped-up imports.
    """
    return bool(getattr(track, "variantTags", None))


def _candidate_title(candidate: Dict[str, Any]) -> str:
    return str(
        candidate.get("title")
        or candidate.get("name")
        or candidate.get("trackName")
        or ""
    ).strip()


def _candidate_artists(candidate: Dict[str, Any]) -> List[str]:
    value = candidate.get("artists")
    if value in (None, "", []):
        value = (
            candidate.get("artist")
            or candidate.get("artistName")
            or candidate.get("artist_name")
        )
    return split_artists(value)


def _to_milliseconds(value: Any) -> Optional[int]:
    if value in (None, "", 0):
        return None
    if isinstance(value, str):
        # ``duration`` fixtures sometimes use "3:45".
        parts = value.strip().split(":")
        if len(parts) in (2, 3) and all(part.isdigit() for part in parts):
            numbers = [int(part) for part in parts]
            seconds = 0
            for number in numbers:
                seconds = seconds * 60 + number
            return seconds * 1000
        try:
            value = float(value)
        except (TypeError, ValueError):
            return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number <= 0:
        return None
    if number < 1000:
        number *= 1000
    return int(round(number))


def _candidate_duration(candidate: Dict[str, Any]) -> Optional[int]:
    return _to_milliseconds(
        candidate.get("duration_ms")
        or candidate.get("durationMs")
        or candidate.get("duration")
        or candidate.get("trackTimeMillis")
    )


def _text_similarity(first: str, second: str) -> float:
    if not first or not second:
        return 0.0
    if first == second:
        return 1.0
    scores = (
        fuzz.ratio(first, second),
        fuzz.token_sort_ratio(first, second),
        fuzz.token_set_ratio(first, second),
    )
    return max(scores) / 100.0


def _artist_similarity(
    source_artists: Iterable[str], candidate_artists: Iterable[str]
) -> float:
    source_keys = [normalize_text(name) for name in source_artists if normalize_text(name)]
    candidate_keys = [
        normalize_text(name) for name in candidate_artists if normalize_text(name)
    ]
    if not source_keys or not candidate_keys:
        return 0.0

    best = 0.0
    for source in source_keys:
        for candidate in candidate_keys:
            best = max(best, _text_similarity(source, candidate))
    return best


def _duration_similarity(source_ms: Optional[int], candidate_ms: Optional[int]) -> Optional[float]:
    if not source_ms or not candidate_ms:
        return None
    difference = abs(source_ms - candidate_ms)
    if difference <= 3_000:
        return 1.0
    if difference <= 7_000:
        return 0.9
    if difference <= 15_000:
        return 0.7
    if difference <= 30_000:
        return 0.4
    return 0.0


def _normalized_candidate(candidate: Dict[str, Any], parsed: ParsedTitle, artists: List[str]) -> Dict[str, Any]:
    normalized = dict(candidate)
    normalized["title"] = _candidate_title(candidate)
    normalized["artists"] = list(artists)
    if not normalized.get("artist") and artists:
        normalized["artist"] = artists[0]
    normalized["duration_ms"] = _candidate_duration(candidate)
    return normalized


def score_candidate(
    source: CanonicalTrack,
    candidate: Dict[str, Any],
    threshold: float = DEFAULT_THRESHOLD,
) -> CandidateScore:
    """Score one candidate against *source* and decide whether it is safe."""
    title = _candidate_title(candidate)
    artists = _candidate_artists(candidate)
    parsed = parse_title(title, artists)

    flags: List[str] = []
    candidate_title_key = normalize_text(parsed.base_title)
    source_title_key = normalize_text(source.baseTitle or source.title)

    if not candidate_title_key:
        return CandidateScore(
            candidate=_normalized_candidate(candidate, parsed, artists),
            title=title,
            artists=artists,
            parsed=parsed,
            score=0.0,
            title_score=0.0,
            artist_score=0.0,
            duration_score=None,
            accepted=False,
            flags=["empty_title"],
        )

    title_score = _text_similarity(source_title_key, candidate_title_key)
    if source_title_key == candidate_title_key:
        flags.append("title_exact")

    source_artists = list(source.primaryArtists) + list(source.featuredArtists)
    if not source_artists:
        source_artists = list(source.artists)
    artist_score = _artist_similarity(source_artists, artists)
    if artist_score >= 0.99:
        flags.append("artist_exact")

    duration_score = _duration_similarity(source.durationMs, _candidate_duration(candidate))
    if duration_score is not None and duration_score >= 0.9:
        flags.append("duration_close")

    if duration_score is None:
        score = (title_score * 0.66) + (artist_score * 0.34)
    else:
        score = (
            (title_score * 0.62)
            + (artist_score * 0.30)
            + (duration_score * 0.08)
        )

    accepted = title_score >= MIN_TITLE_SCORE and score >= threshold

    # Any tagged variant candidate (live, remix, acoustic, ...) is unsafe when
    # the source is a studio recording.  Source variants are rejected before
    # candidates are even requested.
    if parsed.variant_tags:
        flags.append("variant_conflict")
        for tag in parsed.variant_tags:
            flags.append(f"variant_{tag}")
        accepted = False
        score = min(score, 0.5)

    if artist_score < 0.45:
        flags.append("artist_mismatch")
        accepted = False

    if title_score < MIN_TITLE_SCORE:
        flags.append("title_mismatch")

    return CandidateScore(
        candidate=_normalized_candidate(candidate, parsed, artists),
        title=title,
        artists=artists,
        parsed=parsed,
        score=round(score, 4),
        title_score=round(title_score, 4),
        artist_score=round(artist_score, 4),
        duration_score=duration_score,
        accepted=accepted,
        flags=flags,
    )


def rank_candidates(
    source: CanonicalTrack,
    candidates: Iterable[Any],
    threshold: float = DEFAULT_THRESHOLD,
) -> List[CandidateScore]:
    """Score and rank candidates, best first."""
    scored: List[CandidateScore] = []
    for candidate in candidates or []:
        if candidate is None:
            continue
        if hasattr(candidate, "model_dump"):
            candidate = candidate.model_dump()
        if not isinstance(candidate, dict):
            continue
        scored.append(score_candidate(source, candidate, threshold=threshold))
    scored.sort(key=lambda item: item.score, reverse=True)
    return scored


def best_candidate(
    source: CanonicalTrack,
    candidates: Iterable[Any],
    threshold: float = DEFAULT_THRESHOLD,
) -> Optional[CandidateScore]:
    """Return the highest-scoring accepted candidate, if any."""
    for scored in rank_candidates(source, candidates, threshold=threshold):
        if scored.accepted:
            return scored
    return None
