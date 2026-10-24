# backend/matching/normalization.py
"""Text normalization and canonical track construction.

The helpers in this module are deliberately platform agnostic.  They turn the
messy metadata returned by Spotify, YouTube Music, Apple Music and manual
imports into a comparable shape:

* ``normalize_text`` - aggressive, script-preserving string normalization
* ``parse_title`` - separates a display title from version/edition tags and
  featured artists
* ``split_artists`` - splits delimited artist strings into individual names
* ``strip_artist_prefix`` - removes YouTube style ``Artist - Title`` prefixes
* ``canonical_from_track`` - builds a :class:`CanonicalTrack` from any adapter
  payload (dict or model)
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence

from models.canonical import CanonicalTrack


# ---------------------------------------------------------------------------
# Version / edition vocabulary
# ---------------------------------------------------------------------------

# Tags which describe a different recording.  Matching a source studio track
# to one of these candidates is a precision failure, so they are rejected.
VARIANT_KEYWORDS: Dict[str, tuple] = {
    "live": ("live", "concert", "in concert", "on tour", "unplugged"),
    "remix": ("remix", "rmx", "bootleg", "mashup", "mash up"),
    "acoustic": ("acoustic",),
    "karaoke": ("karaoke", "backing track", "sing along", "sing-along"),
    "instrumental": ("instrumental", "inst.", "no vocals"),
    "demo": ("demo", "demo version"),
    "cover": ("cover", "tribute"),
    "sped_up": ("sped up", "speed up", "sped-up"),
    "slowed": ("slowed", "slowed down", "reverb", "nightcore"),
    "a_cappella": ("a cappella", "acapella", "a-capella"),
    "8d": ("8d audio", "8d"),
}

# Tags which are different editions of the *same* recording.  They are ignored
# for matching but retained on the canonical track for transparency.
NEUTRAL_KEYWORDS: Dict[str, tuple] = {
    "remaster": ("remaster", "remastered", "re-master", "re-mastered"),
    "mix": ("mix", "mix version"),
    "version": ("version",),
    "edit": ("edit", "radio edit"),
    "mono": ("mono",),
    "stereo": ("stereo",),
    "deluxe": ("deluxe", "deluxe edition"),
    "bonus": ("bonus", "bonus track"),
    "anniversary": ("anniversary",),
    "soundtrack": ("soundtrack", "from the soundtrack"),
}

# YouTube / promotional noise.  These never belong to the song title.
NOISE_KEYWORDS: tuple = (
    "official music video",
    "official video",
    "official audio",
    "official lyric video",
    "official lyrics video",
    "lyric video",
    "lyrics video",
    "official visualizer",
    "visualizer",
    "official hd video",
    "hd video",
    "music video",
    "with lyrics",
    "lyrics",
    "audio",
    "topic",
    "explicit",
    "clean",
    "m/v",
    "mv",
    "4k",
    "hd",
    "hq",
)

FEATURED_PREFIXES: tuple = (
    "feat.",
    "feat",
    "ft.",
    "ft",
    "featuring",
    "with",
    "prod.",
    "prod",
    "produced by",
)

_BRACKET_RE = re.compile(r"[\(\[]([^\)\]]*)[\)\]]")
_DASH_RE = re.compile(r"\s+[-\u2010\u2011\u2012\u2013\u2014\u2015]+\s+")
_FEAT_INLINE_RE = re.compile(
    r"\s+(?:feat\.?|ft\.?|featuring)\s+(.+)$", re.IGNORECASE
)
_ARTIST_SPLIT_RE = re.compile(
    r"\s*(?:,|;|/|\||&|\+|×|\s+x\s+|\s+feat\.?\s+|\s+ft\.?\s+|\s+featuring\s+|\s+with\s+|\s+and\s+)\s*",
    re.IGNORECASE,
)
_DURATION_RE = re.compile(r"^\s*(?:(\d+):)?(\d+):(\d+)\s*$")


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


def normalize_text(value: Any) -> str:
    """Return a case/punctuation-insensitive comparison key.

    Non-Latin scripts are preserved.  Latin diacritics are folded (``Cię`` ->
    ``cie``) while Hangul/Cyrillic/Arabic/CJK characters are kept intact.
    """
    if value is None:
        return ""

    text = str(value)
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("'", "")
    text = text.replace("&", " and ")
    text = _DASH_RE.sub(" - ", text)

    # NFKD decomposes accented Latin characters but also Hangul syllables.
    # Keep any non-combining character so non-Latin scripts still compare.
    decomposed = unicodedata.normalize("NFKD", text)
    chars: List[str] = []
    for char in decomposed:
        if unicodedata.combining(char):
            continue
        category = unicodedata.category(char)
        if category[0] in ("L", "N", "M"):
            chars.append(char)
        else:
            chars.append(" ")

    text = "".join(chars).casefold()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalized_tokens(value: Any) -> List[str]:
    return normalize_text(value).split()


def split_artists(value: Any) -> List[str]:
    """Split an artist field (string or sequence) into unique artist names."""
    if value is None:
        return []

    raw_items: List[str] = []
    if isinstance(value, str):
        raw_items = [value]
    elif isinstance(value, dict):
        name = value.get("name") or value.get("artist")
        if name:
            raw_items = [str(name)]
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            if isinstance(item, dict):
                name = item.get("name") or item.get("artist")
                if name:
                    raw_items.append(str(name))
            elif item is not None:
                raw_items.append(str(item))
    else:
        raw_items = [str(value)]

    artists: List[str] = []
    seen = set()
    for item in raw_items:
        for part in _ARTIST_SPLIT_RE.split(item):
            part = part.strip(" \t-")
            if not part:
                continue
            key = normalize_text(part)
            if not key or key in seen:
                continue
            seen.add(key)
            artists.append(part)
    return artists


def strip_artist_prefix(title: Any, artists: Any = None) -> str:
    """Remove a leading ``Artist - `` / ``Artist: `` prefix from *title*."""
    text = str(title or "").strip()
    if not text:
        return ""

    artist_names = split_artists(artists)
    if not artist_names:
        return text

    artist_keys = {normalize_text(name) for name in artist_names if normalize_text(name)}
    if not artist_keys:
        return text

    match = re.match(r"^(.*?)\s*[-\u2013\u2014:]\s+(.*)$", text)
    if match:
        prefix_key = normalize_text(match.group(1))
        if prefix_key in artist_keys:
            return match.group(2).strip()

    # Also handle "Artist - Title" where the prefix contains extra credits.
    for name in artist_names:
        pattern = re.compile(
            r"^" + re.escape(name) + r"\s*[-\u2013\u2014:]\s*", re.IGNORECASE
        )
        stripped = pattern.sub("", text, count=1)
        if stripped != text:
            return stripped.strip()

    return text


# ---------------------------------------------------------------------------
# Title parsing
# ---------------------------------------------------------------------------


@dataclass
class ParsedTitle:
    """Structured representation of a display title."""

    raw_title: str
    base_title: str
    version_tags: List[str] = field(default_factory=list)
    variant_tags: List[str] = field(default_factory=list)
    featured_artists: List[str] = field(default_factory=list)
    noise_tags: List[str] = field(default_factory=list)

    @property
    def is_variant(self) -> bool:
        return bool(self.variant_tags)


def _contains_any(normalized: str, keywords: Iterable[str]) -> Optional[str]:
    tokens = set(normalized.split())
    for keyword in keywords:
        key = normalize_text(keyword)
        if not key:
            continue
        if " " in key:
            if key in normalized:
                return key
        elif key in tokens:
            return key
    return None


def _classify_segment(segment: str) -> tuple:
    """Classify a parenthetical/dash segment.

    Returns ``(kind, value)`` where kind is one of ``noise``, ``featured``,
    ``variant``, ``neutral`` or ``unknown``.
    """
    text = segment.strip()
    if not text:
        return ("unknown", "")

    normalized = normalize_text(text)
    if not normalized:
        return ("noise", "")

    # Pure years / catalogue numbers are noise.
    if re.fullmatch(r"\d{2,4}", normalized):
        return ("noise", normalized)

    lowered = text.casefold().strip()
    for prefix in FEATURED_PREFIXES:
        if lowered.startswith(prefix):
            remainder = text[len(prefix):].strip(" .:-")
            if remainder:
                return ("featured", remainder)

    # Variant keywords first (remix contains "mix").
    keyword = _contains_any(normalized, VARIANT_KEYWORDS["live"])
    if keyword:
        return ("variant", "live")
    keyword = _contains_any(normalized, VARIANT_KEYWORDS["remix"])
    if keyword:
        return ("variant", "remix")
    keyword = _contains_any(normalized, VARIANT_KEYWORDS["acoustic"])
    if keyword:
        return ("variant", "acoustic")
    keyword = _contains_any(normalized, VARIANT_KEYWORDS["karaoke"])
    if keyword:
        return ("variant", "karaoke")
    keyword = _contains_any(normalized, VARIANT_KEYWORDS["instrumental"])
    if keyword:
        return ("variant", "instrumental")
    keyword = _contains_any(normalized, VARIANT_KEYWORDS["demo"])
    if keyword:
        return ("variant", "demo")
    keyword = _contains_any(normalized, VARIANT_KEYWORDS["cover"])
    if keyword:
        return ("variant", "cover")
    keyword = _contains_any(normalized, VARIANT_KEYWORDS["sped_up"])
    if keyword:
        return ("variant", "sped_up")
    keyword = _contains_any(normalized, VARIANT_KEYWORDS["slowed"])
    if keyword:
        return ("variant", "slowed")
    keyword = _contains_any(normalized, VARIANT_KEYWORDS["a_cappella"])
    if keyword:
        return ("variant", "a_cappella")
    keyword = _contains_any(normalized, VARIANT_KEYWORDS["8d"])
    if keyword:
        return ("variant", "8d")

    for neutral in NEUTRAL_KEYWORDS.values():
        keyword = _contains_any(normalized, neutral)
        if keyword:
            return ("neutral", keyword)

    noise = _contains_any(normalized, NOISE_KEYWORDS)
    if noise:
        return ("noise", noise)

    return ("unknown", text)


def parse_title(title: Any, artists: Any = None) -> ParsedTitle:
    """Parse a display title into a comparable base title and metadata.

    ``artists`` is used to identify and remove a YouTube style artist prefix
    (``Coldplay - Yellow``) as well as trailing ``- Artist`` suffixes.
    """
    raw_title = str(title or "").strip()
    if not raw_title:
        return ParsedTitle(raw_title="", base_title="")

    artist_names = split_artists(artists)
    artist_keys = {normalize_text(name) for name in artist_names if normalize_text(name)}

    version_tags: List[str] = []
    variant_tags: List[str] = []
    featured_artists: List[str] = []
    noise_tags: List[str] = []
    kept_brackets: List[str] = []

    def add_tag(kind: str, value: str) -> None:
        if not value:
            return
        if kind == "variant":
            if value not in variant_tags:
                variant_tags.append(value)
        elif kind == "neutral":
            if value not in version_tags:
                version_tags.append(value)
        elif kind == "featured":
            for name in split_artists(value):
                if name and normalize_text(name) not in {
                    normalize_text(existing) for existing in featured_artists
                }:
                    featured_artists.append(name)
        elif kind == "noise":
            if value not in noise_tags:
                noise_tags.append(value)

    def bracket_repl(match: re.Match) -> str:
        kind, value = _classify_segment(match.group(1))
        if kind == "unknown":
            if value:
                kept_brackets.append(value)
        else:
            add_tag(kind, value)
        return " "

    working = _DASH_RE.sub(" - ", raw_title)
    working = _BRACKET_RE.sub(bracket_repl, working)

    # Inline featured artists (outside brackets), e.g. "Song feat. Artist".
    def inline_repl(match: re.Match) -> str:
        add_tag("featured", match.group(1).strip())
        return ""

    working = _FEAT_INLINE_RE.sub(inline_repl, working)

    parts = [part.strip() for part in working.split(" - ") if part.strip()]

    # Strip an artist prefix from the first remaining segment.
    if len(parts) > 1 and normalize_text(parts[0]) in artist_keys:
        parts.pop(0)

    base_parts: List[str] = []
    for index, part in enumerate(parts):
        kind, value = _classify_segment(part)
        if kind == "unknown":
            normalized_part = normalize_text(part)
            if normalized_part and normalized_part in artist_keys:
                continue
            base_parts.append(part)
        elif kind == "noise":
            add_tag(kind, value)
        else:
            add_tag(kind, value)

    if base_parts:
        base_title = " - ".join(base_parts)
    else:
        # Everything was metadata; fall back to the original title.
        base_title = raw_title

    if kept_brackets:
        base_title = " ".join(
            [base_title] + [f"({segment})" for segment in kept_brackets]
        )

    base_title = re.sub(r"\s+", " ", base_title).strip(" -\u2013\u2014")
    if not base_title:
        base_title = raw_title

    return ParsedTitle(
        raw_title=raw_title,
        base_title=base_title,
        version_tags=version_tags,
        variant_tags=variant_tags,
        featured_artists=featured_artists,
        noise_tags=noise_tags,
    )


# ---------------------------------------------------------------------------
# Canonical conversion
# ---------------------------------------------------------------------------


def _first(data: Dict[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in data and data[key] not in (None, ""):
            return data[key]
    return None


def _coerce_duration_ms(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    if isinstance(value, str):
        match = _DURATION_RE.match(value)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2))
            seconds = int(match.group(3))
            return ((hours * 60 + minutes) * 60 + seconds) * 1000
        try:
            value = float(value)
        except (TypeError, ValueError):
            return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number <= 0:
        return None
    # Values below 1000 are almost certainly seconds, not milliseconds.
    if number < 1000:
        number *= 1000
    return int(round(number))


def _as_mapping(track: Any) -> Dict[str, Any]:
    if isinstance(track, CanonicalTrack):
        return track.model_dump()
    if isinstance(track, dict):
        return dict(track)
    if hasattr(track, "model_dump"):
        try:
            return dict(track.model_dump())
        except Exception:
            pass
    data: Dict[str, Any] = {}
    for key in (
        "title",
        "name",
        "artist",
        "artists",
        "primaryArtists",
        "primary_artists",
        "featuredArtists",
        "featured_artists",
        "album",
        "duration_ms",
        "durationMs",
        "isrc",
        "sourcePlatform",
        "source_platform",
        "sourceId",
        "source_id",
        "id",
    ):
        if hasattr(track, key):
            data[key] = getattr(track, key)
    return data


def _infer_source_platform(data: Dict[str, Any]) -> str:
    explicit = _first(data, ("sourcePlatform", "source_platform", "platform"))
    if explicit:
        return str(explicit)
    for platform in ("spotify", "youtube_music", "apple_music", "manual"):
        if data.get(f"{platform}_id"):
            return platform
    return "unknown"


def _infer_source_id(data: Dict[str, Any], platform: str) -> str:
    explicit = _first(data, ("sourceId", "source_id", "id"))
    if explicit not in (None, ""):
        return str(explicit)
    platform_id = data.get(f"{platform}_id")
    if platform_id not in (None, ""):
        return str(platform_id)
    for candidate_platform in ("spotify", "youtube_music", "apple_music"):
        value = data.get(f"{candidate_platform}_id")
        if value not in (None, ""):
            return str(value)
    return ""


def canonical_from_track(track: Any) -> CanonicalTrack:
    """Build a :class:`CanonicalTrack` from any adapter track representation."""
    if isinstance(track, CanonicalTrack):
        data = track.model_dump()
    else:
        data = _as_mapping(track)

    title = str(_first(data, ("title", "name", "track_name")) or "").strip()

    raw_artists = _first(data, ("artists", "artist", "artistName", "artist_name"))
    artists = split_artists(raw_artists)
    explicit_primary = split_artists(
        _first(data, ("primaryArtists", "primary_artists"))
    )
    explicit_featured = split_artists(
        _first(data, ("featuredArtists", "featured_artists"))
    )

    parsed = parse_title(title, artists or explicit_primary)

    explicit_version_tags = split_artists(
        _first(data, ("versionTags", "version_tags"))
    )
    explicit_variant_tags = split_artists(
        _first(data, ("variantTags", "variant_tags"))
    )
    version_tags = list(parsed.version_tags)
    variant_tags = list(parsed.variant_tags)
    for tag in explicit_version_tags:
        if tag not in version_tags:
            version_tags.append(tag)
    for tag in explicit_variant_tags:
        if tag not in variant_tags:
            variant_tags.append(tag)

    featured = list(explicit_featured)
    for name in parsed.featured_artists:
        if normalize_text(name) not in {normalize_text(item) for item in featured}:
            featured.append(name)

    if explicit_primary:
        primary = list(explicit_primary)
    else:
        primary = [
            name
            for name in artists
            if normalize_text(name)
            not in {normalize_text(featured_name) for featured_name in featured}
        ]
        if not primary:
            primary = list(artists)

    all_artists: List[str] = []
    for name in list(primary) + list(featured) + list(artists):
        key = normalize_text(name)
        if not key:
            continue
        if key in {normalize_text(existing) for existing in all_artists}:
            continue
        all_artists.append(name)

    platform = _infer_source_platform(data)
    source_id = _infer_source_id(data, platform)

    duration = _coerce_duration_ms(
        _first(
            data,
            (
                "durationMs",
                "duration_ms",
                "trackTimeMillis",
                "duration",
                "length",
            ),
        )
    )

    isrc = _first(data, ("isrc", "ISRC", "external_id"))
    if isinstance(isrc, str):
        isrc = isrc.strip() or None
    else:
        isrc = None

    raw = data.get("raw")
    if not isinstance(raw, dict):
        raw = data

    return CanonicalTrack(
        sourcePlatform=platform,
        sourceId=source_id,
        title=title,
        baseTitle=parsed.base_title,
        versionTags=version_tags,
        variantTags=variant_tags,
        artists=all_artists,
        primaryArtists=primary,
        featuredArtists=featured,
        album=_first(data, ("album", "album_name", "collectionName")),
        durationMs=duration,
        isrc=isrc,
        explicit=data.get("explicit"),
        previewUrl=_first(data, ("previewUrl", "preview_url")),
        raw=raw,
    )
