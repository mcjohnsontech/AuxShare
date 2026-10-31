# tests/test_security.py
"""
Security tests — Phase 1a.

Positive cases: correct flow succeeds.
Negative cases: tampered, replayed, expired, mismatched state; PKCE verifier
  mismatch; ciphertext-vs-plaintext identity; key rotation; cookie flags.

Warnings note (2 expected):
  httpx 0.27.x still emits DeprecationWarning: "The 'app' shortcut is now
  deprecated."  Fixing it requires 'transport=httpx.ASGITransport(app=app)'
  which is not available in 0.27.x without the ASGITransport class.  Pinned
  at httpx==0.27.2 (see requirements.txt) until FastAPI/Starlette TestClient
  moves off the shortcut itself.  The warnings are harmless and suppressed in
  pytest.ini via filterwarnings if desired.
"""
import json
import time
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from cryptography.fernet import Fernet

from main import app
from security.oauth import generate_code_verifier, generate_code_challenge, validate_pkce_challenge, generate_state
from security.crypto import TokenCrypto
from security.redaction import redact_sensitive_string, redact_sensitive_dict
from security.session import SecureSessionManager, SESSION_COOKIE_NAME
from session_manager import SessionManager

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clear_client_cookies():
    """Keep tests order-independent: the module-level client keeps cookies."""
    client.cookies.clear()
    yield
    client.cookies.clear()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_redis() -> tuple:
    """Return (mock_redis, storage_dict) wired for setex/get/delete/expire/ttl."""
    store: dict = {}
    ttls: dict = {}
    mock_redis = MagicMock()

    def _setex(k, ttl, v):
        store[k] = v
        ttls[k] = ttl

    def _get(k):
        return store.get(k)

    def _delete(k):
        existed = k in store
        store.pop(k, None)
        ttls.pop(k, None)
        return 1 if existed else 0

    def _expire(k, t):
        ttls[k] = t

    def _ttl(k):
        return ttls.get(k, -2)

    mock_redis.setex.side_effect = _setex
    mock_redis.get.side_effect = _get
    mock_redis.delete.side_effect = _delete
    mock_redis.expire.side_effect = _expire
    mock_redis.ttl.side_effect = _ttl

    return mock_redis, store


def _setup_login_and_get_state(mock_redis, store):
    """Run /api/auth/start and extract the OAuth state + session cookie.

    Login must begin on the backend origin so the session cookie is present
    when Spotify redirects back to /api/auth/callback.
    """
    sm = SecureSessionManager(redis_client=mock_redis)
    with patch("auth.SpotifyAuth.session_manager", sm), \
         patch("main.secure_session", sm):
        resp = client.get("/api/auth/start", follow_redirects=False)
    assert resp.status_code == 302
    location = resp.headers["location"]
    assert "accounts.spotify.com/authorize" in location
    assert "code_challenge=" in location

    # The session cookie set by /api/auth/start must be the one the state is
    # bound to, otherwise the callback can never validate the binding.
    cookie = client.cookies.get(SESSION_COOKIE_NAME)
    assert cookie

    state_keys = [k for k in store.keys() if k.startswith("oauth_state:")]
    assert len(state_keys) == 1
    state = state_keys[0].replace("oauth_state:", "")
    pending = json.loads(store[state_keys[0]])
    assert pending["session_id"] == cookie
    return sm, state


# ---------------------------------------------------------------------------
# PKCE
# ---------------------------------------------------------------------------

def test_pkce_generation_and_validation():
    verifier = generate_code_verifier(64)
    assert len(verifier) == 64
    assert 43 <= len(verifier) <= 128

    challenge = generate_code_challenge(verifier)
    assert len(challenge) > 20
    assert "=" not in challenge  # RFC 7636: no base64 padding

    assert validate_pkce_challenge(verifier, challenge) is True


def test_pkce_verifier_mismatch():
    """Wrong verifier must not satisfy a valid challenge."""
    verifier = generate_code_verifier(64)
    challenge = generate_code_challenge(verifier)
    wrong_verifier = generate_code_verifier(64)
    assert wrong_verifier != verifier
    assert validate_pkce_challenge(wrong_verifier, challenge) is False


