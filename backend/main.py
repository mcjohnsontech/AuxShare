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
        "message": "AuxParty API - Share music across any platform! 🎵",
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

@app.post("/api/convert", response_model=ConvertResponse)
async def convert_playlist(request: ConvertRequest):
    """
    Convert a playlist from one platform to another
    
    Supported conversions (FREE):
    - Spotify → YouTube Music
    - Spotify → Apple Music
    - YouTube Music → Spotify
    - YouTube Music → Apple Music
    """
    try:
        print(f"\n🔄 New conversion request:")
        print(f"   URL: {request.url}")
        print(f"   Target: {request.target_platform}\n")
        
        # Convert playlist
        result = converter.convert(request.url, request.target_platform)
        
        # Save session
        code = session_manager.save_session(result['tracks'])
        
        # Build share URL (update with your actual frontend URL)
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
        # User-friendly errors (e.g., unsupported platform)
        print(f"❌ Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        # Unexpected errors
        print(f"❌ Server error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to convert playlist: {str(e)}"
        )

@app.get("/api/session/{code}", response_model=SessionResponse)
async def get_session(code: str):
    """
    Retrieve a saved session by code
    """
    tracks = session_manager.get_session(code)
    
    if not tracks:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired (sessions last 24 hours)"
        )
    
    # Recalculate stats from stored tracks
    stats = converter._calculate_stats(tracks, 'youtube_music')  # Default platform
    
    return SessionResponse(
        tracks=tracks,
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

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "redis": session_manager.redis_client.ping(),
        "platforms": len(detector.get_supported_platforms())
    }