# tests/test_export_idempotency.py
"""Export must never create a second playlist for the same session.

These tests cover both the record/lock primitive and the /api/export endpoint:
re-clicking Export reuses the existing playlist, re-running a partially added
playlist does not append duplicate tracks, and concurrent requests cannot both
create a playlist.
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import main
from main import app, SESSION_COOKIE_NAME
from export_idempotency import ExportIdempotency


class FakeRedis:
    """Minimal in-memory Redis supporting the operations export uses."""

    def __init__(self):
        self.store: dict = {}
        self.ttls: dict = {}

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, ttl, value):
        self.store[key] = value
        self.ttls[key] = ttl
        return True

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.store:
            return None
        self.store[key] = value
        if ex:
            self.ttls[key] = ex
        return True

    def delete(self, key):
        existed = key in self.store
        self.store.pop(key, None)
        self.ttls.pop(key, None)
        return 1 if existed else 0


client = TestClient(app)

TRACK = {"title": "Song A", "artist": "Artist A", "id": "sp_123"}
SESSION = {"tracks": [TRACK], "target_platform": "spotify"}


def _platform(playlist_id="pl_1"):
    platform = MagicMock()
    platform.get_current_user_id.return_value = "user_abc"
    platform.get_playlist_track_uris.return_value = []
    platform.get_playlist_track_count.return_value = 1
    platform.create_playlist.return_value = playlist_id
    platform.add_tracks_to_playlist.return_value = None
    platform.find_playlist_by_marker.return_value = None
    return platform


def _post(platform, redis, **overrides):
    payload = {
        "session_code": "sess_code_1",
        "target_platform": "spotify",
        "access_token": "token",
        "playlist_name": "My Playlist",
    }
    payload.update(overrides)
    readback = MagicMock(status_code=500)
    with patch.object(main.session_manager, "get_session", return_value=SESSION), \
         patch.object(main.detector, "get_platform", return_value=platform), \
         patch.object(main.session_manager, "redis_client", redis), \
         patch("requests.get", return_value=readback), \
         patch("export_idempotency.ExportIdempotency",
               lambda *a, **kw: ExportIdempotency(redis)):
        return client.post("/api/export", json=payload)


# ---------------------------------------------------------------------------
# Record + lock primitive
# ---------------------------------------------------------------------------

def test_record_roundtrip_and_ttl():
    redis = FakeRedis()
    idem = ExportIdempotency(redis)

    assert idem.get_record("u", "spotify", "s") is None
    idem.save_record("u", "spotify", "s", "pl_1", completed=True, tracks_added=5)

    record = idem.get_record("u", "spotify", "s")
    assert record["playlist_id"] == "pl_1"
    assert record["completed"] is True
    assert record["tracks_added"] == 5
    assert redis.ttls[idem.record_key("u", "spotify", "s")] == idem.record_ttl


def test_record_is_scoped_per_account_and_platform():
    redis = FakeRedis()
    idem = ExportIdempotency(redis)
    idem.save_record("user_a", "spotify", "s", "pl_a", completed=True)

    assert idem.get_record("user_a", "spotify", "s")["playlist_id"] == "pl_a"
    assert idem.get_record("user_b", "spotify", "s") is None
    assert idem.get_record("user_a", "apple_music", "s") is None


def test_lock_is_exclusive():
    redis = FakeRedis()
    idem = ExportIdempotency(redis)

    assert idem.acquire_lock("u", "spotify", "s") is True
    assert idem.acquire_lock("u", "spotify", "s") is False

    idem.release_lock("u", "spotify", "s")
    assert idem.acquire_lock("u", "spotify", "s") is True


# ---------------------------------------------------------------------------
# /api/export idempotency
# ---------------------------------------------------------------------------

def test_second_export_reuses_playlist():
    redis = FakeRedis()
    platform = _platform()

    first = _post(platform, redis)
    assert first.status_code == 200
    first_data = first.json()
    assert first_data["created_new"] is True
    assert first_data["tracks_added"] == 1

    second = _post(platform, redis)
    assert second.status_code == 200
    second_data = second.json()

    assert second_data["created_new"] is False
    assert second_data["already_existed"] is True
    assert second_data["playlist_id"] == first_data["playlist_id"]
    assert second_data["playlist_url"] == first_data["playlist_url"]
    # No new playlist and no duplicate tracks.
    assert platform.create_playlist.call_count == 1
    assert platform.add_tracks_to_playlist.call_count == 1


def test_partial_playlist_only_adds_missing_tracks():
    """A playlist created before a crash must be completed, not duplicated."""
    redis = FakeRedis()
    platform = _platform()
    # Simulate a playlist left behind by an interrupted run: the marker lookup
    # finds it, the record is not marked complete, and one track is present.
    platform.find_playlist_by_marker.return_value = "pl_partial"
    platform.get_playlist_track_uris.return_value = ["spotify:track:sp_123"]

    resp = _post(platform, redis)

    assert resp.status_code == 200
    data = resp.json()
    assert data["created_new"] is False
    assert data["playlist_id"] == "pl_partial"
    assert data["tracks_added"] == 0
    platform.create_playlist.assert_not_called()
    platform.add_tracks_to_playlist.assert_not_called()


def test_duplicate_uris_in_session_added_once():
    redis = FakeRedis()
    platform = _platform()
    session = {"tracks": [TRACK, dict(TRACK)], "target_platform": "spotify"}

    with patch.object(main.session_manager, "get_session", return_value=session), \
         patch.object(main.detector, "get_platform", return_value=platform), \
         patch.object(main.session_manager, "redis_client", redis), \
         patch("requests.get", return_value=MagicMock(status_code=500)), \
         patch("export_idempotency.ExportIdempotency",
               lambda *a, **kw: ExportIdempotency(redis)):
        resp = client.post("/api/export", json={
            "session_code": "sess_code_1",
            "target_platform": "spotify",
            "access_token": "token",
        })

    assert resp.status_code == 200
    uris = platform.add_tracks_to_playlist.call_args[0][2]
    assert uris == ["spotify:track:sp_123"]


def test_concurrent_export_returns_conflict():
    """While another request holds the lock, a second one must not create."""
    redis = FakeRedis()
    platform = _platform()
    idem = ExportIdempotency(redis)
    idem.acquire_lock("user_abc", "spotify", "sess_code_1")

    resp = _post(platform, redis)

    assert resp.status_code == 409
    platform.create_playlist.assert_not_called()


def test_deleted_playlist_is_recreated():
    """A playlist removed on Spotify must not be reported as a success."""
    redis = FakeRedis()
    platform = _platform()

    _post(platform, redis)
    platform.get_playlist_track_count.return_value = None  # gone
    platform.create_playlist.return_value = "pl_2"

    resp = _post(platform, redis)
    assert resp.status_code == 200
    data = resp.json()
    assert data["created_new"] is True
    assert data["playlist_id"] == "pl_2"
    assert platform.create_playlist.call_count == 2


def test_verification_error_does_not_duplicate():
    """If we cannot check the playlist, trust the record rather than duplicate."""
    redis = FakeRedis()
    platform = _platform()

    _post(platform, redis)
    platform.get_playlist_track_count.side_effect = Exception("network blip")

    resp = _post(platform, redis)
    assert resp.status_code == 200
    data = resp.json()
    assert data["created_new"] is False
    assert data["playlist_id"] == "pl_1"
    assert platform.create_playlist.call_count == 1


def test_resume_read_failure_does_not_duplicate():
    """If existing playlist contents cannot be read, add nothing."""
    redis = FakeRedis()
    platform = _platform()
    platform.find_playlist_by_marker.return_value = "pl_partial"
    platform.get_playlist_track_uris.side_effect = Exception("spotify 503")

    resp = _post(platform, redis)

    assert resp.status_code == 502
    assert "avoid duplicates" in resp.json()["detail"]
    platform.add_tracks_to_playlist.assert_not_called()


def test_force_new_creates_another_playlist():
    redis = FakeRedis()
    platform = _platform()

    _post(platform, redis)
    platform.create_playlist.return_value = "pl_2"
    resp = _post(platform, redis, force_new=True)

    assert resp.status_code == 200
    data = resp.json()
    assert data["created_new"] is True
    assert data["playlist_id"] == "pl_2"
    assert platform.create_playlist.call_count == 2
    # The stored record now points at the newest playlist.
    assert ExportIdempotency(redis).get_record(
        "user_abc", "spotify", "sess_code_1"
    )["playlist_id"] == "pl_2"


# ---------------------------------------------------------------------------
# /api/export/status (drives the disabled button)
# ---------------------------------------------------------------------------

def _status(platform, redis, *, logged_in=True, **params):
    query = {"session_code": "sess_code_1", "target_platform": "spotify"}
    query.update(params)
    tokens = {"access_token": "token", "refresh_token": None, "is_expired": False}
    with patch.object(main.detector, "get_platform", return_value=platform), \
         patch.object(main.session_manager, "redis_client", redis), \
         patch.object(main.secure_session, "get_user_tokens",
                      return_value=tokens if logged_in else None), \
         patch("export_idempotency.ExportIdempotency",
               lambda *a, **kw: ExportIdempotency(redis)):
        cookies = {SESSION_COOKIE_NAME: "sess_abc"} if logged_in else {}
        return client.get("/api/export/status", params=query, cookies=cookies)


def test_status_signed_out_is_not_exported():
    redis = FakeRedis()
    platform = _platform()

    resp = _status(platform, redis, logged_in=False)

    assert resp.status_code == 200
    data = resp.json()
    assert data["authenticated"] is False
    assert data["exported"] is False


def test_status_reports_completed_export():
    """After a successful export the button must be disabled by the UI."""
    redis = FakeRedis()
    platform = _platform()
    _post(platform, redis)

    resp = _status(platform, redis)

    assert resp.status_code == 200
    data = resp.json()
    assert data["authenticated"] is True
    assert data["exported"] is True
    assert data["playlist_id"] == "pl_1"
    assert data["playlist_url"] == "https://open.spotify.com/playlist/pl_1"
    assert data["tracks_in_playlist"] == 1


def test_status_incomplete_record_is_not_exported():
    redis = FakeRedis()
    platform = _platform()
    idem = ExportIdempotency(redis)
    idem.save_record("user_abc", "spotify", "sess_code_1", "pl_1", completed=False)

    resp = _status(platform, redis)

    assert resp.json()["exported"] is False


def test_status_deleted_playlist_re_enables_export():
    redis = FakeRedis()
    platform = _platform()
    _post(platform, redis)
    platform.get_playlist_track_count.return_value = None

    resp = _status(platform, redis)

    assert resp.json()["exported"] is False
    assert ExportIdempotency(redis).get_record("user_abc", "spotify", "sess_code_1") is None


def test_status_rejects_unsupported_platform():
    redis = FakeRedis()
    platform = _platform()

    resp = _status(platform, redis, target_platform="apple_music")

    assert resp.status_code == 400