# ---------------------------------------------------------------------------
# Crypto: key rotation, ciphertext identity
# ---------------------------------------------------------------------------

def test_crypto_multifernet_and_rotation():
    key1 = Fernet.generate_key().decode()
    key2 = Fernet.generate_key().decode()

    crypto_old = TokenCrypto(keys=[key2])
    token = "BQDb89_spotify_secret_access_token_12345"
    encrypted_old = crypto_old.encrypt(token)
    assert crypto_old.decrypt(encrypted_old) == token

    crypto_new = TokenCrypto(keys=[key1, key2])
    assert crypto_new.decrypt(encrypted_old) == token

    rotated = crypto_new.rotate(encrypted_old)
    assert crypto_new.decrypt(rotated) == token


def test_ciphertext_differs_from_plaintext():
    """Encryption must not be the identity function."""
    crypto = TokenCrypto(keys=[Fernet.generate_key().decode()])
    plaintext = "super_secret_access_token"
    ciphertext = crypto.encrypt(plaintext)
    assert ciphertext != plaintext
    assert len(ciphertext) > len(plaintext)


def test_decrypt_after_key_rotation():
    """Old ciphertext must remain decryptable when a new primary key is added."""
    old_key = Fernet.generate_key().decode()
    new_key = Fernet.generate_key().decode()

    crypto_before = TokenCrypto(keys=[old_key])
    secret = "refresh_token_xyz_123"
    ct = crypto_before.encrypt(secret)

    crypto_after = TokenCrypto(keys=[new_key, old_key])
    assert crypto_after.decrypt(ct) == secret


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------

def test_redaction_guarantees_no_logged_tokens():
    raw_log = (
        "Error in request: Bearer BQDb89_spotify_secret_token_1234567890 "
        "with authorization: Bearer secret_123"
    )
    sanitized = redact_sensitive_string(raw_log)
    assert "BQDb89_spotify_secret_token_1234567890" not in sanitized
    assert "[REDACTED_TOKEN]" in sanitized

    raw_dict = {
        "access_token": "secret_access_token_abc",
        "refresh_token": "secret_refresh_token_xyz",
        "nested": {"token": "nested_secret_123"},
    }
    sanitized_dict = redact_sensitive_dict(raw_dict)
    assert sanitized_dict["access_token"] == "[REDACTED]"
    assert sanitized_dict["refresh_token"] == "[REDACTED]"
    assert sanitized_dict["nested"]["token"] == "[REDACTED]"


# ---------------------------------------------------------------------------
# CSRF
# ---------------------------------------------------------------------------

def test_csrf_origin_check_blocks_untrusted_origins():
    resp = client.post(
        "/api/convert",
        json={"url": "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"},
        headers={"origin": "http://evil-phishing-site.com"},
    )
    assert resp.status_code == 403
    assert "CSRF" in resp.json()["detail"]


def test_csrf_origin_check_allows_trusted_origins():
    fake_tracks = [{"title": "Song", "artist": "Artist", "id": "1"}]
    fake_result = {
        "source_platform": "Spotify",
        "target_platform": "youtube_music",
        "tracks": fake_tracks,
        "stats": {
            "total": 1, "matched": 1, "failed": 0, "match_rate": 1.0,
            "avg_confidence": 1.0, "high_confidence": 1,
            "medium_confidence": 0, "low_confidence": 0,
        },
    }
    with patch("main.converter.convert", return_value=fake_result), \
         patch("main.session_manager.save_session", return_value="sess_test123"):
        resp = client.post(
            "/api/convert",
            json={"url": "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"},
            headers={"origin": "http://localhost:5173"},
        )
        assert resp.status_code == 200


def test_csrf_missing_origin_and_referer_with_session_cookie_rejected():
    """State-changing request with session cookie but no Origin/Referer is rejected."""
    resp = client.post(
        "/api/convert",
        json={"url": "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"},
        headers={},
        cookies={SESSION_COOKIE_NAME: "sess_fake_1234567890abcdef"},
    )
    assert resp.status_code == 403
    assert "CSRF" in resp.json()["detail"]


