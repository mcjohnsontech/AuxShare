# backend/cache/mapping_cache.py
import json
import os
from typing import Optional, Dict, Any

import redis


class MappingCache:
    def __init__(self, redis_client=None):
        if redis_client is None:
            self.redis = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                db=int(os.getenv("REDIS_DB", "0")),
                decode_responses=True
            )
        else:
            self.redis = redis_client
    
    def _key(self, isrc: str, target_platform: str, market: str = "US") -> str:
        return f"map:{target_platform}:{market}:{isrc.upper()}"
    
    def get(self, isrc: str, target_platform: str, market: str = "US") -> Optional[Dict[str, Any]]:
        if not isrc:
            return None
        key = self._key(isrc, target_platform, market)
        data = self.redis.get(key)
        if not data:
            return None
        try:
            return json.loads(data)
        except Exception:
            return None
    
    def set_positive(self, isrc: str, target_platform: str, market: str, target_track_id: str, ttl: int = 86400 * 30):
        if not isrc or not target_track_id:
            return
        key = self._key(isrc, target_platform, market)
        data = {"type": "positive", "target_track_id": target_track_id}
        self.redis.setex(key, ttl, json.dumps(data))
    
    def set_negative(self, isrc: str, target_platform: str, market: str, ttl: int = 86400 * 7):
        if not isrc:
            return
        key = self._key(isrc, target_platform, market)
        data = {"type": "negative", "target_track_id": None}
        self.redis.setex(key, ttl, json.dumps(data))
    
    def is_negative(self, isrc: str, target_platform: str, market: str = "US") -> bool:
        result = self.get(isrc, target_platform, market)
        if result and result.get("type") == "negative":
            return True
        return False
