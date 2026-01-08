# backend/session_manager.py

import redis
import json
import secrets
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
    
    def save_session(self, tracks: List[Dict], ttl: int = 86400) -> str:
        """
        Save playlist session to Redis
        
        Args:
            tracks: List of matched track dictionaries
            ttl: Time to live in seconds (default 24 hours)
        
        Returns:
            Session code
        """
        code = self.generate_code()
        key = f"playlist:{code}"
        
        # Store as JSON
        self.redis_client.setex(
            key,
            ttl,
            json.dumps(tracks)
        )
        
        print(f"✅ Session saved with code: {code}")
        return code
    
    def get_session(self, code: str) -> Optional[List[Dict]]:
        """
        Retrieve playlist session from Redis
        
        Args:
            code: Session code
        
        Returns:
            List of tracks or None if not found
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
            'youtube_music_id': 'xyz789'
        }
    ]
    
    # Save session
    code = manager.save_session(test_tracks)
    print(f"Session code: {code}")
    
    # Retrieve session
    retrieved = manager.get_session(code)
    print(f"Retrieved: {retrieved}")
    
    # Check TTL
    ttl = manager.get_session_ttl(code)
    print(f"Expires in: {ttl} seconds ({ttl/3600:.1f} hours)")