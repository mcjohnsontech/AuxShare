# tests/test_matching.py
from typing import Dict, List, Optional

from matching import (
    best_candidate,
    canonical_from_track,
    has_blocking_variant,
    normalize_text,
    parse_title,
    rank_candidates,
)
from models.canonical import CanonicalTrack
from platforms.base import MusicPlatform


class FakePlatform(MusicPlatform):
    def __init__(self, candidates=None, isrc_result=None, legacy_result=None):
        super().__init__("fake")
        self.candidates = candidates or []
        self.isrc_result = isrc_result
        self.legacy_result = legacy_result
        self.candidate_queries = []

    def extract_playlist_id(self, url):
        return None

    def get_playlist_tracks(self, playlist_id):
        return []

    def search_by_isrc(self, isrc):
        return self.isrc_result

    def search_by_metadata(self, title, artist):
        return self.legacy_result

    def search_candidates(self, title, artist, limit=10):
        self.candidate_queries.append((title, artist))
        return self.candidates

    def generate_playback_link(self, track_ids):
        return ""


def candidate(**overrides) -> Dict:
    item = {
        "id": "candidate-1",
        "title": "Levitating",
        "artists": ["Dua Lipa"],
        "album": "Future Nostalgia",
        "duration_ms": 203000,
    }
    item.update(overrides)
    return item


def test_normalize_text_is_script_preserving():
    assert normalize_text("  DON'T Start Now!  ") == "dont start now"
    assert normalize_text("MAREK STYCZYŃSKI") == "marek styczynski"
    assert normalize_text("Группа крови") == "группа крови"
    assert normalize_text("夜に駆ける") == "夜に駆ける"
    assert normalize_text("R&B") == "r and b"


def test_parse_title_removes_youtube_noise_and_artist_prefix():
    parsed = parse_title(
        "Coldplay - Yellow (Official Audio)", artists=["Coldplay"]
    )
    assert parsed.base_title == "Yellow"
    assert parsed.variant_tags == []
    assert "official audio" in parsed.noise_tags


def test_parse_title_extracts_featured_artists_and_neutral_tags():
    featured = parse_title("Levitating (feat. DaBaby)", artists=["Dua Lipa"])
    assert featured.base_title == "Levitating"
    assert featured.featured_artists == ["DaBaby"]

    remaster = parse_title("Hey Jude - 2015 Remaster", artists=["The Beatles"])
    assert remaster.base_title == "Hey Jude"
    assert remaster.version_tags == ["remaster"]
    assert remaster.variant_tags == []


def test_parse_title_detects_variants():
    expectations = {
        "Hotel California - Live On MTV, 1994": "live",
        "Levitating (The Blessed Madonna Remix)": "remix",
        "Creep - Acoustic": "acoustic",
        "Smells Like Teen Spirit - Sped Up": "sped_up",
        "Bohemian Rhapsody - Karaoke Version": "karaoke",
    }
    for title, expected in expectations.items():
        assert parse_title(title).variant_tags == [expected]


def test_canonical_from_dict_canonical_and_manual_models():
    from_dict = canonical_from_track(
        {
            "title": "STAY (with Justin Bieber)",
            "artist": "The Kid LAROI",
            "duration_ms": 141000,
            "isrc": "USSM12104193",
        }
    )
    assert from_dict.baseTitle == "STAY"
    assert from_dict.primaryArtists == ["The Kid LAROI"]
    assert from_dict.featuredArtists == ["Justin Bieber"]
    assert from_dict.durationMs == 141000
    assert from_dict.isrc == "USSM12104193"
    assert has_blocking_variant(from_dict) is False

    manual_payload = CanonicalTrack(
        sourcePlatform="manual",
        sourceId="manual_1",
        title="Creep - Acoustic",
        baseTitle="Creep - Acoustic",
        artists=["Radiohead"],
        primaryArtists=["Radiohead"],
    ).model_dump()
    from_manual = canonical_from_track(manual_payload)
    assert from_manual.baseTitle == "Creep"
    assert has_blocking_variant(from_manual) is True


def test_rank_candidates_prefers_exact_title_and_rejects_variants():
    source = canonical_from_track(
        {"title": "Levitating (feat. DaBaby)", "artist": "Dua Lipa"}
    )
    ranked = rank_candidates(
        source,
        [
            candidate(id="wrong", title="Levitating (Live)", artists=["Dua Lipa"]),
            candidate(id="right", title="Levitating (feat. DaBaby)"),
        ],
    )
    assert ranked[0].candidate["id"] == "right"
    assert ranked[0].accepted is True
    assert ranked[1].accepted is False
    assert "variant_conflict" in ranked[1].flags
    assert best_candidate(source, [ranked[1].candidate]) is None


def test_non_latin_token_subset_can_match():
    source = canonical_from_track({"title": "怪物", "artist": "YOASOBI"})
    scored = best_candidate(
        source,
        [candidate(id="kaibutsu", title="Monster (怪物)", artists=["YOASOBI"])],
    )
    assert scored is not None
    assert scored.candidate["id"] == "kaibutsu"


def test_match_track_rejects_variant_source_without_searching():
    platform = FakePlatform(candidates=[candidate()])
    result = platform.match_track(
        {"title": "Creep - Acoustic", "artist": "Radiohead"}
    )
    assert result is None
    assert platform.candidate_queries == []


def test_match_track_uses_ranked_metadata_candidate():
    platform = FakePlatform(
        candidates=[
            candidate(id="live", title="Hotel California (Live On MTV, 1994)"),
            candidate(id="studio", title="Hotel California", artists=["Eagles"]),
        ]
    )
    result = platform.match_track(
        {"title": "Hotel California", "artist": "Eagles"}
    )
    assert result is not None
    assert result["id"] == "studio"
    assert result["match_method"] == "metadata"
    assert result["confidence"] == 1.0
    assert platform.candidate_queries == [("Hotel California", "Eagles")]


def test_match_track_validates_isrc_before_accepting_it():
    platform = FakePlatform(
        isrc_result={
            "id": "bad-isrc",
            "title": "T.V. Scene",
            "artist": "Linda Di Franco",
        },
        candidates=[candidate(id="right", title="Levitating (feat. DaBaby)")],
    )
    result = platform.match_track(
        {
            "title": "Levitating (feat. DaBaby)",
            "artist": "Dua Lipa",
            "isrc": "GBAHT2000570",
        }
    )
    assert result is not None
    assert result["id"] == "right"
    assert result["match_method"] == "metadata"


def test_match_track_uses_consistent_isrc_fast_path():
    platform = FakePlatform(
        isrc_result={
            "id": "spotify-1",
            "title": "Flowers",
            "artist": "Miley Cyrus",
        },
        candidates=[candidate(id="should-not-be-used")],
    )
    result = platform.match_track(
        {"title": "Flowers", "artist": "Miley Cyrus", "isrc": "USSM12209777"}
    )
    assert result is not None
    assert result["id"] == "spotify-1"
    assert result["match_method"] == "isrc"
    assert result["confidence"] == 1.0
    assert "isrc" in result["flags"]


def test_match_track_falls_back_to_legacy_metadata_search_when_no_candidates():
    platform = FakePlatform(
        legacy_result={
            "id": "legacy-1",
            "title": "Yellow",
            "artist": "Coldplay",
        }
    )
    result = platform.match_track(
        {"title": "Coldplay - Yellow (Official Audio)", "artist": "Coldplay"}
    )
    assert result is not None
    assert result["id"] == "legacy-1"
    assert result["match_method"] == "metadata"
