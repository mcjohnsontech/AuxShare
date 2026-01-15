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

    def add_tracks_to_playlist(self, access_token: str, playlist_id: str, track_uris: List[str]):
        """Add tracks to a playlist"""
        import requests
        
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Spotify allows max 100 tracks per request
        for i in range(0, len(track_uris), 100):
            chunk = track_uris[i:i + 100]
            data = {"uris": chunk}
            requests.post(url, headers=headers, json=data)
