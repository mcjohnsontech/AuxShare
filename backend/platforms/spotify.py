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

    def get_current_user_id(self, access_token: str) -> str:
        """Return the Spotify user id that owns this access token."""
        import requests

        headers = {'Authorization': f'Bearer {access_token}'}
        resp = requests.get('https://api.spotify.com/v1/me', headers=headers, timeout=15)
        if resp.status_code != 200:
            raise Exception(f"Failed to get user info: {resp.text}")
        return resp.json()['id']

    def get_playlist_track_uris(self, access_token: str, playlist_id: str) -> List[str]:
        """Return every track URI already in a playlist (paginated)."""
        import requests

        headers = {'Authorization': f'Bearer {access_token}'}
        uris: List[str] = []
        url = (
            f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
            '?fields=next,items(track(uri))&limit=100'
        )
        while url:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                raise Exception(f"Failed to read playlist tracks: {resp.text}")
            payload = resp.json()
            for item in payload.get('items') or []:
                track = (item or {}).get('track') or {}
                uri = track.get('uri')
                if uri:
                    uris.append(uri)
            url = payload.get('next')
        return uris

    def get_playlist_track_count(self, access_token: str, playlist_id: str) -> Optional[int]:
        """Return the playlist's track count, or None if it no longer exists.

        Raises for transport/auth errors so callers can distinguish "deleted"
        from "could not check right now" and avoid creating a duplicate.
        """
        import requests

        headers = {'Authorization': f'Bearer {access_token}'}
        url = f'https://api.spotify.com/v1/playlists/{playlist_id}?fields=id,tracks(total)'
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 404:
            return None
        if resp.status_code != 200:
            raise Exception(f"Failed to read playlist: {resp.text}")
        payload = resp.json() or {}
        return ((payload.get('tracks') or {}).get('total'))

    def create_playlist(self, access_token: str, name: str, description: str = "") -> str:
        """Create a new playlist and return its ID"""
        import requests
        
        user_id = self.get_current_user_id(access_token)
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 2. Create Playlist
        url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
        data = {
            "name": name,
            "description": description,
            "public": False
        }
        
        resp = requests.post(url, headers=headers, json=data, timeout=15)
        if resp.status_code not in [200, 201]:
            raise Exception(f"Failed to create playlist: {resp.text}")
            
        return resp.json()['id']
    
    def find_playlist_by_marker(self, access_token: str, marker: str) -> Optional[str]:
        """Find a playlist containing the marker in its description.

        Paginates through the user's playlists. This is only a recovery path for
        playlists created before durable idempotency records existed; the
        primary lookup is the Redis export record.
        """
        import requests
        headers = {'Authorization': f'Bearer {access_token}'}
        url = 'https://api.spotify.com/v1/me/playlists?limit=50'
        pages = 0
        try:
            while url and pages < 20:
                resp = requests.get(url, headers=headers, timeout=15)
                if resp.status_code != 200:
                    return None
                payload = resp.json()
                for pl in payload.get('items') or []:
                    desc = (pl or {}).get('description') or ''
                    if marker in desc:
                        return pl['id']
                url = payload.get('next')
                pages += 1
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
    
