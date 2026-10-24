# Audit Report - AuxShare

**Date:** 2026-10-24  
**Scope:** Full codebase review as requested

## 1. How URLs are parsed

### Platform detection (`backend/platform_detector.py`)
- **Flow:** `PlatformDetector.detect_platform(url)` matches against platform patterns via `extract_playlist_id` from each handler
- **Supported platforms:** spotify, youtube_music, apple_music, manual_import
- **Manual import:** URLs starting with `manual://` are parsed by `ManualPlatform` which extracts base64/quoted content

### Per-platform URL parsing
| Platform | Method | Patterns | Notes |
|---|---|---|---|
| **Spotify** (`backend/platforms/spotify.py`) | `extract_playlist_id()` via `SpotifyClient.extract_playlist_id()` | `spotify.com/playlist/([a-zA-Z0-9]+)`, `spotify:playlist:([a-zA-Z0-9]+)` | Returns just the ID |
| **YouTube Music** (`backend/platforms/youtube_music.py`) | `extract_playlist_id()` | `list=([a-zA-Z0-9_-]+)`, `playlist/([a-zA-Z0-9_-]+)` | Strips `&si` params |
| **Apple Music** (`backend/platforms/apple_music.py`) | `extract_playlist_id()` | `playlist/[^/]+/(pl\.[a-zA-Z0-9-]+)`, `album/[^/]+/(\d+)` | Also accepts album URLs (as ID) |
| **Manual** (`backend/platforms/manual.py`) | `extract_playlist_id()` / parse from `manual://` URL | Decodes URL-encoded or base64 content | Parses CSV/line-based text |

**Router:** `universal_converter.py` calls `detector.detect_platform()` → gets handler, checks `can_extract`, calls `extract_playlist_id()`, then `get_playlist_tracks()`.

## 2. How tracks are fetched

### Source adapters
| Platform | Fetch method | Auth required | Notes |
|---|---|---|---|
| **Spotify** | `SpotifyClient.get_playlist_tracks()` uses `spotipy` with `SpotifyClientCredentials` | App credentials only | Paginates with `sp.next()`. Has 404 handling for inaccessible playlists. |
| **YouTube Music** | `YouTubeMusicClient.get_playlist()` uses `ytmusicapi` | No user auth (public) | Has retry logic. |
| **Apple Music** | `AppleMusicPlatform.get_playlist_tracks()` | N/A | Raises NotImplementedError - marked as cannot extract as source |
| **Manual** | Parses from URL content | None | Reads inline text/CSV |

Apple Music as source is not supported for extraction - only as target. Universal converter blocks extraction for platforms with `can_extract=False`.

## 3. How matching is done

### Flow (per track)
1. Convert source track to `CanonicalTrack` via `canonical_from_track()`
2. Check `has_blocking_variant()` - rejects if source is live/remix/acoustic etc.
3. **Tier 1 (ISRC)**: If `canonical.isrc` exists, call `search_by_isrc()`. If found, return match with `confidence=1.0`, `match_method="isrc"`
4. **Tier 3 (text search)**: Build query from `baseTitle` + primary artists, call `search_candidates()`, rank with `best_candidate()` using multi-feature scorer

### Components
| Component | Location | Status |
|---|---|---|
| **Normalization** | `backend/matching/normalization.py` | Implemented - Unicode NFKC, diacritics, artist splitting, version tags, featured artists |
| **Scoring** | `backend/matching/scoring.py` | Implemented - Multi-feature scorer with fuzzywuzzy, title/artist/duration weights, thresholds (0.82 overall, 0.85 title min), variant rejection |
| **Canonical models** | `backend/models/canonical.py` | Pydantic models for CanonicalTrack, TargetTrack |
| **Integration** | `backend/platforms/base.py` | Integrated into base class |

**Scoring:** title 0.62/0.66, artist 0.30/0.34, duration 0.08 if available. Duration: <=3s→1.0, <=7s→0.9, <=15s→0.7, <=30s→0.4. Candidate variants rejected (score capped at 0.5). Artist similarity < 0.45 rejected.

