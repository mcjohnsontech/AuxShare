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

## Frontend / OAuth topology
- **Single-origin API calls:** The SPA calls `/api/*` on its own origin and nginx
  proxies those requests to the backend container. `VITE_API_URL` is built as an
  empty string (`aux_share/Dockerfile` default, `docker-compose.yml` build arg).
  Never set it to `/` — that yields `//api/...`, which browsers normalize to
  `http://api/...`. Only set it for `npm run dev` (e.g. `http://localhost:8000`).
- **Cross-origin OAuth callback:** Spotify redirects to the *backend* origin
  (`SPOTIFY_REDIRECT_URI`, e.g. `http://127.0.0.1:8000/api/auth/callback`) while
  the SPA runs on `http://localhost:5173`.
  Because the OAuth `state` is bound to a session cookie, and cookies are
  origin-scoped, login must begin on the **backend** origin. The frontend reads
  `auth_start_url` from `GET /api/config` and performs a top-level navigation to
  `GET /api/auth/start`, which sets `aux_session` for the backend origin and
  redirects to Spotify. The callback therefore receives the cookie the state was
  bound to, and a missing/mismatched cookie is **rejected** (login-CSRF defence).
  After the token exchange the callback issues a short-lived (180s), single-use
  *handoff code* and redirects to `<FRONTEND_URL>/callback?status=success&handoff=...`.
  `CallbackView` POSTs the code to `POST /api/auth/handoff` on its own origin,
  which consumes the code and sets `aux_session` for the frontend origin.
- **Redirect URI matching:** `SPOTIFY_REDIRECT_URI` must match a Redirect URI
  registered in the Spotify dashboard *exactly* (host + port + path). It is
  pinned in `.env` to the verified working value.

## Export idempotency
- **One playlist per export.** `POST /api/export` is idempotent for the tuple
  `(Spotify account id, target platform, session code)`. The record lives in
  Redis (`export:<account>:<platform>:<session>`, 30-day TTL) and holds the
  `playlist_id`, whether the run completed, and the track count.
- **Why not the description marker:** Spotify playlist listing is paginated and
  newly created private playlists are not reliably returned in the first page, so
  a description-marker search alone created duplicates. The marker
  (`converted-by-auxshare:session_<code>`) is now only a **recovery path** for
  playlists created before the Redis record existed.
- **Fast path:** if the record says `completed`, the playlist is verified with a
  single `GET /playlists/{id}?fields=id,tracks(total)` and returned with
  `tracks_added: 0`, `already_existed: true`. If the playlist was deleted on
  Spotify, the record is cleared and a new playlist is created. If verification
  fails for a transport/auth reason, the record is trusted (fail closed: never
  duplicate).
- **No duplicate tracks:** on a resumed run the existing playlist URIs are read
  and only missing tracks are appended. URIs are deduplicated within the request.
- **Concurrency:** a `SET NX EX 180` lock guards playlist creation; a second
  concurrent request gets `409` instead of creating a second playlist.
- **Intentional copies:** send `force_new: true` to deliberately create another
  playlist; the stored record then points at the newest playlist.
- **UI gating:** `GET /api/export/status?session_code=...` reports
  `{authenticated, exported, playlist_url, tracks_in_playlist}` for the current
  account and is verified against Spotify. `ExportButton` disables itself once
  `exported` is true and offers an "Open playlist" link; a deleted playlist
  clears the record and re-enables the button. The check is advisory only — the
  export endpoint stays idempotent regardless, so a stale UI cannot duplicate.

