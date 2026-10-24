# backend/jobs/manager.py
import json
import os
import secrets
import time
from typing import Optional, List, Dict, Any
from datetime import datetime

import redis
from .models import ConversionJob, JobTrack, JobStatus, JobTrackStatus


class JobManager:
    def __init__(self, redis_client=None):
        if redis_client is None:
            self.redis = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                db=int(os.getenv("REDIS_DB", "0")),
                decode_responses=True
            )
        else:
            self.redis = redis_client
    
    def generate_job_id(self) -> str:
        return f"job_{secrets.token_urlsafe(16)}"
    
    def generate_track_id(self) -> str:
        return f"t_{secrets.token_urlsafe(12)}"
    
    def create_job(self, source_url: str, source_platform: str, target_platform: str, 
                   market: str = "US", user_id: Optional[str] = None) -> ConversionJob:
        job_id = self.generate_job_id()
        job = ConversionJob(
            id=job_id,
            user_id=user_id,
            source_url=source_url,
            source_platform=source_platform,
            target_platform=target_platform,
            market=market,
            status=JobStatus.QUEUED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        job.playlist_marker = f"converted-by-auxshare:job_{job_id}"
        self._save_job(job)
        return job
    
    def _save_job(self, job: ConversionJob):
        key = f"job:{job.id}"
        # Serialize job
        job_dict = {
            "id": job.id,
            "user_id": job.user_id,
            "source_url": job.source_url,
            "source_platform": job.source_platform,
            "target_platform": job.target_platform,
            "market": job.market,
            "status": job.status.value,
            "playlist_id": job.playlist_id,
            "playlist_url": job.playlist_url,
            "playlist_marker": job.playlist_marker,
            "counts": job.counts,
            "error_message": job.error_message,
            "retry_count": job.retry_count,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "tracks": [
                {
                    "id": t.id,
                    "job_id": t.job_id,
                    "source_track": t.source_track,
                    "status": t.status.value,
                    "candidates": t.candidates,
                    "selected_target_id": t.selected_target_id,
                    "selected_at": t.selected_at.isoformat() if t.selected_at else None,
                    "added_at": t.added_at.isoformat() if t.added_at else None,
                    "failure_reason": t.failure_reason,
                    "match_tier": t.match_tier,
                    "confidence": t.confidence,
                    "position": t.position
                }
                for t in job.tracks
            ]
        }
        self.redis.setex(key, 86400 * 7, json.dumps(job_dict))  # Keep for 7 days
    
    def get_job(self, job_id: str) -> Optional[ConversionJob]:
        key = f"job:{job_id}"
        data = self.redis.get(key)
        if not data:
            return None
        job_dict = json.loads(data)
        job = ConversionJob(
            id=job_dict["id"],
            user_id=job_dict.get("user_id"),
            source_url=job_dict.get("source_url", ""),
            source_platform=job_dict.get("source_platform", ""),
            target_platform=job_dict.get("target_platform", ""),
            market=job_dict.get("market", "US"),
            status=JobStatus(job_dict["status"]),
            playlist_id=job_dict.get("playlist_id"),
            playlist_url=job_dict.get("playlist_url"),
            playlist_marker=job_dict.get("playlist_marker"),
            counts=job_dict.get("counts", {}),
            error_message=job_dict.get("error_message"),
            retry_count=job_dict.get("retry_count", 0),
            created_at=datetime.fromisoformat(job_dict["created_at"]),
            updated_at=datetime.fromisoformat(job_dict["updated_at"]),
        )
        for t_dict in job_dict.get("tracks", []):
            track = JobTrack(
                id=t_dict["id"],
                job_id=t_dict["job_id"],
                source_track=t_dict["source_track"],
                status=JobTrackStatus(t_dict["status"]),
                candidates=t_dict.get("candidates", []),
                selected_target_id=t_dict.get("selected_target_id"),
                selected_at=datetime.fromisoformat(t_dict["selected_at"]) if t_dict.get("selected_at") else None,
                added_at=datetime.fromisoformat(t_dict["added_at"]) if t_dict.get("added_at") else None,
                failure_reason=t_dict.get("failure_reason"),
                match_tier=t_dict.get("match_tier"),
                confidence=t_dict.get("confidence", 0.0),
                position=t_dict.get("position", 0)
            )
            job.tracks.append(track)
        return job
    
    def update_job_status(self, job_id: str, status: JobStatus, error_message: Optional[str] = None):
        job = self.get_job(job_id)
        if not job:
            return
        job.update_status(status)
        if error_message:
            job.error_message = error_message
        self._save_job(job)
    
    def add_tracks_to_job(self, job_id: str, tracks: List[Dict[str, Any]]):
        job = self.get_job(job_id)
        if not job:
            return
        for i, track in enumerate(tracks):
            job_track = JobTrack(
                id=self.generate_track_id(),
                job_id=job_id,
                source_track=track,
                status=JobTrackStatus.MATCHED if track.get(f'{job.target_platform}_id') else JobTrackStatus.UNMATCHED,
                confidence=track.get(f'{job.target_platform}_confidence', 0.0),
                position=i
            )
            job.tracks.append(job_track)
        job.counts = job.get_counts()
        self._save_job(job)
    
    def mark_track_added(self, job_id: str, track_id: str):
        job = self.get_job(job_id)
        if not job:
            return
        for t in job.tracks:
            if t.id == track_id:
                t.status = JobTrackStatus.ADDED
                t.added_at = datetime.utcnow()
                break
        job.counts = job.get_counts()
        self._save_job(job)
    
    def mark_track_failed(self, job_id: str, track_id: str, reason: str):
        job = self.get_job(job_id)
        if not job:
            return
        for t in job.tracks:
            if t.id == track_id:
                t.status = JobTrackStatus.FAILED
                t.failure_reason = reason
                break
        job.counts = job.get_counts()
        self._save_job(job)
    
    def get_pending_tracks(self, job_id: str) -> List[JobTrack]:
        job = self.get_job(job_id)
        if not job:
            return []
        return [t for t in job.tracks if t.status in [JobTrackStatus.MATCHED, JobTrackStatus.USER_SELECTED]]
    
    def find_playlist_by_marker(self, user_id: Optional[str], marker: str) -> Optional[str]:
        # Search through user's playlists? This is hard without knowing playlists
        # For now, return None - would need platform API to search
        return None
