# backend/export_idempotency.py
"""Durable idempotency for playlist exports.

Exporting the same conversion session twice must never create a second
playlist. The authoritative record is stored in Redis, keyed by the Spotify
account, the target platform, and the session code, so a repeated click (or a
retry after a timeout) resolves to the playlist that already exists.

A short-lived lock guards the create step so two concurrent requests cannot
both create a playlist.
"""
import json
import time
from typing import Any, Dict, Optional

RECORD_TTL_SECONDS = 86400 * 30
LOCK_TTL_SECONDS = 180


class ExportIdempotency:
    def __init__(self, redis_client, record_ttl: int = RECORD_TTL_SECONDS,
                 lock_ttl: int = LOCK_TTL_SECONDS):
        self.redis = redis_client
        self.record_ttl = record_ttl
        self.lock_ttl = lock_ttl

    # ---------------- keys ----------------

    @staticmethod
    def record_key(account_id: str, target_platform: str, session_code: str) -> str:
        return f"export:{account_id}:{target_platform}:{session_code}"

    @staticmethod
    def lock_key(account_id: str, target_platform: str, session_code: str) -> str:
        return f"export_lock:{account_id}:{target_platform}:{session_code}"

    # ---------------- record ----------------

    def get_record(self, account_id: str, target_platform: str, session_code: str) -> Optional[Dict[str, Any]]:
        raw = self.redis.get(self.record_key(account_id, target_platform, session_code))
        if not raw:
            return None
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return None

    def save_record(self, account_id: str, target_platform: str, session_code: str,
                    playlist_id: str, completed: bool, tracks_added: int = 0) -> None:
        payload = {
            "playlist_id": playlist_id,
            "completed": completed,
            "tracks_added": tracks_added,
            "updated_at": time.time(),
        }
        self.redis.setex(
            self.record_key(account_id, target_platform, session_code),
            self.record_ttl,
            json.dumps(payload),
        )

    # ---------------- lock ----------------

    def acquire_lock(self, account_id: str, target_platform: str, session_code: str) -> bool:
        return bool(self.redis.set(
            self.lock_key(account_id, target_platform, session_code),
            str(time.time()),
            nx=True,
            ex=self.lock_ttl,
        ))

    def release_lock(self, account_id: str, target_platform: str, session_code: str) -> None:
        self.redis.delete(self.lock_key(account_id, target_platform, session_code))

    def clear_record(self, account_id: str, target_platform: str, session_code: str) -> None:
        self.redis.delete(self.record_key(account_id, target_platform, session_code))
