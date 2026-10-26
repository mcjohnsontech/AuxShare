# backend/main.py
import os
import re
import urllib.parse
import logging
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Response, Depends, logger
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from redis.exceptions import RedisError

from universal_converter import UniversalConverter
from platform_detector import PlatformDetector
from session_manager import SessionManager
from auth import SpotifyAuth, get_redirect_uri, get_public_backend_url
from security.csrf import default_csrf
from security.session import SecureSessionManager, SESSION_COOKIE_NAME
from security.redaction import SensitiveDataLogFilter, redact_sensitive_string
from jobs.models import JobStatus, JobTrackStatus
from jobs.manager import JobManager
from jobs.review import ReviewService
from jobs.events import ReviewEventLogger
from jobs.orchestrator import JobOrchestrator
from jobs.queue import JobQueue

# Attach log sanitization filter to root logger
logging.getLogger().addFilter(SensitiveDataLogFilter())


class _QueryParamRedactFilter(logging.Filter):
    """Strip `code=` and `state=` query params from access log lines."""

    _PATTERN = re.compile(r'([?&])(code|state)=[^&\s"\']+', re.IGNORECASE)

    def _redact(self, value: str) -> str:
        return self._PATTERN.sub(r'\1\2=[REDACTED]', value)

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            # uvicorn's AccessFormatter unpacks record.args as a 5-tuple
            # (client_addr, method, full_path, http_version, status_code).
            # Rewriting the message and emptying args breaks that unpacking,
            # so redact the path in place instead.
            if isinstance(record.args, tuple) and len(record.args) == 5:
                client, method, path, http_version, status = record.args
                if isinstance(path, str):
                    record.args = (client, method, self._redact(path), http_version, status)
                return True

            if record.args:
                msg = record.getMessage()
                redacted = self._redact(msg)
                if redacted != msg:
                    record.msg = redacted
                    record.args = ()
            else:
                record.msg = self._redact(str(record.msg))
        except Exception:
            pass
        return True


_redact_filter = _QueryParamRedactFilter()
# Apply to uvicorn access and error loggers so request paths are sanitised
for _log_name in ("uvicorn.access", "uvicorn", "uvicorn.error", "fastapi"):
    logging.getLogger(_log_name).addFilter(_redact_filter)

tags_metadata = [
    {
        "name": "Conversion",
        "description": "Convert playlists between platforms",
    },
    {
        "name": "Sessions",
        "description": "Manage conversion sessions",
    },
    {
        "name": "Authentication",
        "description": "OAuth authentication for Spotify",
    },
    {
        "name": "Export",
        "description": "Export converted playlists to target platforms",
    },
    {
        "name": "Health",
        "description": "Health check endpoints",
    },
]

