# backend/platforms/spotify.py

import re
from typing import List, Dict, Optional
from .base import MusicPlatform
from spotify_client import SpotifyClient

class SpotifyPlatform(MusicPlatform):
    def __init__(self):
        super().__init__('spotify')
        self.client = SpotifyClient()
    
    def extract_playlist_id(self, url: str) -> Optional[str]:
        return self.client.extract_playlist_id(url)
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        return self.client.get_playlist_tracks(playlist_id)
    
    def search_by_isrc(self, isrc: str) -> Optional[Dict]:
        results = self.client.sp.search(q=f'isrc:{isrc}', type='track', limit=1)
        
        if results['tracks']['items']:
            track = results['tracks']['items'][0]
            return {
                'id': track['id'],
                'title': track['name'],
                'artist': track['artists'][0]['name']
            }
        return None
    
    def search_by_metadata(self, title: str, artist: str) -> Optional[Dict]:
        query = f"track:{title} artist:{artist}"
        results = self.client.sp.search(q=query, type='track', limit=1)
        
        if results['tracks']['items']:
            track = results['tracks']['items'][0]
            return {
                'id': track['id'],
                'title': track['name'],
                'artist': track['artists'][0]['name'],
                'confidence': 0.8  # Lower confidence for metadata search
            }
        return None

    def _candidate_from_item(self, item: Dict) -> Dict:
        album = item.get('album') or {}
        external_ids = item.get('external_ids') or {}
        artists = [
            artist.get('name')
            for artist in item.get('artists', [])
            if isinstance(artist, dict) and artist.get('name')
        ]
        track_id = item.get('id')
        return {
            'id': track_id,
            'title': item.get('name', ''),
            'artists': artists,
            'album': album.get('name', '') if isinstance(album, dict) else str(album or ''),
            'duration_ms': item.get('duration_ms'),
            'isrc': external_ids.get('isrc') if isinstance(external_ids, dict) else None,
            'url': f"https://open.spotify.com/track/{track_id}" if track_id else None,
            'raw': item,
        }

    def search_candidates(self, title: str, artist: str, limit: int = 10) -> List[Dict]:
        """Return several Spotify search results for the matcher to score."""
        query = f"track:{title} artist:{artist}"
        results = self.client.sp.search(q=query, type='track', limit=limit)
        items = (results.get('tracks') or {}).get('items') or []
        return [self._candidate_from_item(item) for item in items if item]

    
    def generate_playback_link(self, track_ids: List[str]) -> str:
        # For now, just return a search link
        # Later we'll implement playlist creation
        if len(track_ids) == 1:
            return f"spotify:track:{track_ids[0]}"
        else:
            # Would need to create a playlist here
            return f"spotify:search:{'+'.join(track_ids[:5])}"

    def create_playlist(self, access_token: str, name: str, description: str = "") -> str:
        """Create a new playlist and return its ID"""
        import requests
        
        # 1. Get User ID
        headers = {'Authorization': f'Bearer {access_token}'}
        user_resp = requests.get('https://api.spotify.com/v1/me', headers=headers)
        if user_resp.status_code != 200:
            raise Exception("Failed to get user info")
        user_id = user_resp.json()['id']
        
        # 2. Create Playlist
        url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
        data = {
            "name": name,
            "description": description,
            "public": False
        }
        
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code not in [200, 201]:
            raise Exception(f"Failed to create playlist: {resp.text}")
            
        return resp.json()['id']
    
    def find_playlist_by_marker(self, access_token: str, marker: str) -> Optional[str]:
        """Find a playlist containing the marker in description"""
        import requests
        headers = {'Authorization': f'Bearer {access_token}'}
        try:
            resp = requests.get('https://api.spotify.com/v1/me/playlists?limit=50', headers=headers)
            if resp.status_code != 200:
                return None
            playlists = resp.json().get('items', [])
            for pl in playlists:
                desc = pl.get('description') or ''
                if marker in desc:
                    return pl['id']
        except Exception:
            pass
        return None
    

    def add_tracks_to_playlist(self, access_token: str, playlist_id: str, track_uris: List[str], position: int = None):
        """Add tracks to a playlist"""
        import requests
        
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Spotify allows max 100 tracks per request
        for i in range(0, len(track_uris), 100):
            chunk = track_uris[i:i + 100]
            data = {"uris": chunk}
            if position is not None:
                data["position"] = position + i
            resp = requests.post(url, headers=headers, json=data)
            if resp.status_code not in [200, 201]:
                raise Exception(f"Failed to add tracks: {resp.text}")
        return 200
    
