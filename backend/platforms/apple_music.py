# backend/platforms/apple_music.py

from typing import List, Dict, Optional
from platforms.base import MusicPlatform
from apple_music_free import AppleMusicFreeClient
from fuzzywuzzy import fuzz
import time

class AppleMusicPlatform(MusicPlatform):
    def __init__(self):
        super().__init__('apple_music')
        self.client = AppleMusicFreeClient()
    
    def extract_playlist_id(self, url: str) -> Optional[str]:
        """
        Extract playlist ID from Apple Music URL
        
        Note: Free API can't fetch playlist contents
        This is just for URL validation
        """
        import re
        # https://music.apple.com/us/playlist/name/pl.xxxxx
        match = re.search(r'playlist/[^/]+/(pl\.[a-zA-Z0-9-]+)', url)
        if match:
            return match.group(1)
        
        # Also support album URLs
        match = re.search(r'album/[^/]+/(\d+)', url)
        if match:
            return match.group(1)
        
        return None
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        """
        Fetch playlist tracks
        
        Note: Not supported with free iTunes API
        Would require MusicKit ($99/year)
        """
        raise NotImplementedError(
            "❌ Extracting Apple Music playlists requires MusicKit credentials ($99/year).\n"
            "💡 Solution: Use Spotify or YouTube Music as your source platform instead!\n"
            "   You can still convert TO Apple Music for free."
        )
    
    def search_by_isrc(self, isrc: str) -> Optional[Dict]:
        """
        Search by ISRC
        
        Note: iTunes API doesn't support ISRC search directly
        But sometimes ISRC is included in results!
        """
        # iTunes API doesn't support ISRC search
        return None
    
    def search_by_metadata(self, title: str, artist: str) -> Optional[Dict]:
        """
        Search for a track by title and artist with fuzzy matching
        """
        time.sleep(1.2) 
        # Get multiple results for better matching
        results = self.client.search_multiple(title, artist, limit=5)
        
        if not results:
            # Try simplified search (remove featuring, etc.)
            simplified_title = self._simplify_title(title)
            simplified_artist = self._simplify_artist(artist)
            
            if simplified_title != title or simplified_artist != artist:
                results = self.client.search_multiple(simplified_title, simplified_artist, limit=5)
        
        if not results:
            return None
        
        # Find best match using fuzzy matching
        best_match = None
        best_score = 0
        
        for result in results:
            # Calculate similarity scores
            title_score = fuzz.ratio(
                title.lower(),
                result['title'].lower()
            )
            artist_score = fuzz.ratio(
                artist.lower(),
                result['artist'].lower()
            )
            
            # Also try token sort ratio (handles word order differences)
            title_token_score = fuzz.token_sort_ratio(
                title.lower(),
                result['title'].lower()
            )
            artist_token_score = fuzz.token_sort_ratio(
                artist.lower(),
                result['artist'].lower()
            )
            
            # Use the better score
            title_final = max(title_score, title_token_score)
            artist_final = max(artist_score, artist_token_score)
            
            # Combined score (title weighted more)
            combined_score = (title_final * 0.6) + (artist_final * 0.4)
            
            if combined_score > best_score:
                best_score = combined_score
                best_match = result
        
        # Only return if confidence is high enough
        if best_score >= 70:  # 70% threshold
            return {
                'id': best_match['apple_music_id'],
                'title': best_match['title'],
                'artist': best_match['artist'],
                'album': best_match.get('album', ''),
                'confidence': best_score / 100,
                'apple_music_url': best_match['apple_music_url'],
                'preview_url': best_match.get('preview_url'),
                'artwork_url': best_match.get('artwork_url')
            }
        
        return None
    
    def generate_playback_link(self, track_ids: List[str]) -> str:
        """
        Generate deep link to Apple Music
        
        Note: Free API can't create playlists
        Returns link to first song
        """
        if not track_ids:
            return None
        
        # For single track
        if len(track_ids) == 1:
            return self.client.generate_deep_link(track_ids[0])
        
        # For multiple tracks, return link to first
        # User will need to manually add others
        return self.client.generate_deep_link(track_ids[0])
    
    def _simplify_title(self, title: str) -> str:
        """
        Simplify title by removing common additions
        """
        import re
        
        # Remove content in parentheses/brackets
        title = re.sub(r'\([^)]*\)', '', title)
        title = re.sub(r'\[[^\]]*\]', '', title)
        
        # Remove "feat.", "ft.", etc.
        title = re.sub(r'\s+feat\..*', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s+ft\..*', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s+featuring.*', '', title, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        title = ' '.join(title.split())
        
        return title.strip()
    
    def _simplify_artist(self, artist: str) -> str:
        """
        Simplify artist name
        """
        # Take only the first artist if multiple
        if ',' in artist:
            artist = artist.split(',')[0]
        if '&' in artist:
            artist = artist.split('&')[0]
        if ' and ' in artist.lower():
            artist = artist.lower().split(' and ')[0]
        
        return artist.strip()


# Test the platform
if __name__ == "__main__":
    print("🧪 Testing Apple Music Platform (Free)\n")
    
    platform = AppleMusicPlatform()
    
    # Test metadata search
    print("Test: Searching for track")
    result = platform.search_by_metadata("Blinding Lights", "The Weeknd")
    
    if result:
        print(f"✅ Match found!")
        print(f"   Title: {result['title']}")
        print(f"   Artist: {result['artist']}")
        print(f"   Confidence: {result['confidence']:.1%}")
        print(f"   Link: {result['apple_music_url']}")
    else:
        print("❌ No match found")
    
    print("\n" + "="*60 + "\n")
    
    # Test playlist extraction (should fail gracefully)
    print("Test: Trying to extract playlist (should fail with helpful message)")
    try:
        platform.get_playlist_tracks("pl.abc123")
    except NotImplementedError as e:
        print(f"Expected error: {e}")