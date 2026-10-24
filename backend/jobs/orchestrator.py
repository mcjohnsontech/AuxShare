# backend/jobs/orchestrator.py
import time
from typing import Optional, Dict, Any
from datetime import datetime

from .manager import JobManager
from .models import JobStatus, JobTrackStatus


class JobOrchestrator:
    def __init__(self, job_manager: JobManager, converter=None, detector=None, session_manager=None):
        self.job_manager = job_manager
        self.converter = converter
        self.detector = detector
        self.session_manager = session_manager
    
    def resume_if_needed(self, job_id: str) -> Dict[str, Any]:
        job = self.job_manager.get_job(job_id)
        if not job:
            return {"error": "Job not found"}
        
        # If awaiting reauth, keep in awaiting_reauth state
        if job.status == JobStatus.AWAITING_REAUTH:
            return {
                "job_id": job.id,
                "status": job.status.value,
                "playlist_id": job.playlist_id,
                "counts": job.get_counts(),
                "can_resume": False,
                "requires_auth": True,
                "message": "Job awaiting re-authentication. Please reconnect and resume."
            }
        
        # If failed retryable, can resume
        if job.status == JobStatus.FAILED_RETRYABLE:
            self.job_manager.update_job_status(job_id, JobStatus.ADDING_TRACKS)
            return {
                "job_id": job.id,
                "status": JobStatus.ADDING_TRACKS.value,
                "playlist_id": job.playlist_id,
                "counts": job.get_counts(),
                "can_resume": True,
                "resumed": True
            }
        
        return {
            "job_id": job.id,
            "status": job.status.value,
            "playlist_id": job.playlist_id,
            "counts": job.get_counts(),
            "can_resume": job.status in [JobStatus.PLAYLIST_CREATED, JobStatus.ADDING_TRACKS]
        }
    
    def handle_auth_expiry(self, job_id: str):
        self.job_manager.update_job_status(job_id, JobStatus.AWAITING_REAUTH)
        return {"status": "awaiting_reauth", "job_id": job_id}
    
    def ensure_terminal_state(self, job_id: str, access_token: str = None) -> Dict[str, Any]:
        job = self.job_manager.get_job(job_id)
        if not job:
            return {"error": "Job not found"}
        
        counts = job.get_counts()
        job.counts = counts
        
        # Enforce reconciliation if playlist exists
        if job.playlist_id and job.target_platform == 'spotify' and access_token:
            try:
                import requests
                headers = {'Authorization': f'Bearer {access_token}'}
                resp = requests.get(f'https://api.spotify.com/v1/playlists/{job.playlist_id}/tracks?fields=total&limit=1', headers=headers)
                if resp.status_code == 200:
                    total_in_playlist = resp.json().get('total', counts.get('added', 0))
                    counts['verified_in_playlist'] = total_in_playlist
                    job.counts = counts
            except Exception:
                pass
        
        if job.status not in [JobStatus.COMPLETE, JobStatus.FAILED_PERMANENT]:
            pending = sum(1 for t in job.tracks if t.status in [JobTrackStatus.MATCHED, JobTrackStatus.NEEDS_REVIEW])
            if pending == 0:
                job.status = JobStatus.COMPLETE
                job.updated_at = datetime.utcnow()
                self.job_manager._save_job(job)
        else:
            self.job_manager._save_job(job)
        return {
            "job_id": job.id,
            "status": job.status.value,
            "counts": counts
        }