def test_csrf_missing_origin_and_referer_without_session_cookie_allowed():
    """Pure API call with no session cookie passes through CSRF middleware."""
    fake_result = {
        "source_platform": "Spotify",
        "target_platform": "youtube_music",
        "tracks": [{"title": "T", "artist": "A", "id": "1"}],
        "stats": {
            "total": 1, "matched": 1, "failed": 0, "match_rate": 1.0,
            "avg_confidence": 1.0, "high_confidence": 1,
            "medium_confidence": 0, "low_confidence": 0,
        },
    }
    with patch("main.converter.convert", return_value=fake_result), \
         patch("main.session_manager.save_session", return_value="sess_abc"):
        resp = client.post(
            "/api/convert",
            json={"url": "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"},
            # no Origin, no Referer, no session cookie
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# OAuth state — negative cases
# ---------------------------------------------------------------------------

def test_oauth_tampered_state_rejected():
    """Callback with tampered state must be rejected."""
    mock_redis, store = _make_mock_redis()
    sm, _ = _setup_login_and_get_state(mock_redis, store)

    with patch("auth.SpotifyAuth.session_manager", sm), \
         patch("main.secure_session", sm):
        resp = client.get(
            "/api/auth/callback?code=test_code&state=TAMPERED_STATE_VALUE",
            follow_redirects=False,
        )
    assert resp.status_code == 303
    assert "error=" in resp.headers["location"]


def test_oauth_replayed_state_rejected():
    """State consumed on first use must be rejected on second use."""
    mock_redis, store = _make_mock_redis()
    sm, state = _setup_login_and_get_state(mock_redis, store)

    with patch("auth.SpotifyAuth.session_manager", sm), \
         patch("main.secure_session", sm), \
         patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "access_token": "tok_abc",
                "refresh_token": "ref_xyz",
                "expires_in": 3600,
                "scope": "playlist-modify-public",
            },
        )
        # First use — state consumed (migrate_session may error, doesn't matter)
        client.get(
            f"/api/auth/callback?code=test_code&state={state}",
            follow_redirects=False,
        )
        # Second use must fail
        resp2 = client.get(
            f"/api/auth/callback?code=test_code&state={state}",
            follow_redirects=False,
        )
    assert resp2.status_code == 303
    assert "error=" in resp2.headers["location"]


def test_oauth_expired_state_rejected():
    """State deleted from Redis (simulating TTL expiry) must be rejected."""
    mock_redis, store = _make_mock_redis()
    sm = SecureSessionManager(redis_client=mock_redis)
    sm.store_oauth_pending_state("expired_state_abc", "sess_x", "verifier_x", ttl=1)
    store.clear()  # simulate expiry

    with patch("auth.SpotifyAuth.session_manager", sm), \
         patch("main.secure_session", sm):
        resp = client.get(
            "/api/auth/callback?code=test_code&state=expired_state_abc",
            follow_redirects=False,
        )
    assert resp.status_code == 303
    assert "error=" in resp.headers["location"]


def test_oauth_state_from_different_session_rejected():
    """State bound to session A must not be usable with session B cookie."""
    mock_redis, store = _make_mock_redis()
    sm = SecureSessionManager(redis_client=mock_redis)
    state = generate_state(32)
    sm.store_oauth_pending_state(state, "sess_A_1234567890abcdef", "verifier_x")

    with patch("auth.SpotifyAuth.session_manager", sm), \
         patch("main.secure_session", sm), \
         patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "access_token": "tok",
                "refresh_token": "ref",
                "expires_in": 3600,
                "scope": "playlist-modify-public",
            },
        )
        resp = client.get(
            f"/api/auth/callback?code=test_code&state={state}",
            follow_redirects=False,
            cookies={SESSION_COOKIE_NAME: "sess_B_9999999999abcdef"},
        )
    assert resp.status_code == 303
    assert "error=" in resp.headers["location"]


# ---------------------------------------------------------------------------
# Cookie flags
# ---------------------------------------------------------------------------

