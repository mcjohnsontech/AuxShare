# backend/platforms/youtube_music.py

from typing import List, Dict, Optional
from .base import MusicPlatform
from youtube_music_client import YouTubeMusicClient
    

class YouTubeMusicPlatform(MusicPlatform):
    def __init__(self):
        super().__init__('youtube_music')
        self.client = YouTubeMusicClient()
    
    def extract_playlist_id(self, url: str) -> Optional[str]:
        import re
        match = re.search(r'list=([a-zA-Z0-9_-]+)', url)
        return match.group(1) if match else None
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        playlist = self.client.ytmusic.get_playlist(playlist_id)
        
        tracks = []
        for item in playlist['tracks']:
            tracks.append({
                'title': item['title'],
                'artist': item['artists'][0]['name'],
                'youtube_music_id': item['videoId'],
                'duration_ms': item.get('duration_seconds', 0) * 1000
            })
        
        return tracks
    
    def search_by_isrc(self, isrc: str) -> Optional[Dict]:
        # YouTube Music doesn't support ISRC search
        return None
    
    def search_by_metadata(self, title: str, artist: str) -> Optional[Dict]:
        result = self.client.search_track(title, artist)
        
        if result:
            return {
                'id': result['youtube_music_id'],
                'title': result['title'],
                'artist': result['artist'],
                'confidence': result['confidence']
            }
        return None
    
    def generate_playback_link(self, track_ids: List[str]) -> str:
        if len(track_ids) == 1:
            return f"https://music.youtube.com/watch?v={track_ids[0]}"
        else:
            # Create a playlist URL with multiple videos
            video_list = ','.join(track_ids)
            return f"https://music.youtube.com/watch?v={track_ids[0]}&list={video_list}"