# backend/auth.py
import os
import urllib.parse
from typing import Optional, Dict, Any
import requests
from fastapi import HTTPException
from dotenv import load_dotenv

from security.oauth import generate_code_verifier, generate_code_challenge, generate_state
from security.session import SecureSessionManager
from security.redaction import redact_sensitive_string

load_dotenv()

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID') or os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET') or os.getenv('SPOTIPY_CLIENT_SECRET')
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

# Minimum required scopes for creating & managing playlists
SCOPES = "playlist-modify-public playlist-modify-private user-read-private"

def get_redirect_uri() -> str:
    """
    Get configured Spotify redirect URI.
    Supports SPOTIFY_REDIRECT_URI, or falls back to BACKEND_URL/api/auth/callback,
    or FRONTEND_URL/callback.
    """
    explicit = os.getenv("SPOTIFY_REDIRECT_URI")
    if explicit:
        return explicit
    backend_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
    return f"{backend_url}/api/auth/callback"


def get_public_backend_url() -> str:
    """Public origin of this API, as the browser must reach it directly.

    OAuth state is bound to a cookie, and cookies are origin-scoped. The login
    must therefore begin on the same origin that Spotify will redirect back to,
    otherwise the callback cannot present the cookie that the state is bound to.
    """
    explicit = os.getenv("PUBLIC_BACKEND_URL")
    if explicit:
        return explicit.rstrip("/")

    redirect_uri = get_redirect_uri()
    parsed = urllib.parse.urlparse(redirect_uri)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"

    return os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

class SpotifyAuth:
    session_manager = SecureSessionManager()

    @classmethod
    def get_auth_url(cls, session_id: str) -> Dict[str, str]:
        """
        Generate the Spotify OAuth authorization URL with PKCE and state binding.
        """
        if not CLIENT_ID:
            raise HTTPException(status_code=500, detail="Missing Spotify Client ID configuration.")

        code_verifier = generate_code_verifier(64)
        code_challenge = generate_code_challenge(code_verifier)
        state = generate_state(32)

        # Bind state and PKCE verifier to session
        cls.session_manager.store_oauth_pending_state(state, session_id, code_verifier)

        redirect_uri = get_redirect_uri()
        params = {
            'client_id': CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': SCOPES,
            'state': state,
            'code_challenge_method': 'S256',
            'code_challenge': code_challenge,
            'show_dialog': 'true'
        }
        url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
        return {"url": url, "state": state}

    @classmethod
    def exchange_code(cls, code: str, state: str, session_id: str) -> Dict[str, Any]:
        """
        Validate OAuth state, exchange auth code with PKCE code_verifier,
        and store encrypted tokens server-side.
        """
        if not CLIENT_ID or not CLIENT_SECRET:
            raise HTTPException(status_code=500, detail="Missing Spotify Credentials.")

        # 1. Strictly validate state
        pending = cls.session_manager.consume_oauth_pending_state(state)
        if not pending:
            raise HTTPException(status_code=400, detail="Invalid or expired OAuth state parameter.")

        # The flow must be completed by the same browser that started it. Login
        # is initiated on the backend origin (see /api/auth/start) precisely so
        # that this cookie is available here; without that check an attacker
        # could hand a victim an authorize URL and end up with the victim's
        # Spotify tokens bound to the attacker's session.
        pending_session_id = pending.get("session_id")
        if not pending_session_id:
            raise HTTPException(status_code=400, detail="OAuth state is not bound to a session.")
        if not session_id or session_id != pending_session_id:
            raise HTTPException(status_code=400, detail="OAuth state does not match session.")

        code_verifier = pending.get("code_verifier")
        if not code_verifier:
            raise HTTPException(status_code=400, detail="Missing PKCE code verifier for state.")

        # 2. Exchange authorization code with PKCE verifier
        redirect_uri = get_redirect_uri()
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code_verifier': code_verifier
        }

        try:
            response = requests.post(TOKEN_URL, data=data, timeout=15)
        except requests.RequestException as e:
            redacted_err = redact_sensitive_string(str(e))
            raise HTTPException(status_code=502, detail=f"Failed to connect to Spotify: {redacted_err}")

        if response.status_code != 200:
            err_msg = redact_sensitive_string(response.text)
            raise HTTPException(status_code=400, detail=f"Spotify token exchange failed: {err_msg}")

        token_payload = response.json()
        access_token = token_payload.get('access_token')
        refresh_token = token_payload.get('refresh_token')
        expires_in = token_payload.get('expires_in', 3600)
        scopes = token_payload.get('scope', SCOPES)

        if not access_token:
            raise HTTPException(status_code=400, detail="Spotify did not return an access token.")

        # 3. Encrypt and store tokens in session
        effective_session_id = pending_session_id
        cls.session_manager.store_user_tokens(
            session_id=effective_session_id,
            platform="spotify",
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            scopes=scopes
        )

        return {
            "status": "authenticated",
            "session_id": effective_session_id,
            "expires_in": expires_in
        }

    @classmethod
    def refresh_user_token(cls, session_id: str) -> str:
        """
        Refresh expired access token using stored encrypted refresh token.
        """
        tokens = cls.session_manager.get_user_tokens(session_id, "spotify")
        if not tokens or not tokens.get("refresh_token"):
            raise HTTPException(
                status_code=401,
                detail="No refresh token available. Re-authorization required."
            )

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': tokens["refresh_token"],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        try:
            response = requests.post(TOKEN_URL, data=data, timeout=15)
        except requests.RequestException as e:
            raise HTTPException(status_code=502, detail=f"Failed to refresh token: {redact_sensitive_string(str(e))}")

        if response.status_code != 200:
            # Refresh token may have been revoked
            cls.session_manager.clear_user_tokens(session_id, "spotify")
            raise HTTPException(
                status_code=401,
                detail="Spotify authorization has expired or was revoked. Please log in again."
            )

        payload = response.json()
        new_access_token = payload.get('access_token')
        new_refresh = payload.get('refresh_token') or tokens["refresh_token"]
        expires_in = payload.get('expires_in', 3600)

        cls.session_manager.store_user_tokens(
            session_id=session_id,
            platform="spotify",
            access_token=new_access_token,
            refresh_token=new_refresh,
            expires_in=expires_in,
            scopes=tokens.get("scopes")
        )
        return new_access_token
