# Decisions Log

All "verify" items from the spec have been checked and documented.

## Platform API verifications

### Spotify
- **Auth scopes:** Using `playlist-modify-public playlist-modify-private user-read-private` (minimum required for creating and managing playlists). Verified against Spotify Web API docs.
- **Create playlist:** `POST https://api.spotify.com/v1/users/{user_id}/playlists` - confirmed.
- **Add tracks:** `POST https://api.spotify.com/v1/playlists/{playlist_id}/tracks` with `uris` array, max 100 per request - confirmed.
- **Search:** `GET https://api.spotify.com/v1/search` - confirmed.
- **Playlist size limit:** ~10,000 tracks (Spotify limit) - noted.
- **Rate limits:** 429 responses possible, need to honor Retry-After - implemented backoff.
- **Editorial/algorithmic playlists:** Return 404 when not accessible via app credentials - handled with clear error message.

### YouTube Music
- **Library:** Using `ytmusicapi` for access. Public playlists readable where possible.
- **Note:** No official public API for all operations; using ytmusicapi as existing solution.

### Apple Music
- **Source extraction:** Not supported without MusicKit - blocked as source, allowed as target only.
- **Target matching:** Using iTunes Search API (free) for matching - confirmed working.

### Redis
- **Sessions:** Stored with 24h TTL.
- **Rate limiting:** Fails open on Redis errors (as implemented).

## Matching decisions
- **Precision-first:** Never auto-add variant recordings (live/remix/cover). Hard reject policy implemented.
- **ISRC priority:** ISRC lookups take precedence, cached.
- **Cache:** Negative results cached with 7-day TTL, positive with 30-day TTL.
- **Thresholds:** Auto-add >= 0.90, needs review 0.60-0.90, unmatched < 0.60 (configurable).

## Security
- **PKCE:** Implemented with S256.
- **State binding:** OAuth state bound to session.
- **Token encryption:** Fernet encryption at rest.
- **Session rotation:** After login to prevent fixation.
- **CSRF:** Origin/Referer validation.
- **Log redaction:** Tokens, codes, states redacted from logs.
