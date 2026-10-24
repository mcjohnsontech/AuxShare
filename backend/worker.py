#!/usr/bin/env python
# backend/worker.py
import os
import sys
import time
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jobs.queue import JobQueue
from jobs.manager import JobManager
from jobs.models import JobStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Worker:
    def __init__(self):
        self.job_manager = JobManager()
        self.queue = JobQueue()
        self.running = True
    
    def process_job(self, job_data):
        job_id = job_data.get('job_id')
        if not job_id:
            return
        job = self.job_manager.get_job(job_id)
        if not job:
            logger.warning(f"Job {job_id} not found")
            return
        logger.info(f"Processing job {job_id} - status: {job.status.value}")
        try:
            if job.status == JobStatus.QUEUED:
                self.job_manager.update_job_status(job_id, JobStatus.MATCHING)
            elif job.status == JobStatus.MATCHING:
                self.job_manager.update_job_status(job_id, JobStatus.PLAYLIST_CREATED)
            elif job.status == JobStatus.PLAYLIST_CREATED:
                self.job_manager.update_job_status(job_id, JobStatus.ADDING_TRACKS)
            elif job.status == JobStatus.ADDING_TRACKS:
                self.job_manager.update_job_status(job_id, JobStatus.VERIFYING)
            elif job.status == JobStatus.VERIFYING:
                self.job_manager.update_job_status(job_id, JobStatus.COMPLETE)
            else:
                logger.info(f"Job {job_id} in terminal state: {job.status.value}")
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}")
            self.job_manager.update_job_status(job_id, JobStatus.FAILED_RETRYABLE)
    
    def run(self):
        logger.info("Worker started, waiting for jobs...")
        while self.running:
            try:
                job_data = self.queue.dequeue(timeout=5)
                if job_data:
                    self.process_job(job_data)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                time.sleep(1)


if __name__ == "__main__":
    worker = Worker()
    worker.run()
