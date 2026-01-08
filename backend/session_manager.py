# backend/session_manager.py (COMPLETE FILE)

import redis
import json
import secrets
import time
from typing import List, Dict, Optional

class SessionManager:
    def __init__(self):
        """Initialize Redis connection"""
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True  # Automatically decode bytes to strings
        )
    
    def generate_code(self) -> str:
        """Generate a unique 4-digit code"""
        while True:
            code = str(secrets.randbelow(9000) + 1000)  # 1000-9999
            
            # Check if code already exists
            if not self.redis_client.exists(f"playlist:{code}"):
                return code
    
    def save_session(
        self, 
        tracks: List[Dict], 
        target_platform: str = None,
        source_platform: str = None,
        ttl: int = 86400
    ) -> str:
        """
        Save playlist session to Redis
        
        Args:
            tracks: List of matched track dictionaries
            target_platform: Which platform was targeted
            source_platform: Which platform was the source
            ttl: Time to live in seconds (default 24 hours)
        
        Returns:
            Session code
        """
        code = self.generate_code()
        key = f"playlist:{code}"
        
        # Store tracks AND metadata
        session_data = {
            'tracks': tracks,
            'target_platform': target_platform,
            'source_platform': source_platform,
            'created_at': time.time()
        }
        
        # Store as JSON
        self.redis_client.setex(
            key,
            ttl,
            json.dumps(session_data)
        )
        
        print(f"✅ Session saved with code: {code}")
        print(f"   Target platform: {target_platform}")
        print(f"   Source platform: {source_platform}")
        print(f"   Tracks: {len(tracks)}")
        
        return code
    
    def get_session(self, code: str) -> Optional[Dict]:
        """
        Retrieve playlist session from Redis
        
        Args:
            code: Session code
        
        Returns:
            Session data dict or None if not found
        """
        key = f"playlist:{code}"
        data = self.redis_client.get(key)
        
        if data:
            return json.loads(data)
        return None
    
    def delete_session(self, code: str) -> bool:
        """Delete a session"""
        key = f"playlist:{code}"
        return self.redis_client.delete(key) > 0
    
    def session_exists(self, code: str) -> bool:
        """Check if session exists"""
        key = f"playlist:{code}"
        return self.redis_client.exists(key) > 0
    
    def get_session_ttl(self, code: str) -> int:
        """Get remaining TTL in seconds"""
        key = f"playlist:{code}"
        return self.redis_client.ttl(key)


# Test it!
if __name__ == "__main__":
    manager = SessionManager()
    
    # Sample data
    test_tracks = [
        {
            'title': 'Blinding Lights',
            'artist': 'The Weeknd',
            'spotify_id': 'abc123',
            'youtube_music_id': 'xyz789',
            'youtube_music_url': 'https://music.youtube.com/watch?v=xyz789'
        }
    ]
    
    # Save session with target platform
    code = manager.save_session(
        test_tracks, 
        target_platform='youtube_music',
        source_platform='Spotify'
    )
    print(f"\nSession code: {code}")
    
    # Retrieve session
    retrieved = manager.get_session(code)
    print(f"\nRetrieved session:")
    print(f"  Target platform: {retrieved['target_platform']}")
    print(f"  Source platform: {retrieved['source_platform']}")
    print(f"  Tracks: {len(retrieved['tracks'])}")
    
    # Check TTL
    ttl = manager.get_session_ttl(code)
    print(f"\nExpires in: {ttl} seconds ({ttl/3600:.1f} hours)")