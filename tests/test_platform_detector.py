# tests/test_platform_detector.py
import pytest
from platform_detector import PlatformDetector
from universal_converter import UniversalConverter

def test_detect_spotify_url():
    detector = PlatformDetector()
    res = detector.detect_platform("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M")
    assert res is not None
    assert res["name"] == "spotify"
    assert res["can_extract"] is True

def test_detect_youtube_music_url():
    detector = PlatformDetector()
    res = detector.detect_platform("https://music.youtube.com/playlist?list=RDCLAK5uy_kmPRjHDECIcuVwnKsx")
    assert res is not None
    assert res["name"] == "youtube_music"
    assert res["can_extract"] is True

def test_detect_apple_music_url():
    detector = PlatformDetector()
    res = detector.detect_platform("https://music.apple.com/us/playlist/todays-hits/pl.f4d106fed2bd41149aaacabb233eb5eb")
    assert res is not None
    assert res["name"] == "apple_music"
    assert res["can_extract"] is False  # Blocked without MusicKit

def test_detect_manual_url():
    detector = PlatformDetector()
    res = detector.detect_platform("manual://Song%20-%20Artist")
    assert res is not None
    assert res["name"] == "manual"
    assert res["can_extract"] is True

def test_apple_music_source_extraction_fails_gracefully():
    converter = UniversalConverter()
    with pytest.raises(ValueError) as excinfo:
        converter.convert("https://music.apple.com/us/playlist/todays-hits/pl.f4d106fed2bd41149aaacabb233eb5eb", "spotify")
    assert "not supported yet" in str(excinfo.value)
    assert "Apple Music" in str(excinfo.value)

