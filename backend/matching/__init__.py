# backend/matching/__init__.py
"""Canonical track normalization and precision-first matching helpers."""

from .normalization import (
    ParsedTitle,
    canonical_from_track,
    normalize_text,
    parse_title,
    split_artists,
    strip_artist_prefix,
)
from .scoring import (
    DEFAULT_THRESHOLD,
    MIN_TITLE_SCORE,
    CandidateScore,
    best_candidate,
    has_blocking_variant,
    rank_candidates,
    score_candidate,
)

__all__ = [
    "DEFAULT_THRESHOLD",
    "MIN_TITLE_SCORE",
    "CandidateScore",
    "ParsedTitle",
    "best_candidate",
    "canonical_from_track",
    "has_blocking_variant",
    "normalize_text",
    "parse_title",
    "rank_candidates",
    "score_candidate",
    "split_artists",
    "strip_artist_prefix",
]
