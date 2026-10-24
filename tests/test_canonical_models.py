# tests/test_canonical_models.py
from models.canonical import CanonicalTrack, TargetTrack

def test_canonical_track_defaults():
    t = CanonicalTrack(
        sourcePlatform="spotify",
        sourceId="123",
        title="Song (Remix)",
        artists=["Artist A", "Artist B"]
    )
    assert t.baseTitle == "Song (Remix)"
    assert t.primaryArtists == ["Artist A"]
    assert t.featuredArtists == ["Artist B"]

def test_target_track():
    tt = TargetTrack(
        targetPlatform="youtube_music",
        targetId="yt_123",
        title="Song",
        artists=["Artist A"],
        confidence=0.95
    )
    assert tt.targetPlatform == "youtube_music"
    assert tt.confidence == 0.95

