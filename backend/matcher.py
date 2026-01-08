# backend/matcher.py

from typing import List, Dict
from spotify_client import SpotifyClient
from youtube_music_client import YouTubeMusicClient
from apple_music_client import AppleMusicClient  # Optional
import asyncio

class TrackMatcher:
    def __init__(self):
        self.spotify = SpotifyClient()
        self.youtube = YouTubeMusicClient()
        # self.apple = AppleMusicClient()  # Uncomment when ready
    
    def match_track_to_youtube(self, track: Dict) -> Dict:
        """Match a single Spotify track to YouTube Music"""
        youtube_match = self.youtube.search_track(
            track['title'],
            track['artists']
        )
        
        return {
            **track,  # Keep original Spotify data
            'youtube_music_id': youtube_match['youtube_music_id'] if youtube_match else None,
            'youtube_confidence': youtube_match['confidence'] if youtube_match else 0
        }
    
    def match_playlist(self, spotify_tracks: List[Dict]) -> List[Dict]:
        """Match entire playlist to YouTube Music"""
        matched_tracks = []
        
        print(f"Matching {len(spotify_tracks)} tracks...")
        
        for i, track in enumerate(spotify_tracks, 1):
            print(f"  [{i}/{len(spotify_tracks)}] {track['title']} - {track['artists']}")
            matched = self.match_track_to_youtube(track)
            matched_tracks.append(matched)
        
        return matched_tracks
    
    def get_match_stats(self, matched_tracks: List[Dict]) -> Dict:
        """Calculate matching statistics"""
        total = len(matched_tracks)
        matched = sum(1 for t in matched_tracks if t.get('youtube_music_id'))
        
        avg_confidence = 0
        if matched > 0:
            confidences = [t['youtube_confidence'] for t in matched_tracks if t.get('youtube_music_id')]
            avg_confidence = sum(confidences) / len(confidences)
        
        return {
            'total': total,
            'matched': matched,
            'match_rate': matched / total if total > 0 else 0,
            'avg_confidence': avg_confidence
        }

# Test it!
if __name__ == "__main__":
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