**Cache:** Not implemented. **Tier 4 (audio):** Not implemented. **MusicBrainz:** Not implemented.

## 4. How the playlist is created

**Current flow (synchronous):**
1. `POST /api/convert` → `UniversalConverter.convert()` matches all tracks → stores in Redis session via `SessionManager.save_session()` → returns session code
2. User calls `POST /api/export` → gets session, resolves tokens (server-side encrypted preferred), creates playlist via platform, searches/matches tracks again or uses stored IDs, adds in batches of 100, returns success

**Issues vs spec:** No job state machine, no create-first with marker, no per-track status, no read-back verification/reconciliation, no retry/backoff, only Spotify export, no CSV fallback.

## 5. How auth works

- **OAuth:** Spotify with PKCE (S256), state bound to session, scopes `playlist-modify-public playlist-modify-private user-read-private`
- **Tokens:** Encrypted server-side with Fernet/MultiFernet, stored in Redis, rotated on login (session fixation defense)
- **Cookies:** httpOnly session cookie `aux_session`, SameSite=lax, Secure configurable
- **CSRF:** Origin/Referer validation, blocks missing Origin+session cookie, blocks cross-site
- **Reading:** Public playlists with app credentials; no auth needed for source reading where public

## 6. Where state is stored

| Data | Storage | TTL | Notes |
|---|---|---|---|
| **Conversion sessions** | Redis `playlist:{code}` | 24h | Tracks + metadata (JSON). Long codes (22+ chars). Legacy 4-digit deprecated. |
| **OAuth pending state** | Redis via SecureSessionManager | Short-lived | PKCE verifier bound to session |
| **Encrypted OAuth tokens** | Redis `tokens:{session_id}:{platform}` | Managed | Fernet encrypted |
| **Session cookie** | Browser `aux_session` | Session | High-entropy session ID |
| **Rate limiting** | Redis counters | 60s | Session lookup 30/min per IP, fails open on Redis error |

**No SQL/DB** - everything in Redis or in-memory.

## Gap Analysis

### Major gaps vs spec
- **Job system:** No async jobs, state machine, queue/workers
- **Reliable playlist creation:** No create-first+marker, no per-track status, no read-back verification/reconciliation, no resumability
- **Matching tiers:** No cache (pos/neg), no MusicBrainz expansion, no audio verifier, no market awareness
- **Review flow:** No candidates storage, no review API/UI, no user selection/resolution
- **Data model:** Redis-only, missing proper job/track/mapping tables
- **Resilience:** No awaiting_reauth state, no proper retry/backoff, no CSV fallback
- **Error handling:** Limited retry logic

### Strengths
- Good normalization and precision-first scoring
- Solid security (PKCE, CSRF, encrypted tokens, session rotation)
- Working adapter pattern
- Evaluation harness in place
- Good test coverage (48 tests pass)

## Phased Plan

### Phase 0: Audit and baseline ✓ COMPLETE
Audit done, tests pass (48 passed), evaluation shows precision 1.0.

### Phase 1: Reliability (Priority)
Make playlist creation resumable and verifiable:
1. Job state machine with all states
2. Create-first with persisted playlist ID and marker in description
3. Batch add with per-track status tracking
4. Retry/backoff/rate limiting
5. Token refresh and awaiting_reauth state
6. Read-back verification and reconciliation
7. Honest reporting with real counts
8. CSV fallback on permanent failure

### Phase 2: Matching quality
1. Configurable version policy table
2. Improved ISRC handling
3. Mapping cache with positive/negative entries (TTL)
4. Market-aware search
5. Negative cache to avoid retries

### Phase 3: Review flow
1. Store candidates for uncertain tracks
2. Review API and UI
3. Idempotent selection
4. Position-aware insertion
5. Review events logging

### Phase 4: Scale and structure
Queue/workers, SSE/polling progress, adapter interface cleanup

### Phase 5: Research tier (if justified)
MusicBrainz expansion, audio verifier behind flag, scorer retraining

**Starting with Phase 1.**
