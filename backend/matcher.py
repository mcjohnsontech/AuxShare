# backend/matcher.py
"""Legacy track matcher retained for the CLI/demo entry point.

The production conversion path lives in :class:`platforms.base.MusicPlatform`
and uses the shared precision-first scoring in :mod:`matching`.  This module
wraps the same logic for ad-hoc Spotify -> YouTube Music matching.
"""

from typing import Dict, List, Optional

from matching import (
    best_candidate,
    canonical_from_track,
    has_blocking_variant,
)
from youtube_music_client import YouTubeMusicClient


class TrackMatcher:
    def __init__(self):
        self.youtube = YouTubeMusicClient()

    def match_track_to_youtube(self, track: Dict) -> Dict:
        """Match a single Spotify track to YouTube Music."""
        canonical = canonical_from_track(track)

        if has_blocking_variant(canonical):
            return {
                **track,
                'youtube_music_id': None,
                'youtube_confidence': 0,
            }

        title = canonical.baseTitle or canonical.title
        artist = ", ".join(canonical.primaryArtists or canonical.artists)
        candidates = self.youtube.search_candidates(title, artist)
        best = best_candidate(canonical, candidates)

        if best is None:
            return {
                **track,
                'youtube_music_id': None,
                'youtube_confidence': 0,
            }

        return {
            **track,
            'youtube_music_id': best.candidate.get('id'),
            'youtube_confidence': best.score,
            'youtube_match_method': 'metadata',
            'base_title': canonical.baseTitle,
        }

    def match_playlist(self, spotify_tracks: List[Dict]) -> List[Dict]:
        """Match an entire playlist to YouTube Music."""
        matched_tracks = []

        print(f"Matching {len(spotify_tracks)} tracks...")

        for i, track in enumerate(spotify_tracks, 1):
            canonical = canonical_from_track(track)
            artist = ", ".join(canonical.primaryArtists or canonical.artists)
            print(f"  [{i}/{len(spotify_tracks)}] {canonical.title} - {artist}")
            matched = self.match_track_to_youtube(track)
            matched_tracks.append(matched)

        return matched_tracks

    def get_match_stats(self, matched_tracks: List[Dict]) -> Dict:
        """Calculate matching statistics."""
        total = len(matched_tracks)
        matched = sum(1 for t in matched_tracks if t.get('youtube_music_id'))

        avg_confidence = 0
        if matched > 0:
            confidences = [
                t['youtube_confidence']
                for t in matched_tracks
                if t.get('youtube_music_id')
            ]
            avg_confidence = sum(confidences) / len(confidences)

        return {
            'total': total,
            'matched': matched,
            'match_rate': matched / total if total > 0 else 0,
            'avg_confidence': avg_confidence,
        }


# Test it!
if __name__ == "__main__":
    from spotify_client import SpotifyClient

    matcher = TrackMatcher()
    spotify = SpotifyClient()

    # Get a playlist
    playlist_id = spotify.extract_playlist_id(
        "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
    )
    tracks = spotify.get_playlist_tracks(playlist_id)[:10]  # Test with first 10

    # Match to YouTube Music
    matched = matcher.match_playlist(tracks)
    stats = matcher.get_match_stats(matched)

    print(f"\n📊 Match Statistics:")
    print(f"Total tracks: {stats['total']}")
    print(f"Matched: {stats['matched']}")
    print(f"Match rate: {stats['match_rate']:.1%}")
    print(f"Avg confidence: {stats['avg_confidence']:.1%}")
