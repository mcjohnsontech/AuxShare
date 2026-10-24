# backend/models/canonical.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class CanonicalTrack(BaseModel):
    """Normalized cross-platform track representation."""
    sourcePlatform: str
    sourceId: str
    title: str
    baseTitle: str = ""
    versionTags: List[str] = Field(default_factory=list)
    variantTags: List[str] = Field(default_factory=list)
    artists: List[str] = Field(default_factory=list)
    primaryArtists: List[str] = Field(default_factory=list)
    featuredArtists: List[str] = Field(default_factory=list)
    album: Optional[str] = None
    durationMs: Optional[int] = None
    isrc: Optional[str] = None
    explicit: Optional[bool] = None
    previewUrl: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.baseTitle:
            self.baseTitle = self.title
        if not self.artists and self.primaryArtists:
            self.artists = list(self.primaryArtists) + list(self.featuredArtists)
        elif self.artists and not self.primaryArtists:
            self.primaryArtists = [self.artists[0]] if self.artists else []
            self.featuredArtists = self.artists[1:] if len(self.artists) > 1 else []

class TargetTrack(BaseModel):
    """Track result from a target platform."""
    targetPlatform: str
    targetId: str
    title: str
    artists: List[str] = Field(default_factory=list)
    album: Optional[str] = None
    durationMs: Optional[int] = None
    isrc: Optional[str] = None
    explicit: Optional[bool] = None
    previewUrl: Optional[str] = None
    matchMethod: Optional[str] = None
    confidence: float = 0.0
    score: Optional[float] = None
    flags: List[str] = Field(default_factory=list)
    raw: Optional[Dict[str, Any]] = None