def test_callback_sets_correct_cookie_flags():
    """Successful callback must set httpOnly + SameSite=lax cookie."""
    mock_redis, store = _make_mock_redis()
    sm, state = _setup_login_and_get_state(mock_redis, store)

    with patch("auth.SpotifyAuth.session_manager", sm), \
         patch("main.secure_session", sm), \
         patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "access_token": "tok_abc",
                "refresh_token": "ref_xyz",
                "expires_in": 3600,
                "scope": "playlist-modify-public",
            },
        )
        resp = client.get(
            f"/api/auth/callback?code=test_code&state={state}",
            follow_redirects=False,
        )

    set_cookie = resp.headers.get("set-cookie", "")
    assert SESSION_COOKIE_NAME in set_cookie
    assert "httponly" in set_cookie.lower()
    assert "samesite=lax" in set_cookie.lower()


def test_auth_start_sets_cookie_and_redirects_to_spotify():
    """/api/auth/start must set the session cookie *and* redirect to Spotify."""
    mock_redis, store = _make_mock_redis()
    sm = SecureSessionManager(redis_client=mock_redis)

    with patch("auth.SpotifyAuth.session_manager", sm), \
         patch("main.secure_session", sm):
        resp = client.get("/api/auth/start", follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["location"].startswith("https://accounts.spotify.com/authorize")
    set_cookie = resp.headers.get("set-cookie", "")
    assert SESSION_COOKIE_NAME in set_cookie
    assert "httponly" in set_cookie.lower()

    # The cookie must be the session the state is bound to, otherwise the
    # callback cannot validate the binding.
    cookie = client.cookies.get(SESSION_COOKIE_NAME)
    state_key = next(k for k in store if k.startswith("oauth_state:"))
    assert json.loads(store[state_key])["session_id"] == cookie


def test_callback_without_session_cookie_rejected():
    """A state bound to a session is unusable without that session's cookie."""
    mock_redis, store = _make_mock_redis()
    sm = SecureSessionManager(redis_client=mock_redis)
    state = generate_state(32)
    sm.store_oauth_pending_state(state, "sess_bound_to_someone_else", "verifier_x")

    with patch("auth.SpotifyAuth.session_manager", sm), \
         patch("main.secure_session", sm), \
         patch("requests.post") as mock_post:
        resp = client.get(
            f"/api/auth/callback?code=test_code&state={state}",
            follow_redirects=False,
        )

    mock_post.assert_not_called()  # must never reach the token exchange
    assert resp.status_code == 303
    assert "error=" in resp.headers["location"]


def test_config_exposes_backend_origin():
    resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["auth_start_url"].endswith("/api/auth/start")
    assert data["auth_callback_url"].endswith("/api/auth/callback")
    assert "client_secret" not in json.dumps(data).lower()


# ---------------------------------------------------------------------------
# Session ID length
# ---------------------------------------------------------------------------
def test_long_random_ids_replace_4digit_codes():
    sm = SessionManager()
    with patch.object(sm.redis_client, "exists", return_value=False):
        code = sm.generate_code()
        assert len(code) >= 16
        assert not code.isdigit()


# ---------------------------------------------------------------------------
# Production startup guard (1a-e)
# ---------------------------------------------------------------------------

def test_production_env_requires_encryption_key(monkeypatch, tmp_path):
    """TokenCrypto must raise RuntimeError in production if no key is configured."""
    monkeypatch.delenv("AUXSHARE_ENCRYPTION_KEYS", raising=False)
    monkeypatch.delenv("ENCRYPTION_KEYS", raising=False)
    monkeypatch.delenv("AUXSHARE_SECRET_KEY", raising=False)
    monkeypatch.setenv("AUXSHARE_ENV", "production")

    # Patch the secret file path so it can't fall back to the dev file on disk
    import security.crypto as crypto_mod
    with patch.object(crypto_mod, "os") as mock_os:
        mock_os.getenv.side_effect = lambda k, default=None: {
            "AUXSHARE_ENCRYPTION_KEYS": None,
            "ENCRYPTION_KEYS": None,
            "AUXSHARE_SECRET_KEY": None,
            "AUXSHARE_ENV": "production",
            "ENVIRONMENT": "production",
        }.get(k, default)
        mock_os.path = __import__("os").path
        mock_os.path.exists = lambda p: False  # no dev key file

        with pytest.raises(RuntimeError, match="AUXSHARE_ENCRYPTION_KEYS"):
            crypto_mod.TokenCrypto()
