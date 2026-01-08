# backend/platforms/youtube_music.py (COMPLETE UPDATE)

from typing import List, Dict, Optional
from platforms.base import MusicPlatform
from youtube_music_client import YouTubeMusicClient
import time

class YouTubeMusicPlatform(MusicPlatform):
    def __init__(self):
        super().__init__('youtube_music')
        self.client = YouTubeMusicClient()
    
    def extract_playlist_id(self, url: str) -> Optional[str]:
        import re
        
        # Handle different YouTube Music URL formats
        patterns = [
            r'list=([a-zA-Z0-9_-]+)',  # Standard format
            r'playlist/([a-zA-Z0-9_-]+)',  # Alternative format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                playlist_id = match.group(1)
                # Remove &si parameter if present
                playlist_id = playlist_id.split('&')[0]
                return playlist_id
        
        return None
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        """
        Fetch playlist tracks with retry logic
        """
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                print(f"   Attempting to fetch YouTube Music playlist (attempt {attempt + 1}/{max_retries})...")
                
                playlist = self.client.ytmusic.get_playlist(playlist_id)
                
                tracks = []
                for item in playlist.get('tracks', []):
                    if not item:
                        continue
                    
                    # Extract video ID
                    video_id = item.get('videoId')
                    if not video_id:
                        continue
                    
                    # Get artist name
                    artists = item.get('artists', [])
                    artist_name = artists[0].get('name', 'Unknown Artist') if artists else 'Unknown Artist'
                    
                    # Get album name
                    album = item.get('album')
                    album_name = album.get('name', '') if album else ''
                    
                    # Get duration
                    duration_seconds = 0
                    if 'duration_seconds' in item:
                        duration_seconds = item['duration_seconds']
                    elif 'duration' in item:
                        # Parse duration string like "3:45"
                        duration_str = item['duration']
                        try:
                            parts = duration_str.split(':')
                            if len(parts) == 2:
                                duration_seconds = int(parts[0]) * 60 + int(parts[1])
                            elif len(parts) == 3:
                                duration_seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                        except:
                            pass
                    
                    tracks.append({
                        'title': item.get('title', 'Unknown Title'),
                        'artist': artist_name,
                        'album': album_name,
                        'youtube_music_id': video_id,
                        'duration_ms': duration_seconds * 1000 if duration_seconds else 0
                    })
                
                print(f"   ✅ Successfully fetched {len(tracks)} tracks from YouTube Music")
                return tracks
                
            except KeyError as e:
                error_msg = f"YouTube Music API structure changed (KeyError: {e})"
                print(f"   ❌ {error_msg}")
                
                if attempt < max_retries - 1:
                    print(f"   ⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise ValueError(
                        f"Failed to fetch YouTube Music playlist after {max_retries} attempts.\n"
                        f"This might be due to:\n"
                        f"  • YouTube Music API changes\n"
                        f"  • Private or unavailable playlist\n"
                        f"  • Network connectivity issues\n\n"
                        f"Please try:\n"
                        f"  1. Using a different playlist\n"
                        f"  2. Using Spotify as source instead\n"
                        f"  3. Checking if the playlist is public"
                    )
            
            except ConnectionError as e:
                print(f"   ❌ Connection error: {e}")
                
                if attempt < max_retries - 1:
                    print(f"   ⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise ValueError(
                        f"Failed to connect to YouTube Music after {max_retries} attempts.\n"
                        f"Please check your internet connection and try again."
                    )
            
            except Exception as e:
                print(f"   ❌ Unexpected error: {e}")
                
                if attempt < max_retries - 1:
                    print(f"   ⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise ValueError(
                        f"Failed to fetch YouTube Music playlist: {str(e)}\n"
                        f"Please try using Spotify as source instead."
                    )
        
        return []
    
    def search_by_isrc(self, isrc: str) -> Optional[Dict]:
        """YouTube Music doesn't support ISRC search"""
        return None
    
    def search_by_metadata(self, title: str, artist: str) -> Optional[Dict]:
        """Search for a track by title and artist"""
        try:
            result = self.client.search_track(title, artist)
            
            if result:
                return {
                    'id': result['youtube_music_id'],
                    'title': result['title'],
                    'artist': result['artist'],
                    'confidence': result['confidence']
                }
        except Exception as e:
            print(f"   ⚠️  YouTube Music search failed for '{title}': {e}")
        
        return None
    
    def generate_playback_link(self, track_ids: List[str]) -> str:
        """Generate deep link to YouTube Music"""
        if len(track_ids) == 1:
            return f"https://music.youtube.com/watch?v={track_ids[0]}"
        else:
            # Create a playlist URL with multiple videos
            video_list = ','.join(track_ids)
            return f"https://music.youtube.com/watch?v={track_ids[0]}&list={video_list}"