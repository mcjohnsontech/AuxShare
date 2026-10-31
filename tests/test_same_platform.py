from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

import main
from universal_converter import UniversalConverter


SOURCES = [
    ("spotify", "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5"),
    ("youtube_music", "https://music.youtube.com/playlist?list=PLexample"),
]


@pytest.mark.parametrize("platform,url", SOURCES)
def test_same_platform_conversion_does_not_fetch_tracks(platform, url):
    source = Mock()
    target = Mock()
    target.name = platform
    detector = Mock()
    detector.detect_platform.return_value = {
        "name": platform, "display_name": platform, "can_extract": True, "handler": source,
    }
    detector.get_platform.return_value = target
    converter = UniversalConverter.__new__(UniversalConverter)
    converter.detector = detector

    with pytest.raises(ValueError, match="different destination"):
        converter.convert(url, platform)

    source.extract_playlist_id.assert_not_called()
    source.get_playlist_tracks.assert_not_called()
    target.match_track.assert_not_called()


@pytest.mark.parametrize("platform,url", SOURCES)
@pytest.mark.parametrize("endpoint", ["/api/convert", "/api/jobs"])
def test_same_platform_request_is_rejected_before_creating_job(platform, url, endpoint):
    field = "url" if endpoint == "/api/convert" else "source_url"
    with patch.object(main.job_manager, "create_job") as create_job, \
         patch.object(main.converter, "convert") as convert:
        response = TestClient(main.app).post(endpoint, json={field: url, "target_platform": platform})

    assert response.status_code == 400
    assert "different" in response.json()["detail"]
    create_job.assert_not_called()
    convert.assert_not_called()