app = FastAPI(
    title="AuxParty API - Secure Playlist Converter",
    description="Convert playlists between music platforms with precision matching. "
                "Supports Spotify, YouTube Music, Apple Music (as target), and Manual Import.",
    version="2.1.0",
    openapi_tags=tags_metadata,
    docs_url="/swagger",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
allowed_origins = [
    frontend_url,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CSRF Protection Middleware for state-changing endpoints
@app.middleware("http")
async def csrf_protect_middleware(request: Request, call_next):
    try:
        default_csrf.validate_request(request)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    response = await call_next(request)
    return response

# Initialize services
converter = UniversalConverter()
detector = PlatformDetector()
session_manager = SessionManager()
secure_session = SecureSessionManager()
job_manager = JobManager(session_manager.redis_client)
review_service = ReviewService(job_manager)
review_logger = ReviewEventLogger(session_manager.redis_client)
job_orchestrator = JobOrchestrator(job_manager, converter, detector, session_manager)
job_queue = JobQueue(session_manager.redis_client)

# Models
class ConvertRequest(BaseModel):
    url: str
    target_platform: str = "youtube_music"

class PlatformInfo(BaseModel):
    name: str
    display_name: str
    icon: str
    can_extract: Optional[bool] = None

class MatchStats(BaseModel):
    total: int
    matched: int
    failed: int
    match_rate: float
    avg_confidence: float
    high_confidence: int
    medium_confidence: int
    low_confidence: int

class ConvertResponse(BaseModel):
    code: str
    share_url: str
    source_platform: str
    target_platform: str
    stats: MatchStats

class SessionResponse(BaseModel):
    tracks: List[dict]
    target_platform: str
    source_platform: Optional[str] = None
    stats: MatchStats

class ExportRequest(BaseModel):
    session_code: str
    target_platform: str
    access_token: Optional[str] = None
    playlist_name: Optional[str] = "AuxParty Session"
    # Export is idempotent per (Spotify account, target platform, session).
    # Set this only when the user explicitly asks for another copy.
    force_new: bool = False

@app.get("/")
async def root():
    return {
        "message": "AuxParty API - Share music across any platform!",
        "version": "2.1",
        "features": ["Spotify", "YouTube Music", "Apple Music (FREE)", "Manual Import"],
        "security": "PKCE + Server-side Encrypted Sessions + CSRF Protection"
    }

@app.get("/api/platforms", response_model=List[PlatformInfo])
async def get_platforms():
    """Get list of all supported platforms"""
    return detector.get_supported_platforms()

@app.get("/api/platforms/sources", response_model=List[PlatformInfo])
async def get_source_platforms():
    """Get platforms that can be used as source"""
    return detector.get_supported_sources()

@app.get("/api/platforms/targets", response_model=List[PlatformInfo])
async def get_target_platforms():
    """Get platforms that can be used as target"""
    return detector.get_supported_targets()

@app.post("/api/convert", response_model=ConvertResponse)
async def convert_playlist(request: ConvertRequest):
    """
    Convert a playlist from one platform to another
    """
    try:
        print(f"\n🔄 New conversion request:")
        print(f"   URL: {request.url}")
        print(f"   Target: {request.target_platform}\n")
        
        # Detect source platform
        source_platform_name = "unknown"
        try:
            det = detector.detect_platform(request.url)
            if det:
                source_platform_name = det['name']
        except Exception:
            pass
        
        # Create job first (orchestration)
        job = job_manager.create_job(
            source_url=request.url,
            source_platform=source_platform_name,
            target_platform=request.target_platform,
            market="US"
        )
        job_manager.update_job_status(job.id, JobStatus.MATCHING)
        
        # Convert playlist
        result = converter.convert(request.url, request.target_platform)
        
        # Save session with BOTH source and target platform info (for backwards compat)
        code = session_manager.save_session(
            tracks=result['tracks'],
            target_platform=request.target_platform,
            source_platform=result['source_platform']
        )
        
        # Add tracks to job
        job_manager.add_tracks_to_job(job.id, result['tracks'])
        job_manager.update_job_status(job.id, JobStatus.COMPLETE)
        
        # Enqueue for async processing if workers available
        try:
            job_queue.enqueue(job.id, {"session_code": code})
        except Exception:
            pass
        
        # Build share URL
        share_url = f"{frontend_url}/join/{code}"
        
        print(f"\n✅ Conversion complete!")
        print(f"   Session code: {code}")
        print(f"   Job ID: {job.id}")
        print(f"   Match rate: {result['stats']['match_rate']:.1%}\n")
        
        return ConvertResponse(
            code=code,
            share_url=share_url,
            source_platform=result['source_platform'],
            target_platform=result['target_platform'],
            stats=MatchStats(**result['stats'])
        )
        
    except ValueError as e:
        print(f"❌ Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        print(f"❌ Server error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to convert playlist: {str(e)}"
        )

@app.get("/api/session/{code}", response_model=SessionResponse)
async def get_session(code: str, req: Request):
    """
    Retrieve a saved session by code (supports long IDs and legacy codes).

    1a-b: Rate-limited per IP (30 lookups per 60 s) to prevent enumeration.
    Legacy 4-digit numeric codes are deprecated (removal after 2026-12-01).
    """
    # IP-based rate limiting using Redis. Fail open when Redis is unavailable so
    # a cache outage does not turn every lookup into an unhandled 500. Session
    # retrieval below still reports a clear 503 if Redis remains unreachable.
    client_ip = req.client.host if req.client else "unknown"
    rate_key = f"rate:session_lookup:{client_ip}"
    try:
        count = session_manager.redis_client.incr(rate_key)
        if count == 1:
            session_manager.redis_client.expire(rate_key, 60)
        if count > 30:
            raise HTTPException(
                status_code=429,
                detail="Too many session lookup requests. Please wait before retrying."
            )
    except RedisError:
        logging.getLogger(__name__).warning(
            "Redis unavailable; skipping session lookup rate limiting"
        )

    # Legacy 4-digit code deprecation warning
    if len(code) == 4 and code.isdigit():
        logging.getLogger(__name__).warning(
            "Legacy 4-digit session code lookup attempted (code length=4). "
            "Support for 4-digit codes will be removed on 2026-12-01."
        )

    try:
        session_data = session_manager.get_session(code)
    except RedisError:
        logging.getLogger(__name__).error(
            "Redis unavailable while retrieving session %s", code
        )
        raise HTTPException(
            status_code=503,
            detail="Session storage is temporarily unavailable. Please try again."
        )

    if not session_data:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired (sessions last 24 hours)"
        )
    
    tracks = session_data.get('tracks', [])
    target_platform = session_data.get('target_platform', 'youtube_music')
    source_platform = session_data.get('source_platform')
    
    # Recalculate stats
    stats = converter._calculate_stats(tracks, target_platform)
    
    return SessionResponse(
        tracks=tracks,
        target_platform=target_platform,
        source_platform=source_platform,
        stats=MatchStats(**stats)
    )

@app.get("/api/session/{code}/ttl")
async def get_session_ttl(code: str):
    """Get remaining time for a session"""
    if not session_manager.session_exists(code):
        raise HTTPException(status_code=404, detail="Session not found")
    
    ttl = session_manager.get_session_ttl(code)
    
    return {
        "code": code,
        "ttl_seconds": ttl,
        "ttl_hours": round(ttl / 3600, 1),
        "expires_in": f"{ttl // 3600}h {(ttl % 3600) // 60}m"
    }

# ----------------- Security: Authentication Endpoints -----------------

@app.get("/api/config")
async def client_config():
    """Public configuration the browser needs (no secrets)."""
    backend_url = get_public_backend_url()
    return {
        "backend_url": backend_url,
        "auth_start_url": f"{backend_url}/api/auth/start",
        "auth_callback_url": get_redirect_uri(),
    }


@app.get("/api/auth/start")
async def start_spotify_auth(request: Request):
    """Begin Spotify OAuth on the backend origin.

    This endpoint is reached by a top-level browser navigation (not XHR) so the
    session cookie is issued for the same origin Spotify will redirect back to.
    That makes the state-to-session binding verifiable in the callback.
    """
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id or len(session_id) < 16:
        session_id = secure_session.generate_session_id()

    auth_data = SpotifyAuth.get_auth_url(session_id)
    redirect_response = RedirectResponse(url=auth_data["url"], status_code=302)
    secure_session.set_session_cookie(redirect_response, session_id)
    return redirect_response


@app.get("/api/auth/login")
async def login_spotify(request: Request, response: Response):
    """
    Initiate Spotify OAuth 2.0 with PKCE and state bound to session cookie.
    """
    session_id = secure_session.get_or_create_session_id(request, response)
    auth_data = SpotifyAuth.get_auth_url(session_id)
    return {"url": auth_data["url"]}

@app.get("/api/auth/callback")
async def callback_spotify(request: Request, code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    """
    Handle Spotify OAuth callback using PKCE:
    - Validates state
    - Exchanges code with code_verifier
    - Stores encrypted tokens server-side
    - Sets httpOnly session cookie
    - Redirects cleanly without exposing tokens
    """
    if error:
        return RedirectResponse(
            url=f"{frontend_url}/callback?error={urllib.parse.quote(error)}",
            status_code=303
        )

    if not code or not state:
        return RedirectResponse(
            url=f"{frontend_url}/callback?error={urllib.parse.quote('Missing OAuth code or state parameter')}",
            status_code=303
        )

    try:
        old_session_id = request.cookies.get(SESSION_COOKIE_NAME) or ""
        result = SpotifyAuth.exchange_code(code, state, old_session_id)

        # 1a-d: Session fixation defence — rotate session ID after login so
        # a pre-auth session ID cannot be reused by an attacker.
        old_stored_session = result["session_id"]
        new_session_id = secure_session.generate_session_id()
        SpotifyAuth.session_manager.migrate_session(old_stored_session, new_session_id)

        # The callback usually runs on the backend origin (e.g.
        # http://127.0.0.1:8000) while the app lives on another origin
        # (e.g. http://localhost:5173). Cookies are origin-scoped, so a cookie
        # set here would never be sent by the frontend. Issue a single-use
        # handoff code and let the frontend exchange it on its own origin.
        handoff_code = secure_session.store_auth_handoff(new_session_id)

        redirect_response = RedirectResponse(
            url=f"{frontend_url}/callback?status=success&handoff={urllib.parse.quote(handoff_code)}",
            status_code=303
        )
        # Also set the cookie for the (rare) same-origin deployment.
        secure_session.set_session_cookie(redirect_response, new_session_id)
        return redirect_response


    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception("Spotify OAuth callback failed: %s", type(e).__name__)

        # Surface the actionable reasons; keep anything else generic so we never
        # leak internals or credentials into a URL.
        detail = getattr(e, "detail", None)
        if isinstance(detail, str) and detail in {
            "OAuth state does not match session.",
            "Invalid or expired OAuth state parameter.",
            "OAuth state is not bound to a session.",
        }:
            err_msg = (
                "This Spotify sign-in link is invalid or expired, or it was "
                "started in a different browser. Please press Connect Spotify "
                "again."
            )
        elif isinstance(detail, str) and detail.startswith("Spotify token exchange failed"):
            err_msg = (
                "Spotify rejected the sign-in attempt. Please try connecting "
                "again."
            )
        else:
            err_msg = "Spotify authentication failed. Check backend logs."

        return RedirectResponse(
            url=f"{frontend_url}/callback?error="
            f"{urllib.parse.quote(err_msg)}",
            status_code=303,
        )

@app.post("/api/auth/handoff")
async def auth_handoff(payload: dict, response: Response):
    """Adopt a session created on the OAuth callback origin.

    Cookies are scoped to the origin that set them, and the Spotify callback
    runs on the backend origin. The callback redirects to the frontend with a
    short-lived single-use code; the frontend posts it here (same-origin, via
    the nginx proxy) so the session cookie is issued for the frontend origin.
    """
    code = (payload or {}).get("code")
    session_id = secure_session.consume_auth_handoff(code) if code else None
    if not session_id:
        raise HTTPException(status_code=400, detail="Invalid or expired auth handoff code")
    secure_session.set_session_cookie(response, session_id)
    return {"status": "ok"}


@app.get("/api/auth/status")
async def auth_status(request: Request):
    """Check if the current session has authenticated credentials for target platforms."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    has_spotify = False
    if session_id:
        tokens = secure_session.get_user_tokens(session_id, "spotify")
        has_spotify = bool(tokens)
    return {
        "authenticated": has_spotify,
        "platforms": {
            "spotify": has_spotify
        }
    }

@app.post("/api/export")
async def export_playlist(request: ExportRequest, req: Request):
    """Export session to a real playlist with server-side token management."""
    try:
        # 1. Get Session
        session = session_manager.get_session(request.session_code)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
            
        tracks = session['tracks']
        
        # 2. Get Platform Handler
        if request.target_platform != 'spotify':
            raise HTTPException(status_code=400, detail="Only Spotify export is supported currently")
            
        platform = detector.get_platform('spotify')
        
        # 3. Resolve Access Token (prefer server-side encrypted token; fallback to body token)
        access_token = request.access_token
        if not access_token:
            session_id = req.cookies.get(SESSION_COOKIE_NAME)
            if session_id:
                user_tokens = secure_session.get_user_tokens(session_id, "spotify")
                if user_tokens:
                    if user_tokens.get("is_expired") and user_tokens.get("refresh_token"):
                        try:
                            access_token = SpotifyAuth.refresh_user_token(session_id)
                        except Exception:
                            raise HTTPException(
                                status_code=401,
                                detail="Spotify authorization expired. Please log in again."
                            )
                    else:
                        access_token = user_tokens.get("access_token")

        if not access_token:
            raise HTTPException(
                status_code=401,
                detail="Spotify authorization required. Please authenticate via /api/auth/login"
            )

        # 4. Resolve the Spotify account so the idempotency key is per user.
        from export_idempotency import ExportIdempotency

        try:
            account_id = platform.get_current_user_id(access_token)
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"Could not identify the Spotify account: {e}"
            )

        idem = ExportIdempotency(session_manager.redis_client)
        marker = f"converted-by-auxshare:session_{request.session_code}"

        stored = idem.get_record(account_id, request.target_platform, request.session_code)
        # force_new deliberately ignores any existing export for this session.
        playlist_id = None if request.force_new else (stored or {}).get("playlist_id")
        created_new = False

        # Fast path: this session was already fully exported to this account.
        # Return the existing playlist without touching Spotify again.
        if playlist_id and stored.get("completed") and not request.force_new:
            known_tracks = stored.get("tracks_added", 0)
            try:
                live_count = platform.get_playlist_track_count(access_token, playlist_id)
            except Exception:
                # Could not verify (network/auth): keep trusting the record so a
                # hiccup cannot produce a duplicate playlist.
                live_count = known_tracks
            if live_count is not None:
                return {
                    "success": True,
                    "playlist_url": f"https://open.spotify.com/playlist/{playlist_id}",
                    "playlist_id": playlist_id,
                    "created_new": False,
                    "already_existed": True,
                    "tracks_added": 0,
                    "tracks_in_playlist": live_count,
                    "tracks_requested": len(tracks),
                    "tracks_matched": known_tracks,
                    "failed": max(len(tracks) - known_tracks, 0),
                    "status": "complete",
                }
            # The playlist was deleted on Spotify: fall through and make a new one.
            idem.clear_record(account_id, request.target_platform, request.session_code)
            playlist_id = None

        if not playlist_id and not request.force_new:
            # Recovery path for playlists created before export records existed.
            try:
                found = platform.find_playlist_by_marker(access_token, marker)
            except Exception:
                found = None
            if isinstance(found, str) and found:
                playlist_id = found
                idem.save_record(
                    account_id, request.target_platform, request.session_code,
                    playlist_id, completed=False
                )

        if not playlist_id:
            if not idem.acquire_lock(account_id, request.target_platform, request.session_code):
                raise HTTPException(
                    status_code=409,
                    detail="This playlist is already being created. Please wait a moment and try again."
                )
            try:
                # Double-checked: another request may have finished while we
                # waited for the lock. Never applies when a new copy was asked for.
                if not request.force_new:
                    stored = idem.get_record(account_id, request.target_platform, request.session_code)
                    playlist_id = (stored or {}).get("playlist_id")

                if not playlist_id:
                    playlist_id = platform.create_playlist(
                        access_token,
                        request.playlist_name,
                        f"Created with AuxParty 🎵 {marker}"
                    )
                    created_new = True
                    # Persist immediately so a crash mid-add cannot duplicate it.
                    idem.save_record(
                        account_id, request.target_platform, request.session_code,
                        playlist_id, completed=False
                    )
            finally:
                idem.release_lock(account_id, request.target_platform, request.session_code)

        # 5. Search & Add Tracks
        real_uris = []
        for track in tracks:
            # If we have a spotify ID, use it
            if session.get('target_platform') == 'spotify' and track.get('id'):
                real_uris.append(f"spotify:track:{track['id']}")
                continue
                
            # Otherwise, quick search
            try:
                result = platform.match_track(track)
                if result and result.get('id'):
                    real_uris.append(f"spotify:track:{result['id']}")
            except Exception:
                continue

        # Only add tracks that are not already in the playlist, so re-clicking
        # Export cannot append a second copy of every song.
        existing_uris = set()
        if not created_new:
            # This playlist predates this request, so it may already hold tracks.
            # If we cannot read them, adding blindly would duplicate songs, so we
            # stop and report instead (a retry re-reads the playlist).
            try:
                existing_uris = set(platform.get_playlist_track_uris(access_token, playlist_id))
            except Exception as e:
                raise HTTPException(
                    status_code=502,
                    detail=(
                        "Could not verify which tracks are already in this playlist, "
                        f"so nothing was added (to avoid duplicates). Please try again. ({e})"
                    )
                )

        desired_uris = []
        seen = set()
        for uri in real_uris:
            if uri in seen:
                continue
            seen.add(uri)
            if uri not in existing_uris:
                desired_uris.append(uri)
        
        # 6. Add to Playlist in batches
        added = 0
        if desired_uris:
            try:
                platform.add_tracks_to_playlist(access_token, playlist_id, desired_uris)
                added = len(desired_uris)
            except Exception as e:
                # On permanent failure, provide CSV fallback
                import csv
                import io
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(['title', 'artist', 'album', 'spotify_uri', 'target_url'])
                for i, track in enumerate(tracks):
                    if i < len(real_uris):
                        uri = real_uris[i]
                        if isinstance(uri, str) and uri.startswith('spotify:track:'):
                            url = f"https://open.spotify.com/track/{uri.split(':')[-1]}"
                        else:
                            url = track.get('spotify_url') or ''
                        writer.writerow([
                            track.get('title', ''),
                            track.get('artist') or track.get('artists', ''),
                            track.get('album', ''),
                            uri,
                            url
                        ])
                    else:
                        writer.writerow([
                            track.get('title', ''),
                            track.get('artist') or track.get('artists', ''),
                            track.get('album', ''),
                            '',
                            track.get('spotify_url', '')
                        ])
                csv_content = output.getvalue()
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to add tracks to playlist: {str(e)}. CSV fallback:\n{csv_content}"
                )
            
        # 7. Read-back verification (basic)
        try:
            import requests
            headers = {'Authorization': f'Bearer {access_token}'}
            resp = requests.get(f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks?fields=total&limit=1', headers=headers)
            if resp.status_code == 200:
                total = resp.json().get('total', added)
            else:
                total = len(existing_uris) + added
        except Exception:
            total = len(existing_uris) + added

        # Record completion so future clicks are fully idempotent.
        try:
            idem.save_record(
                account_id, request.target_platform, request.session_code,
                playlist_id, completed=True, tracks_added=total
            )
        except Exception:
            pass

        return {
            "success": True,
            "playlist_url": f"https://open.spotify.com/playlist/{playlist_id}",
            "playlist_id": playlist_id,
            "created_new": created_new,
            "already_existed": not created_new,
            "tracks_added": added,
            "tracks_in_playlist": total,
            "tracks_requested": len(tracks),
            "tracks_matched": len(real_uris),
            "failed": len(tracks) - len(real_uris),
            "status": "complete"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/status")
async def export_status(req: Request, session_code: str, target_platform: str = "spotify"):
    """Report whether the current Spotify user already exported this session.

    Used by the UI to disable the Export button once a playlist exists. The
    answer is scoped to the signed-in Spotify account and verified against
    Spotify, so a deleted playlist re-enables the button.
    """
    if target_platform != 'spotify':
        raise HTTPException(status_code=400, detail="Only Spotify export is supported currently")

    from export_idempotency import ExportIdempotency

    session_id = req.cookies.get(SESSION_COOKIE_NAME)
    user_tokens = secure_session.get_user_tokens(session_id, "spotify") if session_id else None
    if not user_tokens:
        return {"authenticated": False, "exported": False, "playlist_id": None, "playlist_url": None}

    access_token = user_tokens.get("access_token")
    if user_tokens.get("is_expired") and user_tokens.get("refresh_token"):
        try:
            access_token = SpotifyAuth.refresh_user_token(session_id)
        except Exception:
            return {"authenticated": False, "exported": False, "playlist_id": None, "playlist_url": None}

    platform = detector.get_platform('spotify')
    try:
        account_id = platform.get_current_user_id(access_token)
    except Exception:
        # Token is unusable; let the UI treat the user as signed out.
        return {"authenticated": False, "exported": False, "playlist_id": None, "playlist_url": None}

    idem = ExportIdempotency(session_manager.redis_client)
    stored = idem.get_record(account_id, target_platform, session_code)
    playlist_id = (stored or {}).get("playlist_id")
    if not (stored and stored.get("completed") and playlist_id):
        return {
            "authenticated": True,
            "exported": False,
            "playlist_id": None,
            "playlist_url": None,
        }

    try:
        live_count = platform.get_playlist_track_count(access_token, playlist_id)
    except Exception:
        # Cannot verify right now: trust the record rather than re-enable
        # Export and risk creating a duplicate playlist.
        live_count = stored.get("tracks_added", 0)

    if live_count is None:
        # Playlist was deleted on Spotify; allow a fresh export.
        idem.clear_record(account_id, target_platform, session_code)
        return {
            "authenticated": True,
            "exported": False,
            "playlist_id": None,
            "playlist_url": None,
        }

    return {
        "authenticated": True,
        "exported": True,
        "playlist_id": playlist_id,
        "playlist_url": f"https://open.spotify.com/playlist/{playlist_id}",
        "tracks_in_playlist": live_count,
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "redis": session_manager.redis_client.ping(),
        "platforms": len(detector.get_supported_platforms())
    }


# ----------------- Jobs & Review API -----------------

class CreateJobRequest(BaseModel):
    source_url: str
    target_platform: str = "spotify"
    market: str = "US"


@app.post("/api/jobs")
async def create_job(request: CreateJobRequest):
    source_platform = "unknown"
    try:
        det = detector.detect_platform(request.source_url)
        if det:
            source_platform = det['name']
    except Exception:
        pass
    job = job_manager.create_job(
        source_url=request.source_url,
        source_platform=source_platform,
        target_platform=request.target_platform,
        market=request.market
    )
    return {
        "job_id": job.id,
        "status": job.status.value,
        "source_platform": job.source_platform,
        "target_platform": job.target_platform,
        "playlist_marker": job.playlist_marker,
        "created_at": job.created_at.isoformat()
    }


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "status": job.status.value,
        "source_platform": job.source_platform,
        "target_platform": job.target_platform,
        "playlist_id": job.playlist_id,
        "playlist_url": job.playlist_url,
        "counts": job.get_counts(),
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat()
    }


@app.get("/api/jobs/{job_id}/review")
async def get_job_review(job_id: str):
    review_queue = review_service.get_review_queue(job_id)
    return {"tracks": review_queue, "count": len(review_queue)}


@app.post("/api/jobs/{job_id}/tracks/{track_id}/select")
async def select_track(job_id: str, track_id: str, body: dict):
    target_id = body.get("target_id")
    skip = body.get("skip", False)
    job = job_manager.get_job(job_id)
    if job:
        for track in job.tracks:
            if track.id == track_id and track.status.value in ["user_selected", "user_skipped"]:
                return {"success": True, "idempotent": True}
    success = review_service.select_track(job_id, track_id, target_id, skip)
    if success and job:
        candidates = []
        for track in job.tracks:
            if track.id == track_id:
                candidates = track.candidates
                break
        review_logger.log_event(job_id, track_id, candidates, target_id if not skip else None)
    return {"success": success}


@app.post("/api/jobs/{job_id}/accept-top")
async def accept_top(job_id: str):
    success = review_service.accept_top_picks(job_id)
    return {"success": success}


@app.get("/api/search")
async def search_tracks(q: str, platform: str = "spotify"):
    plat = detector.get_platform(platform)
    if not plat:
        raise HTTPException(status_code=400, detail="Unsupported platform")
    try:
        if hasattr(plat, 'search_by_metadata'):
            results = plat.search_by_metadata(q, "")
        else:
            results = []
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/{job_id}/resume")
async def resume_job(job_id: str):
    result = job_orchestrator.resume_if_needed(job_id)
    return result


@app.get("/api/jobs/{job_id}/finalize")
async def finalize_job(job_id: str):
    result = job_orchestrator.ensure_terminal_state(job_id)
    return result

# SSE endpoint for job progress
from fastapi.responses import StreamingResponse
import asyncio
import json

@app.get("/api/jobs/{job_id}/stream")
async def stream_job_progress(job_id: str):
    async def event_generator():
        for _ in range(60):  # Stream for up to 60 seconds
            job = job_manager.get_job(job_id)
            if not job:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break
            yield f"data: {json.dumps({'status': job.status.value, 'counts': job.get_counts()})}\n\n"
            if job.status.value in ['complete', 'failed_permanent']:
                break
            await asyncio.sleep(2)
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
