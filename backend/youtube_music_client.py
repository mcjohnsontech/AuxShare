# backend/youtube_music_client.py

from ytmusicapi import YTMusic
from fuzzywuzzy import fuzz

class YouTubeMusicClient:
    def __init__(self):
        """Initialize YouTube Music client"""
        # No authentication needed for search!
        self.ytmusic = YTMusic()

    @staticmethod
    def _parse_duration_ms(result):
        seconds = result.get('duration_seconds')
        if not seconds and result.get('duration'):
            duration = str(result['duration'])
            try:
                parts = [int(part) for part in duration.split(':')]
                seconds = 0
                for part in parts:
                    seconds = seconds * 60 + part
            except (TypeError, ValueError):
                seconds = None
        return int(seconds * 1000) if seconds else None

    def search_candidates(self, title, artist, limit=10):
        """Return several search results so the matcher can rank them."""
        query = f"{title} {artist}".strip()
        results = self.ytmusic.search(query, filter='songs', limit=limit) or []

        candidates = []
        for result in results:
            video_id = result.get('videoId')
            if not video_id:
                continue
            artists = [
                item.get('name')
                for item in result.get('artists', [])
                if isinstance(item, dict) and item.get('name')
            ]
            album = result.get('album') or {}
            candidates.append({
                'id': video_id,
                'title': result.get('title', ''),
                'artists': artists,
                'album': album.get('name', '') if isinstance(album, dict) else '',
                'duration_ms': self._parse_duration_ms(result),
                'url': f"https://music.youtube.com/watch?v={video_id}",
                'raw': result,
            })
        return candidates
    
    def search_track(self, title, artist):
        """Search for a track on YouTube Music"""
        query = f"{title} {artist}"
        results = self.ytmusic.search(query, filter='songs', limit=5)
        
        if not results:
            return None
        
        # Find best match using fuzzy string matching
        best_match = None
        best_score = 0
        
        for result in results:
            result_title = result.get('title', '')
            result_artist = result.get('artists', [{}])[0].get('name', '')
            
            # Calculate similarity scores
            title_score = fuzz.ratio(title.lower(), result_title.lower())
            artist_score = fuzz.ratio(artist.lower(), result_artist.lower())
            
            # Combined score (title weighted more)
            combined_score = (title_score * 0.6) + (artist_score * 0.4)
            
            if combined_score > best_score:
                best_score = combined_score
                best_match = result
        
        # Only return if confidence is high enough
        if best_score > 70:  # 70% threshold
            return {
                'youtube_music_id': best_match['videoId'],
                'title': best_match['title'],
                'artists': best_match['artists'][0]['name'],
                'album': best_match.get('album', {}).get('name', ''),
                'confidence': best_score / 100
            }
        
        return None

# Test it!
if __name__ == "__main__":
    client = YouTubeMusicClient()
    
    result = client.search_track("Blinding Lights", "The Weeknd")
    
    if result:
        print(f"Found: {result['title']} - {result['artists']}")
        print(f"YouTube Music ID: {result['youtube_music_id']}")
        print(f"Confidence: {result['confidence']:.2%}")