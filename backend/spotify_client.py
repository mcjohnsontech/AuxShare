
from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
# Load environment variables from .env file

load_dotenv()


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
        try:
            results = self.sp.playlist_tracks(playlist_id)
        except Exception as e:
            error_msg = str(e)
            # Spotipy wraps HTTP errors; check for 404 / not found
            if "404" in error_msg or "not found" in error_msg.lower() or "Resource not found" in error_msg:
                raise ValueError(
                    "This Spotify playlist could not be accessed. "
                    "It may be private, region-restricted, or an editorial/algorithmic playlist "
                    "that isn't accessible with this API. Try a user-created playlist or a different source."
                )
            raise
        tracks = []

        while results:
            for item in results['items']:
                track = item.get('track') if isinstance(item, dict) else None
                if track:
                    try:
                        artist = track['artists'][0]['name']
                        tracks.append({
                            'title': track['name'],
                            'artist': artist,
                            'artists': artist,
                            'album': track['album']['name'],
                            'isrc': track.get('external_ids', {}).get('isrc') if isinstance(track.get('external_ids'), dict) else None,
                            'spotify_id': track['id'],
                            'duration_ms': track['duration_ms']
                        })
                    except Exception:
                        continue

            # FIX: This must be OUTSIDE the 'for' loop, but inside the 'while' loop
            try:
                results = self.sp.next(results) if results and results.get('next') else None
            except Exception:
                break

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