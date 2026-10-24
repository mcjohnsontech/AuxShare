# backend/jobs/review.py
from typing import List, Dict, Optional
from .manager import JobManager
from .models import JobTrackStatus


class ReviewService:
    def __init__(self, job_manager: JobManager):
        self.job_manager = job_manager
    
    def get_review_queue(self, job_id: str) -> List[Dict]:
        job = self.job_manager.get_job(job_id)
        if not job:
            return []
        review_tracks = []
        for track in job.tracks:
            if track.status == JobTrackStatus.NEEDS_REVIEW or track.status == JobTrackStatus.MATCHED and len(track.candidates) > 0:
                review_tracks.append({
                    "track_id": track.id,
                    "source": track.source_track,
                    "candidates": track.candidates[:5],
                    "status": track.status.value,
                    "confidence": track.confidence
                })
        return review_tracks
    
    def select_track(self, job_id: str, track_id: str, target_id: Optional[str], skip: bool = False):
        job = self.job_manager.get_job(job_id)
        if not job:
            return False
        for track in job.tracks:
            if track.id == track_id:
                if skip:
                    track.status = JobTrackStatus.USER_SKIPPED
                else:
                    track.status = JobTrackStatus.USER_SELECTED
                    track.selected_target_id = target_id
                    from datetime import datetime
                    track.selected_at = datetime.utcnow()
                break
        self.job_manager._save_job(job)
        return True
    
    def accept_top_picks(self, job_id: str):
        job = self.job_manager.get_job(job_id)
        if not job:
            return False
        for track in job.tracks:
            if track.status == JobTrackStatus.MATCHED and track.candidates:
                track.status = JobTrackStatus.USER_SELECTED
                track.selected_target_id = track.candidates[0].get('target_id') or track.candidates[0].get('id')
                from datetime import datetime
                track.selected_at = datetime.utcnow()
        self.job_manager._save_job(job)
        return True
