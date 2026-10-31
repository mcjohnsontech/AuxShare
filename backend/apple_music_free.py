# backend/apple_music_free.py

import requests
from urllib.parse import quote
from typing import Optional, Dict, List

class AppleMusicFreeClient:
    """
    Free Apple Music integration using iTunes Search API
    No authentication or payment required!
    """
    
    def __init__(self):
        self.base_url = "https://itunes.apple.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AuxParty/1.0'
        })
    
    def search_track(self, title: str, artist: str, limit: int = 5) -> Optional[Dict]:
        """
        Search for a track by title and artist
        
        Args:
            title: Song title
            artist: Artist name
            limit: Number of results to fetch
            
        Returns:
            Dict with track info or None if not found
        """
        query = f"{title} {artist}"
        
        try:
            url = f"{self.base_url}/search"
            params = {
                'term': query,
                'media': 'music',
                'entity': 'song',
                'limit': limit,
                'country': 'US'  # You can make this configurable
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('resultCount', 0) > 0 and data.get('results'):
                # Return the first result
                result = data['results'][0]
                
                return {
                    'apple_music_id': str(result['trackId']),
                    'title': result['trackName'],
                    'artist': result['artistName'],
                    'album': result.get('collectionName', ''),
                    'duration_ms': result.get('trackTimeMillis', 0),
                    'preview_url': result.get('previewUrl'),  # 30-second preview
                    'apple_music_url': result.get('trackViewUrl'),
                    'artwork_url': result.get('artworkUrl100', '').replace('100x100', '600x600'),
                    'release_date': result.get('releaseDate', ''),
                    'genre': result.get('primaryGenreName', ''),
                    'isrc': result.get('isrc')  # Sometimes included!
                }
            
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"❌ iTunes API error: {e}")
            return None
    
    def search_multiple(self, title: str, artist: str, limit: int = 5) -> List[Dict]:
        """
        Search and return multiple results for better matching
        
        Returns:
            List of track dictionaries
        """
        query = f"{title} {artist}"
        
        try:
            url = f"{self.base_url}/search"
            params = {
                'term': query,
                'media': 'music',
                'entity': 'song',
                'limit': limit,
                'country': 'US'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            if data.get('resultCount', 0) > 0 and data.get('results'):
                for result in data['results']:
                    results.append({
                        'apple_music_id': str(result['trackId']),
                        'title': result['trackName'],
                        'artist': result['artistName'],
                        'album': result.get('collectionName', ''),
                        'duration_ms': result.get('trackTimeMillis', 0),
                        'preview_url': result.get('previewUrl'),
                        'apple_music_url': result.get('trackViewUrl'),
                        'artwork_url': result.get('artworkUrl100', '').replace('100x100', '600x600')
                    })
            
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"❌ iTunes API error: {e}")
            return []
    
    def get_track_by_id(self, track_id: str) -> Optional[Dict]:
        """
        Get track details by Apple Music ID
        """
        try:
            url = f"{self.base_url}/lookup"
            params = {
                'id': track_id,
                'entity': 'song'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('resultCount', 0) > 0 and data.get('results'):
                result = data['results'][0]
                
                return {
                    'apple_music_id': str(result['trackId']),
                    'title': result['trackName'],
                    'artist': result['artistName'],
                    'album': result.get('collectionName', ''),
                    'duration_ms': result.get('trackTimeMillis', 0),
                    'preview_url': result.get('previewUrl'),
                    'apple_music_url': result.get('trackViewUrl'),
                    'artwork_url': result.get('artworkUrl100', '').replace('100x100', '600x600')
                }
            
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"❌ iTunes API error: {e}")
            return None
    
    def generate_deep_link(self, track_id: str) -> str:
        """
        Generate a deep link that opens Apple Music app
        """
        return f"https://music.apple.com/us/song/{track_id}"
    
    def generate_preview_player_url(self, preview_url: str) -> str:
        """
        The preview URL can be used directly in an audio player
        """
        return preview_url if preview_url else None


# Test the client
if __name__ == "__main__":
    print("🧪 Testing iTunes Search API (Free Apple Music Access)\n")
    
    client = AppleMusicFreeClient()
    
    # Test 1: Search for a popular song
    print("Test 1: Searching for 'Blinding Lights' by The Weeknd")
    result = client.search_track("Blinding Lights", "The Weeknd")
    
    if result:
        print(f"✅ Found: {result['title']} - {result['artist']}")
        print(f"   Apple Music ID: {result['apple_music_id']}")
        print(f"   Album: {result['album']}")
        print(f"   Link: {result['apple_music_url']}")
        print(f"   Preview: {result['preview_url'][:50]}...")
        print(f"   Artwork: {result['artwork_url'][:50]}...")
    else:
        print("❌ Not found")
    
    print("\n" + "="*60 + "\n")
    
    # Test 2: Search for multiple results
    print("Test 2: Getting multiple results for 'Shape of You'")
    results = client.search_multiple("Shape of You", "Ed Sheeran", limit=3)
    
    print(f"Found {len(results)} results:")
    for i, r in enumerate(results, 1):
        print(f"  {i}. {r['title']} - {r['artist']}")
    
    print("\n" + "="*60 + "\n")
    
    # Test 3: Lookup by ID
    print("Test 3: Looking up track by ID")
    track = client.get_track_by_id("1440873101")  # Blinding Lights
    
    if track:
        print(f"✅ Found by ID: {track['title']} - {track['artist']}")
    else:
        print("❌ Not found by ID")