# backend/jobs/queue.py
import json
import os
from typing import Optional, Dict, Any

import redis


class JobQueue:
    def __init__(self, redis_client=None):
        if redis_client is None:
            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                ssl_kwargs = {"ssl_cert_reqs": None} if redis_url.startswith("rediss://") else {}
                self.redis = redis.from_url(redis_url, decode_responses=True, **ssl_kwargs)
            else:
                self.redis = redis.Redis(
                    host=os.getenv("REDIS_HOST", "localhost"),
                    port=int(os.getenv("REDIS_PORT", "6379")),
                    db=int(os.getenv("REDIS_DB", "0")),
                    decode_responses=True
                )
        else:
            self.redis = redis_client
        self.queue_name = "conversion_jobs"
    
    def enqueue(self, job_id: str, payload: Optional[Dict[str, Any]] = None):
        data = json.dumps({"job_id": job_id, "payload": payload or {}})
        self.redis.lpush(self.queue_name, data)
    
    def dequeue(self, timeout: int = 5) -> Optional[Dict[str, Any]]:
        result = self.redis.brpop(self.queue_name, timeout=timeout)
        if not result:
            return None
        _, data = result
        try:
            return json.loads(data)
        except Exception:
            return None
    
    def get_queue_length(self) -> int:
        return self.redis.llen(self.queue_name)
