# backend/jobs/events.py
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

import redis


class ReviewEventLogger:
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
    
    def log_event(self, job_id: str, track_id: str, candidates: List[Dict], chosen_id: Optional[str], user_id: Optional[str] = None):
        event = {
            "job_id": job_id,
            "track_id": track_id,
            "candidates": candidates,
            "chosen_id": chosen_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        key = f"review_events:{job_id}"
        self.redis.lpush(key, json.dumps(event))
        self.redis.expire(key, 86400 * 30)
    
    def get_events(self, job_id: str) -> List[Dict]:
        key = f"review_events:{job_id}"
        events = self.redis.lrange(key, 0, -1)
        result = []
        for e in events:
            try:
                result.append(json.loads(e))
            except Exception:
                pass
        return result
