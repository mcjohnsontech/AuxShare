# backend/cache/overrides.py
import json
import os
from typing import Optional, Dict, Any

import redis


class UserOverrides:
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
    
    def _user_key(self, user_id: str) -> str:
        return f"user_overrides:{user_id}"
    
    def _global_key(self) -> str:
        return "global_mappings:consensus"
    
    def set_user_override(self, user_id: str, source_key: str, target_track_id: str):
        key = self._user_key(user_id)
        data = self.redis.get(key) or "{}"
        try:
            overrides = json.loads(data)
        except Exception:
            overrides = {}
        overrides[source_key] = target_track_id
        self.redis.set(key, json.dumps(overrides))
    
    def get_user_override(self, user_id: str, source_key: str) -> Optional[str]:
        key = self._user_key(user_id)
        data = self.redis.get(key)
        if not data:
            return None
        try:
            overrides = json.loads(data)
            return overrides.get(source_key)
        except Exception:
            return None
    
    def promote_to_global(self, source_key: str, target_track_id: str, min_consensus: int = 3):
        key = self._global_key()
        data = self.redis.get(key) or "{}"
        try:
            consensus = json.loads(data)
        except Exception:
            consensus = {}
        if source_key not in consensus:
            consensus[source_key] = {}
        consensus[source_key][target_track_id] = consensus[source_key].get(target_track_id, 0) + 1
        # Check if any target has reached consensus
        if consensus[source_key][target_track_id] >= min_consensus:
            self.redis.set(f"promoted:{source_key}", target_track_id)
        self.redis.set(key, json.dumps(consensus))
    
    def get_promoted(self, source_key: str) -> Optional[str]:
        return self.redis.get(f"promoted:{source_key}")
