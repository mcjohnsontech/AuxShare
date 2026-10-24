import React, { useState, useEffect } from 'react';
import api from '../services/api';

const ReviewQueue = ({ jobId, onComplete }) => {
  const [tracks, setTracks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (jobId) {
      fetchReviewQueue();
    }
  }, [jobId]);

  const fetchReviewQueue = async () => {
    try {
      const response = await api.get(`/jobs/${jobId}/review`);
      setTracks(response.data.tracks || []);
    } catch (error) {
      console.error('Error fetching review queue:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectTrack = async (trackId, targetId, skip = false) => {
    try {
      await api.post(`/jobs/${jobId}/tracks/${trackId}/select`, {
        target_id: targetId,
        skip: skip
      });
      if (currentIndex < tracks.length - 1) {
        setCurrentIndex(currentIndex + 1);
      } else {
        if (onComplete) onComplete();
      }
    } catch (error) {
      console.error('Error selecting track:', error);
    }
  };

  const acceptAllTop = async () => {
    try {
      await api.post(`/jobs/${jobId}/accept-top`);
      if (onComplete) onComplete();
    } catch (error) {
      console.error('Error accepting top picks:', error);
    }
  };

  if (loading) return <div>Loading review queue...</div>;
  if (tracks.length === 0) return <div>No tracks need review!</div>;

  const track = tracks[currentIndex];
  const candidates = track.candidates || [];

  return (
    <div className="review-queue">
      <h2>Review Tracks ({currentIndex + 1} of {tracks.length})</h2>
      <button onClick={acceptAllTop}>Accept All Top Picks</button>
      
      <div className="source-track">
        <h3>Source:</h3>
        <p>{track.source?.title} - {track.source?.artist || track.source?.artists}</p>
      </div>
      
      <div className="candidates">
        <h3>Options:</h3>
        {candidates.map((candidate, idx) => (
          <div key={idx} className="candidate">
            <input 
              type="radio" 
              name="candidate" 
              id={`c${idx}`}
              onChange={() => selectTrack(track.track_id, candidate.target_id || candidate.id)}
            />
            <label htmlFor={`c${idx}`}>
              {candidate.title} - {candidate.artists?.join(', ') || candidate.artist}
              {candidate.score && <span> ({Math.round(candidate.score * 100)}%)</span>}
              {candidate.flags?.includes('remix') && <span> ⚠ remix</span>}
              {candidate.flags?.includes('live') && <span> ⚠ live</span>}
            </label>
          </div>
        ))}
        <button onClick={() => selectTrack(track.track_id, null, true)}>Skip</button>
      </div>
    </div>
  );
};

export default ReviewQueue;
