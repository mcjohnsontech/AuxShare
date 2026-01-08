
from dotenv import load_dotenv
import os 
import spotipy 
from spotipy.oauth2 import SpotifyClientCredentials
# Load environment variables from .env file

load_dotenv()
print("SPOTIPY_CLIENT_ID:", os.getenv("SPOTIPY_CLIENT_ID"))
print("SPOTIPY_CLIENT_SECRET:", "SET" if os.getenv("SPOTIPY_CLIENT_SECRET") else "MISSING")

class SpotifyClient: 
    def __init__(self):
        """Initialize the Spotify client with credentials from environment variables."""
        client_id = os.getenv("SPOTIPY_CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
        
        # Client Credentials Flow (No user authorization required)
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        self.sp = spotipy.Spotify(auth_manager=auth_manager)

    def extract_playlist_id(self, url):
        """Extract the playlist ID from a Spotify playlist URL."""
        import re

        patterns = [
            r'spotify\.com/playlist/([a-zA-Z0-9]+)',
            r'spotify:playlist:([a-zA-Z0-9]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None

    def get_playlist_tracks(self, playlist_id):
        """Fetch all tracks from a playlist"""
        results = self.sp.playlist_tracks(playlist_id)
        tracks = []

        while results: 
            for item in results['items']:
                track = item['track']
                if track: 
                    tracks.append({
                        'title': track['name'],
                        'artists': track['artists'][0]['name'],
                        'album': track['album']['name'],
                        'isrc': track['external_ids'].get('isrc'),
                        'spotify_id': track['id'],
                        'duration_ms': track['duration_ms'] 
                    })

            # FIX: This must be OUTSIDE the 'for' loop, but inside the 'while' loop
            results = self.sp.next(results) if results['next'] else None

        return tracks
        # Testing 
if __name__ == "__main__":
    client = SpotifyClient()
    
    #Test with a playlist URL
    # test_url = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
    test_url = "https://open.spotify.com/playlist/0nD8xTksVfk5ToiPi8C9GJ"

    playlist_id = client.extract_playlist_id(test_url)

    print(f"Extracted Playlist ID: {playlist_id}")

    tracks = client.get_playlist_tracks(playlist_id)
    print(f"\nFound {len(tracks)} tracks:")

    for i, track in enumerate(tracks[:5], 1): #show first 5 tracks
        print(f"{i}. {track['title']} - {track['artists']}")
        if track['isrc']:
            print(f"   ISRC: {track['isrc']}")