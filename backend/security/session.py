# backend/security/session.py
import os
import json
import time
import secrets
from typing import Optional, Dict, Any, List
from fastapi import Request, Response
import redis
from .crypto import default_crypto

SESSION_COOKIE_NAME = "aux_session"

class SecureSessionManager:
    """
    Manages high-entropy session IDs, server-side encrypted OAuth tokens,
    and PKCE state bindings backed by Redis.
    """
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        if redis_client is None:
            self.redis = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                db=int(os.getenv("REDIS_DB", "0")),
                decode_responses=True
            )
        else:
            self.redis = redis_client

    def generate_session_id(self) -> str:
        """Generate a cryptographically secure, high-entropy session ID."""
        return f"sess_{secrets.token_urlsafe(24)}"

    def get_or_create_session_id(self, request: Request, response: Optional[Response] = None) -> str:
        """Retrieve existing session ID from httpOnly cookie or generate a new one."""
        session_id = request.cookies.get(SESSION_COOKIE_NAME)
        if not session_id or len(session_id) < 16:
            session_id = self.generate_session_id()
            if response is not None:
                self.set_session_cookie(response, session_id)
        return session_id

    def set_session_cookie(self, response: Response, session_id: str) -> None:
        """Set the httpOnly session cookie with appropriate security attributes.

        The `secure` flag is controlled exclusively by the COOKIE_SECURE env var
        (must be "true" for production; never auto-detected from HTTPS to avoid
        reverse-proxy masking issues).
        """
        is_secure = os.getenv("COOKIE_SECURE", "false").lower() == "true"

        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_id,
            httponly=True,
            samesite="lax",
            secure=is_secure,
            max_age=86400 * 30,  # 30 days
            path="/"
        )

    # ---------------- OAuth State & PKCE ----------------

    def store_oauth_pending_state(self, state: str, session_id: str, code_verifier: str, ttl: int = 600) -> None:
        """Store pending OAuth state bound to the session ID and PKCE verifier."""
        data = {
            "session_id": session_id,
            "code_verifier": code_verifier,
            "created_at": time.time()
        }
        self.redis.setex(f"oauth_state:{state}", ttl, json.dumps(data))

    def consume_oauth_pending_state(self, state: str) -> Optional[Dict[str, Any]]:
        """Validate and atomically consume (delete) the pending OAuth state."""
        key = f"oauth_state:{state}"
        data = self.redis.get(key)
        if not data:
            return None
        self.redis.delete(key)
        try:
            return json.loads(data)
        except Exception:
            return None

    # ---------------- Encrypted Token Storage ----------------

    def store_user_tokens(
        self,
        session_id: str,
        platform: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_in: int = 3600,
        scopes: Optional[str] = None
    ) -> None:
        """Encrypt and store user OAuth tokens bound to the session."""
        key = f"tokens:{session_id}:{platform}"
        expires_at = time.time() + expires_in
        
        token_data = {
            "access_token": default_crypto.encrypt(access_token),
            "refresh_token": default_crypto.encrypt(refresh_token) if refresh_token else None,
            "expires_at": expires_at,
            "scopes": scopes
        }
        # Keep tokens stored for up to 30 days or until revoked
        self.redis.setex(key, 86400 * 30, json.dumps(token_data))

    def get_user_tokens(self, session_id: str, platform: str) -> Optional[Dict[str, Any]]:
        """Retrieve and decrypt user tokens for a platform."""
        key = f"tokens:{session_id}:{platform}"
        raw = self.redis.get(key)
        if not raw:
            return None
        try:
            token_data = json.loads(raw)
            return {
                "access_token": default_crypto.decrypt(token_data["access_token"]),
                "refresh_token": default_crypto.decrypt(token_data["refresh_token"]) if token_data.get("refresh_token") else None,
                "expires_at": token_data.get("expires_at", 0),
                "is_expired": time.time() >= token_data.get("expires_at", 0) - 60,
                "scopes": token_data.get("scopes")
            }
        except Exception as e:
            print(f"Failed to decrypt user tokens: {e}")
            return None

    def clear_user_tokens(self, session_id: str, platform: str) -> bool:
        """Delete user tokens from session."""
        key = f"tokens:{session_id}:{platform}"
        return self.redis.delete(key) > 0

    def migrate_session(self, old_session_id: str, new_session_id: str, platforms: tuple = ("spotify",)) -> None:
        """Copy all platform token entries from old_session_id to new_session_id,
        then delete the old keys.  Called after a successful OAuth callback to
        rotate the session ID and prevent session-fixation attacks."""
        for platform in platforms:
            old_key = f"tokens:{old_session_id}:{platform}"
            new_key = f"tokens:{new_session_id}:{platform}"
            raw = self.redis.get(old_key)
            if raw:
                # Preserve the remaining TTL of the original key
                ttl = self.redis.ttl(old_key)
                ttl = ttl if ttl and ttl > 0 else 86400 * 30
                self.redis.setex(new_key, ttl, raw)
                self.redis.delete(old_key)

