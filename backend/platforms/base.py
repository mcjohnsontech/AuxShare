# backend/platforms/base.py

from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class MusicPlatform(ABC):
    """Base class for all music platform integrations"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def extract_playlist_id(self, url: str) -> Optional[str]:
        """Extract playlist ID from URL"""
        pass
    
    @abstractmethod
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        """Get all tracks from a playlist"""
        pass
    
    @abstractmethod
    def search_by_isrc(self, isrc: str) -> Optional[Dict]:
        """Search for a track by ISRC code"""
        pass
    
    @abstractmethod
    def search_by_metadata(self, title: str, artist: str) -> Optional[Dict]:
        """Search for a track by title and artist"""
        pass
    
    @abstractmethod
    def generate_playback_link(self, track_ids: List[str]) -> str:
        """Generate a link to play these tracks"""
        pass
    
    def match_track(self, track: Dict) -> Optional[Dict]:
        """
        Match a track from another platform to this platform
        Uses ISRC first, then falls back to metadata search
        """
        # Try ISRC first (most accurate)
        if track.get('isrc'):
            result = self.search_by_isrc(track['isrc'])
            if result:
                result['match_method'] = 'isrc'
                result['confidence'] = 1.0
                return result
        
        # Fallback to title + artist search
        artist = track.get('artist') or track.get('artists')
        if not artist:
            # If still no artist (shouldn't happen), try empty string or return None
            return None
            
        result = self.search_by_metadata(track['title'], artist)
        if result:
            result['match_method'] = 'metadata'
            # Confidence will be set by the implementation
        
        return result