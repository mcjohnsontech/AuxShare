# tests/test_characterization.py
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import main
from main import app

client = TestClient(app)

def test_health_check_characterization():
    with patch.object(main.session_manager.redis_client, "ping", return_value=True):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["redis"] is True

def test_platforms_endpoints_characterization():
    resp = client.get("/api/platforms")
    assert resp.status_code == 200
    platforms = resp.json()
    platform_names = [p["name"] for p in platforms]
    assert "spotify" in platform_names
    assert "youtube_music" in platform_names
    assert "apple_music" in platform_names
    assert "manual" in platform_names

    resp_sources = client.get("/api/platforms/sources")
    assert resp_sources.status_code == 200
    source_names = [s["name"] for s in resp_sources.json()]
    assert "apple_music" not in source_names  # Apple Music cannot be source

    resp_targets = client.get("/api/platforms/targets")
    assert resp_targets.status_code == 200
    target_names = [t["name"] for t in resp_targets.json()]
    assert "spotify" in target_names
    assert "youtube_music" in target_names

def test_convert_valid_url_characterization():
    fake_tracks = [
        {"title": "Song A", "artist": "Artist A", "id": "sp_1", "youtube_music_id": "yt_1", "youtube_music_confidence": 0.95}
    ]
    fake_result = {
        "source_platform": "Spotify",
        "target_platform": "youtube_music",
        "tracks": fake_tracks,
        "stats": {
            "total": 1,
            "matched": 1,
            "failed": 0,
            "match_rate": 1.0,
            "avg_confidence": 0.95,
            "high_confidence": 1,
            "medium_confidence": 0,
            "low_confidence": 0
        }
    }
    with patch.object(main.converter, "convert", return_value=fake_result), \
         patch.object(main.session_manager, "save_session", return_value="1234"):
        resp = client.post("/api/convert", json={
            "url": "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
            "target_platform": "youtube_music"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "1234"
        assert data["source_platform"] == "Spotify"
        assert data["target_platform"] == "youtube_music"
        assert data["stats"]["matched"] == 1

def test_convert_apple_music_source_rejected_characterization():
    resp = client.post("/api/convert", json={
        "url": "https://music.apple.com/us/playlist/todays-hits/pl.f4d106fed2bd41149aaacabb233eb5eb",
        "target_platform": "spotify"
    })
    assert resp.status_code == 400
    assert "not supported yet" in resp.json()["detail"]

def test_get_session_characterization():
    fake_session = {
        "tracks": [{"title": "Song A", "artist": "Artist A", "id": "123"}],
        "target_platform": "spotify",
        "source_platform": "YouTube Music"
    }
    with patch.object(main.session_manager, "get_session", return_value=fake_session), \
         patch.object(main.session_manager.redis_client, "incr", return_value=1), \
         patch.object(main.session_manager.redis_client, "expire", return_value=True), \
         patch.object(main.converter, "_calculate_stats", return_value={
             "total": 1, "matched": 1, "failed": 0, "match_rate": 1.0,
             "avg_confidence": 1.0, "high_confidence": 1, "medium_confidence": 0, "low_confidence": 0
         }):
        resp = client.get("/api/session/1234")
        assert resp.status_code == 200
        data = resp.json()
        assert data["target_platform"] == "spotify"
        assert len(data["tracks"]) == 1

def test_get_session_not_found_characterization():
    with patch.object(main.session_manager, "get_session", return_value=None):
        resp = client.get("/api/session/9999")
        assert resp.status_code == 404

def test_export_characterization():
    fake_session = {
        "tracks": [{"title": "Song A", "artist": "Artist A", "id": "sp_123"}],
        "target_platform": "spotify"
    }
    fake_platform = MagicMock()
    fake_platform.create_playlist.return_value = "new_playlist_id_999"
    fake_platform.add_tracks_to_playlist.return_value = None

    with patch.object(main.session_manager, "get_session", return_value=fake_session), \
         patch.object(main.detector, "get_platform", return_value=fake_platform):
        resp = client.post("/api/export", json={
            "session_code": "1234",
            "target_platform": "spotify",
            "access_token": "fake_token_abc",
            "playlist_name": "My Converted Playlist"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "new_playlist_id_999" in data["playlist_url"]
        assert data["tracks_added"] == 1

def test_export_non_spotify_rejected_characterization():
    fake_session = {
        "tracks": [{"title": "Song A", "artist": "Artist A", "id": "sp_123"}],
        "target_platform": "youtube_music"
    }
    with patch.object(main.session_manager, "get_session", return_value=fake_session):
        resp = client.post("/api/export", json={
            "session_code": "1234",
            "target_platform": "youtube_music",
            "access_token": "fake_token"
        })
        assert resp.status_code == 400
        assert "Only Spotify export is supported" in resp.json()["detail"]
