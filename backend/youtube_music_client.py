# backend/youtube_music_client.py

from ytmusicapi import YTMusic
from fuzzywuzzy import fuzz

class YouTubeMusicClient:
    def __init__(self):
        """Initialize YouTube Music client"""
        # No authentication needed for search!
        self.ytmusic = YTMusic()
    
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