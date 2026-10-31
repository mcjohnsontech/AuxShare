# backend/platforms/base.py

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any

from matching import (
    best_candidate,
    canonical_from_track,
    has_blocking_variant,
    score_candidate,
    split_artists,
)

class MusicPlatform(ABC):
    """Base class for all music platform integrations"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def extract_playlist_id(self, url: str) -> Optional[str]:
        """Extract playlist ID from URL"""
        pass
    
    @abstractmethod
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        """Get all tracks from a playlist"""
        pass
    
    @abstractmethod
    def search_by_isrc(self, isrc: str) -> Optional[Dict]:
        """Search for a track by ISRC code"""
        pass
    
    @abstractmethod
    def search_by_metadata(self, title: str, artist: str) -> Optional[Dict]:
        """Search for a track by title and artist"""
        pass
    
    @abstractmethod
    def generate_playback_link(self, track_ids: List[str]) -> str:
        """Generate a link to play these tracks"""
        pass
    
    def create_playlist(self, access_token: str, name: str, description: str = "") -> str:
        raise NotImplementedError
    
    def add_tracks_to_playlist(self, access_token: str, playlist_id: str, track_uris: List[str]):
        raise NotImplementedError
    
    def find_playlist_by_marker(self, access_token: str, marker: str):
        return None

    def search_candidates(self, title: str, artist: str, limit: int = 10) -> List[Dict]:
        """Return candidate tracks for scoring.

        Adapters should override this to return several results rather than a
        single fuzzy "best guess".  The default keeps custom/legacy adapters
        working through the metadata-search fallback in :meth:`match_track`.
        """
        return []

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------

    def _format_match(
        self,
        candidate: Dict,
        confidence: float,
        match_method: str,
        score: float,
        flags: List[str],
    ) -> Dict:
        """Build the legacy-compatible match payload consumed by the API/UI."""
        result = dict(candidate)
        artists = split_artists(result.get("artists") or result.get("artist"))
        candidate_id = (
            result.get("id")
            or result.get("targetId")
            or result.get(f"{self.name}_id")
        )

        result["id"] = str(candidate_id) if candidate_id is not None else None
        result["title"] = result.get("title") or result.get("name") or ""
        result["artists"] = artists
        result["artist"] = artists[0] if artists else ""
        result["confidence"] = round(float(confidence), 4)
        result["match_method"] = match_method
        result["score"] = round(float(score), 4)
        result["flags"] = list(flags)
        return result

    def _score_isrc_result(self, canonical, result: Dict):
        """Validate an ISRC lookup against the source metadata.

        ISRC is normally authoritative, but recorded catalogues occasionally
        contain bad mappings.  Requiring the returned title/artist to resemble
        the source protects against those without giving up the fast path.
        """
        scored = score_candidate(canonical, result, threshold=0.5)
        if scored.parsed.variant_tags:
            return None
        if scored.title_score < 0.6 or scored.artist_score < 0.6:
            return None
        return scored

    def match_track(self, track: Any, market: str = "US") -> Optional[Dict]:
        """
        Match a track from another platform to this platform.

        The source is converted to a canonical representation first.  Variant
        recordings (live, remix, acoustic, ...) are rejected outright, ISRC is
        used as a validated fast path, and metadata candidates are ranked with
        a precision-first score.
        """
        canonical = canonical_from_track(track)

        # Precision-first: never try to map a live/remix/etc. source onto a
        # studio track.  Leaving it unmatched is safer than a wrong song.
        if has_blocking_variant(canonical):
            return None

        # Check negative cache
        try:
            from cache.mapping_cache import MappingCache
            cache = MappingCache()
            if canonical.isrc and cache.is_negative(canonical.isrc, self.name, market):
                return None
        except Exception:
            pass

        # Try ISRC first (most accurate), but only when the returned metadata
        # is consistent with the source.
        if canonical.isrc:
            isrc_result = self.search_by_isrc(canonical.isrc)
            if isrc_result:
                scored = self._score_isrc_result(canonical, isrc_result)
                if scored is not None:
                    flags = ["isrc"] + list(scored.flags)
                    try:
                        from cache.mapping_cache import MappingCache
                        cache = MappingCache()
                        if isrc_result.get('id'):
                            cache.set_positive(canonical.isrc, self.name, market, isrc_result['id'])
                    except Exception:
                        pass
                    return self._format_match(
                        isrc_result,
                        confidence=1.0,
                        match_method="isrc",
                        score=scored.score,
                        flags=flags,
                    )
                try:
                    from cache.mapping_cache import MappingCache
                    cache = MappingCache()
                    if isrc_result.get('id'):
                        cache.set_positive(canonical.isrc, self.name, market, isrc_result['id'])
                except Exception:
                    pass
            else:
                try:
                    from cache.mapping_cache import MappingCache
                    cache = MappingCache()
                    cache.set_negative(canonical.isrc, self.name, market)
                except Exception:
                    pass

        title = canonical.baseTitle or canonical.title
        artists = canonical.primaryArtists or canonical.artists
        artist_query = ", ".join(artists)

        candidates = self.search_candidates(title, artist_query)
        best = best_candidate(canonical, candidates)
        if best is not None:
            try:
                from cache.mapping_cache import MappingCache
                cache = MappingCache()
                if canonical.isrc and best.candidate.get('id'):
                    cache.set_positive(canonical.isrc, self.name, market, best.candidate['id'])
            except Exception:
                pass
            return self._format_match(
                best.candidate,
                confidence=best.score,
                match_method="metadata",
                score=best.score,
                flags=best.flags,
            )

        # Backwards-compatible fallback for adapters that only implement the
        # legacy single-result metadata search.  It is still scored with the
        # same precision-first rules before being accepted.
        if not candidates:
            legacy_result = self.search_by_metadata(title, artist_query)
            if legacy_result:
                scored = score_candidate(canonical, legacy_result)
                if scored.accepted:
                    return self._format_match(
                        legacy_result,
                        confidence=scored.score,
                        match_method="metadata",
                        score=scored.score,
                        flags=scored.flags,
                    )

        return None
