# backend/jobs/models.py
from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


class JobStatus(str, Enum):
    QUEUED = "queued"
    MATCHING = "matching"
    PLAYLIST_CREATED = "playlist_created"
    ADDING_TRACKS = "adding_tracks"
    VERIFYING = "verifying"
    COMPLETE = "complete"
    AWAITING_REAUTH = "awaiting_reauth"
    FAILED_RETRYABLE = "failed_retryable"
    FAILED_PERMANENT = "failed_permanent"


class JobTrackStatus(str, Enum):
    MATCHED = "matched"
    NEEDS_REVIEW = "needs_review"
    USER_SELECTED = "user_selected"
    USER_SKIPPED = "user_skipped"
    UNMATCHED = "unmatched"
    ADDED = "added"
    FAILED = "failed"


@dataclass
class JobTrack:
    id: str
    job_id: str
    source_track: Dict[str, Any]
    status: JobTrackStatus = JobTrackStatus.MATCHED
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    selected_target_id: Optional[str] = None
    selected_at: Optional[datetime] = None
    added_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    match_tier: Optional[str] = None
    confidence: float = 0.0
    position: int = 0


@dataclass
class ConversionJob:
    id: str
    user_id: Optional[str] = None
    source_url: str = ""
    source_platform: str = ""
    target_platform: str = ""
    market: str = "US"
    status: JobStatus = JobStatus.QUEUED
    playlist_id: Optional[str] = None
    playlist_url: Optional[str] = None
    playlist_marker: Optional[str] = None
    tracks: List[JobTrack] = field(default_factory=list)
    counts: Dict[str, int] = field(default_factory=dict)
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def update_status(self, status: JobStatus):
        self.status = status
        self.updated_at = datetime.utcnow()
    
    def get_counts(self) -> Dict[str, int]:
        total = len(self.tracks)
        matched = sum(1 for t in self.tracks if t.status == JobTrackStatus.MATCHED)
        added = sum(1 for t in self.tracks if t.status == JobTrackStatus.ADDED)
        failed = sum(1 for t in self.tracks if t.status in [JobTrackStatus.FAILED, JobTrackStatus.UNMATCHED])
        skipped = sum(1 for t in self.tracks if t.status == JobTrackStatus.USER_SKIPPED)
        needs_review = sum(1 for t in self.tracks if t.status == JobTrackStatus.NEEDS_REVIEW)
        return {
            "total": total,
            "matched": matched,
            "added": added,
            "failed": failed,
            "skipped": skipped,
            "needs_review": needs_review
        }
