# backend/main.py
import os
import re
import urllib.parse
import logging
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from redis.exceptions import RedisError

from universal_converter import UniversalConverter
from platform_detector import PlatformDetector
from session_manager import SessionManager
from auth import SpotifyAuth
from security.csrf import default_csrf
from security.session import SecureSessionManager, SESSION_COOKIE_NAME
from security.redaction import SensitiveDataLogFilter, redact_sensitive_string
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

    def filter(self, record: logging.LogRecord) -> bool:
        if record.args:
            try:
                msg = record.getMessage()
                redacted = self._PATTERN.sub(r'\1\2=[REDACTED]', msg)
                if redacted != msg:
                    record.msg = redacted
                    record.args = ()
            except Exception:
                pass
        else:
            record.msg = self._PATTERN.sub(r'\1\2=[REDACTED]', str(record.msg))
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

        redirect_response = RedirectResponse(
            url=f"{frontend_url}/callback?status=success",
            status_code=303
        )
        secure_session.set_session_cookie(redirect_response, new_session_id)
        return redirect_response

    except Exception as e:
        err_msg = redact_sensitive_string(str(e))
        return RedirectResponse(
            url=f"{frontend_url}/callback?error={urllib.parse.quote(err_msg)}",
            status_code=303
        )

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

        # 4. Create Playlist with marker for resumability
        from jobs.manager import JobManager
        job_manager = JobManager(session_manager.redis_client)
        marker = f"converted-by-auxshare:session_{request.session_code}"
        try:
            existing = platform.find_playlist_by_marker(access_token, marker)
        except Exception:
            existing = None
        if isinstance(existing, str) and existing:
            playlist_id = existing
        else:
            playlist_id = platform.create_playlist(
                access_token,
                request.playlist_name,
                f"Created with AuxParty 🎵 {marker}"
            )
        
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
        
        # 6. Add to Playlist in batches
        added = 0
        if real_uris:
            try:
                platform.add_tracks_to_playlist(access_token, playlist_id, real_uris)
                added = len(real_uris)
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
                total = added
        except Exception:
            total = added
        
        return {
            "success": True,
            "playlist_url": f"https://open.spotify.com/playlist/{playlist_id}",
            "tracks_added": added,
            "tracks_in_playlist": total,
            "tracks_requested": len(tracks),
            "failed": len(tracks) - added,
            "status": "complete"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
