# backend/main.py (ADD Apple Music support)
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from universal_converter import UniversalConverter
from platform_detector import PlatformDetector
from session_manager import SessionManager

app = FastAPI(title="AuxParty API - Now with FREE Apple Music!")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
converter = UniversalConverter()
detector = PlatformDetector()
session_manager = SessionManager()

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
    stats: MatchStats

@app.get("/")
async def root():
    return {
        "message": "AuxParty API - Share music across any platform!",
        "version": "2.0",
        "features": ["Spotify", "YouTube Music", "Apple Music (FREE)"],
        "note": "Apple Music integration uses free iTunes Search API"
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

# backend/main.py (UPDATE convert endpoint)

@app.post("/api/convert", response_model=ConvertResponse)
async def convert_playlist(request: ConvertRequest):
    """
    Convert a playlist from one platform to another
    """
    try:
        print(f"\n🔄 New conversion request:")
        print(f"   URL: {request.url}")
        print(f"   Target: {request.target_platform}\n")
        
        # Convert playlist
        result = converter.convert(request.url, request.target_platform)
        
        # Save session with BOTH source and target platform info
        code = session_manager.save_session(
            tracks=result['tracks'],
            target_platform=request.target_platform,  # ✅ Pass target!
            source_platform=result['source_platform']  # ✅ Pass source!
        )
        
        # Build share URL
        share_url = f"http://localhost:5173/join/{code}"
        
        print(f"\n✅ Conversion complete!")
        print(f"   Session code: {code}")
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

        
# backend/main.py (UPDATE get_session endpoint)

class SessionResponse(BaseModel):
    tracks: List[dict]
    target_platform: str  # ✅ Make it required, not optional
    source_platform: Optional[str] = None
    stats: MatchStats

@app.get("/api/session/{code}", response_model=SessionResponse)
async def get_session(code: str):
    """
    Retrieve a saved session by code
    """
    session_data = session_manager.get_session(code)
    
    if not session_data:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired (sessions last 24 hours)"
        )
    
    # Extract data
    tracks = session_data.get('tracks', [])
    target_platform = session_data.get('target_platform', 'youtube_music')
    source_platform = session_data.get('source_platform')
    
    print(f"📤 Sending session {code}:")
    print(f"   Tracks: {len(tracks)}")
    print(f"   Target platform: {target_platform}")
    print(f"   Source platform: {source_platform}")
    
    # Recalculate stats
    stats = converter._calculate_stats(tracks, target_platform)
    
    return SessionResponse(
        tracks=tracks,
        target_platform=target_platform,  # ✅ Return it!
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

from auth import SpotifyAuth
from fastapi.responses import RedirectResponse

# ... existing imports ...

# Models
class ExportRequest(BaseModel):
    session_code: str
    target_platform: str
    access_token: str
    playlist_name: Optional[str] = "AuxParty Session"

@app.get("/api/auth/login")
async def login_spotify():
    """Redirect to Spotify Login"""
    auth_url = SpotifyAuth.get_auth_url()
    return {"url": auth_url}

@app.get("/api/auth/callback")
async def callback_spotify(code: str):
    """
    Exchange code for token and redirect context to frontend
    """
    try:
        token_data = SpotifyAuth.exchange_code(code)
        access_token = token_data['access_token']
        # Redirect to frontend with token
        return RedirectResponse(url=f"http://localhost:5173/callback?token={access_token}")
    except Exception as e:
        return RedirectResponse(url=f"http://localhost:5173/callback?error={str(e)}")

@app.post("/api/export")
async def export_playlist(request: ExportRequest):
    """Export session to a real playlist"""
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
        
        # 3. Create Playlist
        playlist_id = platform.create_playlist(
            request.access_token, 
            request.playlist_name,
            "Created with AuxParty 🎵"
        )
        
        # 4. Search & Add Tracks
        track_uris = []
        for track in tracks:
            # We need the Spotify URI. If we already matched it, we might have an ID
            # But the track object structure depends on the conversion result
            # We'll assume we need to search or use the ID if it was a direct spotify match
            
            uri = None
            if track.get('id'): # If we have a spotify ID
                 uri = f"spotify:track:{track['id']}"
            
            # If we don't have a direct ID (e.g. from YouTube), we should search
            if not uri:
                # Reuse the search logic? 
                # Ideally we should have stored the Spotify ID during conversion IF target was Spotify
                # But if target was Apple Music, we don't have Spotify IDs.
                # So we might need to search again here if IDs are missing.
                pass
            
            if uri:
                track_uris.append(uri)
                
        # For now, let's assume the tracks HAVE ids from the conversion if the target was spotify.
        # If the playlist was converted to 'spotify', the tracks list should contain spotify IDs.
        
        # But wait, 'session['tracks']' contains the RESULT of the conversion.
        # If the user converted TO Spotify, the tracks have spotify metadata.
        # If they converted TO Apple Music, they have Apple metadata.
        
        # IF we want to export to Spotify but the current session is Apple Music...
        # We technically need to RE-MATCH everything to Spotify.
        # That's a bit complex.
        
        # Simplified approach: Only allow export to the TARGET platform of the session.
        # Or, perform a quick re-match loop here.
        
        real_uris = []
        for track in tracks:
            # If we have a spotify ID, use it
            if session.get('target_platform') == 'spotify' and track.get('id'):
                real_uris.append(f"spotify:track:{track['id']}")
                continue
                
            # Otherwise, quick search
            result = platform.search_by_metadata(track['title'], track['artist'])
            if result and result.get('id'):
                real_uris.append(f"spotify:track:{result['id']}")
        
        # 5. Add to Playlist
        if real_uris:
            platform.add_tracks_to_playlist(request.access_token, playlist_id, real_uris)
            
        return {
            "success": True,
            "playlist_url": f"https://open.spotify.com/playlist/{playlist_id}",
            "tracks_added": len(real_uris)
        }
        
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