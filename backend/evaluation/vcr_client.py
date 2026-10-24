# backend/evaluation/vcr_client.py
import json
import os
from typing import Dict, Any, Optional, List

from matching import normalize_text


class VCRReplayContext:
    """
    Context manager that intercepts external platform searches
    and serves recorded fixtures to ensure reproducible, zero-quota-burning
    dry runs.

    Synthetic fixtures are checked before live recordings.  They are the
    canonical evaluation catalogue and contain the IDs the harness expects;
    live recordings are retained as a fallback for keys that were never
    synthesized.
    """
    def __init__(self, fixtures_dir: Optional[str] = None):
        if not fixtures_dir:
            fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        self.fixtures_dir = fixtures_dir
        
        # Load synthetic baseline fixtures
        self.spotify_fixtures = self._load_json("spotify_search_fixtures.json")
        self.youtube_fixtures = self._load_json("youtube_search_fixtures.json")
        self.itunes_fixtures = self._load_json("itunes_search_fixtures.json")
        
        # Load live-recorded fixtures
        self.live_fixtures = self._load_json("live_recorded_fixtures.json")
        self.spotify_live = self.live_fixtures.get("spotify", {})
        self.itunes_live = self.live_fixtures.get("itunes", {})
        
        self._orig_sp_search = None
        self._orig_yt_client_search = None
        self._orig_itunes_client_search = None
        self._orig_sp_candidates = None
        self._orig_yt_candidates = None
        self._orig_apple_candidates = None
        
    def _load_json(self, filename: str) -> Dict[str, Any]:
        path = os.path.join(self.fixtures_dir, filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    # ------------------------------------------------------------------
    # Fixture shape helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _spotify_items(value: Any) -> List[Dict[str, Any]]:
        if not isinstance(value, dict):
            return []
        tracks = value.get("tracks", value)
        if isinstance(tracks, dict):
            return tracks.get("items") or []
        if isinstance(tracks, list):
            return tracks
        return []

    @staticmethod
    def _youtube_items(value: Any) -> List[Dict[str, Any]]:
        return value if isinstance(value, list) else []

    @staticmethod
    def _itunes_results(value: Any) -> List[Dict[str, Any]]:
        if not isinstance(value, dict):
            return []
        data = value.get("data", value)
        if isinstance(data, dict):
            return data.get("results") or []
        return []

    @staticmethod
    def _matching_keys(
        mapping: Dict[str, Any], title: str, artist: str
    ) -> List[Any]:
        """Find fixture values whose key resembles title + artist.

        Fixture keys are human-readable strings (``"track:Title artist:Artist"``
        or ``"Title Artist"``).  A normalized token-subset comparison lets the
        matcher query with a cleaned title (``Yellow``) while still finding the
        fixture captured for a noisy display title (``Coldplay - Yellow
        (Official Audio)``).
        """
        query_tokens = set(normalize_text(f"{title} {artist}").split())
        if not query_tokens:
            return []

        matches: List[Any] = []
        for key, value in mapping.items():
            if key.startswith("isrc:"):
                continue
            key_tokens = set(normalize_text(key).split())
            if not key_tokens:
                continue
            intersection = query_tokens & key_tokens
            if not intersection:
                continue
            coverage = len(intersection) / len(query_tokens)
            subset = query_tokens.issubset(key_tokens) or key_tokens.issubset(
                query_tokens
            )
            if subset or coverage >= 0.75:
                matches.append(value)
        return matches

    @staticmethod
    def _spotify_candidate(item: Dict[str, Any]) -> Dict[str, Any]:
        album = item.get("album") or {}
        external_ids = item.get("external_ids") or {}
        artists = [
            artist.get("name")
            for artist in item.get("artists", [])
            if isinstance(artist, dict) and artist.get("name")
        ]
        track_id = item.get("id")
        return {
            "id": track_id,
            "title": item.get("name", ""),
            "artists": artists,
            "album": album.get("name", "") if isinstance(album, dict) else "",
            "duration_ms": item.get("duration_ms"),
            "isrc": external_ids.get("isrc")
            if isinstance(external_ids, dict)
            else None,
            "url": f"https://open.spotify.com/track/{track_id}" if track_id else None,
            "raw": item,
        }

    @staticmethod
    def _youtube_candidate(item: Dict[str, Any]) -> Dict[str, Any]:
        album = item.get("album") or {}
        video_id = item.get("videoId")
        return {
            "id": video_id,
            "title": item.get("title", ""),
            "artists": [
                artist.get("name")
                for artist in item.get("artists", [])
                if isinstance(artist, dict) and artist.get("name")
            ],
            "album": album.get("name", "") if isinstance(album, dict) else "",
            "duration_ms": item.get("duration_ms"),
            "url": f"https://music.youtube.com/watch?v={video_id}" if video_id else None,
            "raw": item,
        }

    @staticmethod
    def _itunes_candidate(item: Dict[str, Any]) -> Dict[str, Any]:
        track_id = item.get("trackId")
        return {
            "id": str(track_id) if track_id is not None else None,
            "title": item.get("trackName", ""),
            "artists": [item.get("artistName")] if item.get("artistName") else [],
            "album": item.get("collectionName", ""),
            "duration_ms": item.get("trackTimeMillis"),
            "url": item.get("trackViewUrl"),
            "apple_music_url": item.get("trackViewUrl"),
            "preview_url": item.get("previewUrl"),
            "artwork_url": item.get("artworkUrl100", ""),
            "raw": item,
        }

    # ------------------------------------------------------------------
    # Legacy single-result search mocks
    # ------------------------------------------------------------------

    def mock_spotify_search(self, q: str, type: str = "track", limit: int = 1, market: Optional[str] = None) -> Dict[str, Any]:
        clean_q = q.strip()
        # Synthetic fixtures are canonical for evaluation; fall back to live.
        if clean_q in self.spotify_fixtures:
            return self.spotify_fixtures[clean_q]
        if clean_q in self.spotify_live:
            item = self.spotify_live[clean_q]
            tracks_data = item.get("tracks", item)
            return {"tracks": tracks_data} if "items" in tracks_data else tracks_data
        return {"tracks": {"items": []}}

    def mock_ytmusic_search(self, query: str, filter: str = "songs", limit: int = 5) -> List[Dict[str, Any]]:
        clean_q = query.strip()
        if clean_q in self.youtube_fixtures:
            return self.youtube_fixtures[clean_q]
        return []

    def mock_itunes_search(self, title: str, artist: str, limit: int = 5) -> List[Dict[str, Any]]:
        query = f"{title} {artist}".strip()
        
        # Check synthetic fixtures first, then live recordings.
        fixture = self.itunes_fixtures.get(query)
        if fixture:
            raw = fixture
        elif query in self.itunes_live:
            raw = self.itunes_live[query].get("data", {})
        else:
            return []

        results = []
        for item in raw.get("results", []):
            results.append({
                "apple_music_id": str(item.get("trackId")),
                "title": item.get("trackName"),
                "artist": item.get("artistName"),
                "album": item.get("collectionName", ""),
                "duration_ms": item.get("trackTimeMillis", 0),
                "preview_url": item.get("previewUrl"),
                "apple_music_url": item.get("trackViewUrl"),
                "artwork_url": item.get("artworkUrl100", "")
            })
        return results

    # ------------------------------------------------------------------
    # Candidate search mocks
    # ------------------------------------------------------------------

    def mock_spotify_candidates(self, title: str, artist: str, limit: int = 10) -> List[Dict[str, Any]]:
        values = self._matching_keys(self.spotify_fixtures, title, artist)
        values += self._matching_keys(self.spotify_live, title, artist)

        candidates: List[Dict[str, Any]] = []
        seen = set()
        for value in values:
            for item in self._spotify_items(value):
                candidate = self._spotify_candidate(item)
                if candidate["id"] and candidate["id"] not in seen:
                    seen.add(candidate["id"])
                    candidates.append(candidate)
                if len(candidates) >= limit:
                    return candidates
        return candidates

    def mock_youtube_candidates(self, title: str, artist: str, limit: int = 10) -> List[Dict[str, Any]]:
        values = self._matching_keys(self.youtube_fixtures, title, artist)
        candidates: List[Dict[str, Any]] = []
        seen = set()
        for value in values:
            for item in self._youtube_items(value):
                candidate = self._youtube_candidate(item)
                if candidate["id"] and candidate["id"] not in seen:
                    seen.add(candidate["id"])
                    candidates.append(candidate)
                if len(candidates) >= limit:
                    return candidates
        return candidates

    def mock_itunes_candidates(self, title: str, artist: str, limit: int = 10) -> List[Dict[str, Any]]:
        values = self._matching_keys(self.itunes_fixtures, title, artist)
        values += self._matching_keys(self.itunes_live, title, artist)

        candidates: List[Dict[str, Any]] = []
        seen = set()
        for value in values:
            for item in self._itunes_results(value):
                candidate = self._itunes_candidate(item)
                if candidate["id"] and candidate["id"] not in seen:
                    seen.add(candidate["id"])
                    candidates.append(candidate)
                if len(candidates) >= limit:
                    return candidates
        return candidates

    def __enter__(self):
        from platforms.spotify import SpotifyPlatform
        from platforms.youtube_music import YouTubeMusicPlatform
        from platforms.apple_music import AppleMusicPlatform
        from apple_music_free import AppleMusicFreeClient
        from youtube_music_client import YouTubeMusicClient
        
        self._orig_sp_search = SpotifyPlatform.search_by_isrc, SpotifyPlatform.search_by_metadata
        self._orig_yt_client_search = YouTubeMusicClient.search_track
        self._orig_itunes_client_search = AppleMusicFreeClient.search_multiple
        self._orig_sp_candidates = SpotifyPlatform.search_candidates
        self._orig_yt_candidates = YouTubeMusicPlatform.search_candidates
        self._orig_apple_candidates = AppleMusicPlatform.search_candidates
        
        vcr = self
        
        def mock_sp_isrc(self_sp, isrc: str):
            res = vcr.mock_spotify_search(f"isrc:{isrc}", type="track", limit=1)
            items = res.get("tracks", {}).get("items", [])
            if items:
                track = items[0]
                return {
                    "id": track["id"],
                    "title": track["name"],
                    "artist": track["artists"][0]["name"]
                }
            return None

        def mock_sp_meta(self_sp, title: str, artist: str):
            query = f"track:{title} artist:{artist}"
            res = vcr.mock_spotify_search(query, type="track", limit=1)
            items = res.get("tracks", {}).get("items", [])
            if items:
                track = items[0]
                return {
                    "id": track["id"],
                    "title": track["name"],
                    "artist": track["artists"][0]["name"],
                    "confidence": 0.8
                }
            return None

        def mock_yt_search_track(self_yt, title: str, artist: str):
            query = f"{title} {artist}"
            results = vcr.mock_ytmusic_search(query)
            if not results:
                return None
            from fuzzywuzzy import fuzz
            best_match = None
            best_score = 0
            for r in results:
                t_score = fuzz.ratio(title.lower(), r.get("title", "").lower())
                a_name = r.get("artists", [{}])[0].get("name", "")
                a_score = fuzz.ratio(artist.lower(), a_name.lower())
                combined = (t_score * 0.6) + (a_score * 0.4)
                if combined > best_score:
                    best_score = combined
                    best_match = r
            if best_score > 70 and best_match:
                return {
                    "youtube_music_id": best_match["videoId"],
                    "title": best_match["title"],
                    "artists": best_match["artists"][0]["name"],
                    "album": best_match.get("album", {}).get("name", ""),
                    "confidence": best_score / 100
                }
            return None

        def mock_itunes_search_multiple(self_it, title: str, artist: str, limit: int = 5):
            return vcr.mock_itunes_search(title, artist, limit=limit)

        def mock_sp_candidates(self_sp, title: str, artist: str, limit: int = 10):
            return vcr.mock_spotify_candidates(title, artist, limit=limit)

        def mock_yt_candidates(self_yt, title: str, artist: str, limit: int = 10):
            return vcr.mock_youtube_candidates(title, artist, limit=limit)

        def mock_apple_candidates(self_apple, title: str, artist: str, limit: int = 10):
            return vcr.mock_itunes_candidates(title, artist, limit=limit)

        SpotifyPlatform.search_by_isrc = mock_sp_isrc
        SpotifyPlatform.search_by_metadata = mock_sp_meta
        YouTubeMusicClient.search_track = mock_yt_search_track
        AppleMusicFreeClient.search_multiple = mock_itunes_search_multiple
        SpotifyPlatform.search_candidates = mock_sp_candidates
        YouTubeMusicPlatform.search_candidates = mock_yt_candidates
        AppleMusicPlatform.search_candidates = mock_apple_candidates
        
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        from platforms.spotify import SpotifyPlatform
        from platforms.youtube_music import YouTubeMusicPlatform
        from platforms.apple_music import AppleMusicPlatform
        from apple_music_free import AppleMusicFreeClient
        from youtube_music_client import YouTubeMusicClient
        
        if self._orig_sp_search:
            SpotifyPlatform.search_by_isrc, SpotifyPlatform.search_by_metadata = self._orig_sp_search
        if self._orig_yt_client_search:
            YouTubeMusicClient.search_track = self._orig_yt_client_search
        if self._orig_itunes_client_search:
            AppleMusicFreeClient.search_multiple = self._orig_itunes_client_search
        if self._orig_sp_candidates:
            SpotifyPlatform.search_candidates = self._orig_sp_candidates
        if self._orig_yt_candidates:
            YouTubeMusicPlatform.search_candidates = self._orig_yt_candidates
        if self._orig_apple_candidates:
            AppleMusicPlatform.search_candidates = self._orig_apple_candidates
