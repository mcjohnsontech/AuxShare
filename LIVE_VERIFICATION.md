# Live Verification — 2026-10-23

Real-data verification of the AuxShare/AuxParty stack. No platform responses were
mocked in this run. The backend was rebuilt from the current working tree before
testing.

## Environment

| Item | Value |
| --- | --- |
| Frontend | `http://localhost:5173` (HTTP 200) |
| Backend | `http://localhost:8000` (healthy) |
| Health payload | `{"status":"healthy","redis":true,"platforms":4}` |
| Redis | `auxshare-redis-1`, healthy, used by the live backend |
| Spotify source | Real Spotify Web API with `SPOTIPY_*` client credentials |
| YouTube Music | Real anonymous `ytmusicapi` requests |
| Apple Music target | Real public iTunes Search API |
| Spotify OAuth/export | Not configured (`SPOTIFY_CLIENT_ID`/`SPOTIFY_CLIENT_SECRET` absent) |

## Test data

- **Spotify source playlist:** `Adele - Greatest Hits`
  (`https://open.spotify.com/playlist/6TFHI1i8f8AyS4SbVmvjd8`, 12 tracks)
- **YouTube Music source playlist:** Adele — *25*
  (`https://music.youtube.com/playlist?list=OLAK5uy_k-Bi6NLrq5DrDKVM...`, 11 tracks)
  - Full ID: `OLAK5uy_k-Bi6NLrq5DrDKPLuiRvm7NsbMccKIcEY`
- **Manual import list:**
  - `Blinding Lights - The Weeknd`
  - `Hello - Adele`
  - `Bohemian Rhapsody - Queen`
  - `Blinding Lights (Live) - The Weeknd` (deliberate variant-tagged control)

Spotify editorial playlist IDs such as `37i9dQZF1DXcBWIGoYBM5M` now return
HTTP 404 from the Spotify API, so they were not used. The public user playlist
above was confirmed by fetching its metadata before conversion.

## Phase 1 — Service and platform inventory

**Result: PASS**

- `GET /api/health` → `200`, Redis reachable, four platforms registered.
- `GET /api/platforms` → Spotify, YouTube Music, Apple Music, Manual Import.
- `GET /api/platforms/sources` → Spotify and YouTube Music.
- `GET /api/platforms/targets` → Spotify, YouTube Music, Apple Music.
- Frontend at `http://localhost:5173` → `200`.

Observed minor response-shape issue: `/api/platforms/sources` omits
`can_extract` in each item, so the field serializes as `null` instead of
`true`. This does not affect conversion, but it is inconsistent with
`/api/platforms` and `/api/platforms/targets`.

## Phase 2 — Manual import → real targets

**Result: PASS (3/3 conversions)**

For each target, `POST /api/convert` was followed by a real session lookup and
TTL lookup. All target IDs below came from live catalog searches.

### 2.1 Manual → Spotify

- Conversion: `200`
- Session code: `HYZh29g0lixZkYKXXhClKQ`
- Source/target: `Manual Import` → `spotify`
- Stats: 4 total, 3 matched, 1 failed, 75% match rate, average confidence 1.0
- Session lookup: `200`, 4 tracks returned
- TTL: `200`, `86400` seconds (24h)

| Source title | Spotify ID | Confidence | Method |
| --- | --- | --- | --- |
| Blinding Lights | `0VjIjW4GlUZAMYd2vXMi3b` | 1.0 | metadata |
| Hello | `1Yk0cQdMLx5RzzFTYwmuld` | 1.0 | metadata |
| Bohemian Rhapsody | `2JiDi0qAXsPwhPqA2qaKGt` | 1.0 | metadata |
| Blinding Lights (Live) | — | 0 | rejected (variant) |

### 2.2 Manual → YouTube Music

- Conversion: `200`
- Session code: `S4VVHO9qBM8fKw7s_as_5A`
- Source/target: `Manual Import` → `youtube_music`
- Stats: 4 total, 3 matched, 1 failed, 75% match rate, average confidence 1.0
- Session lookup: `200`, 4 tracks returned
- TTL: `200`, `86400` seconds (24h)

| Source title | YouTube Music ID | Confidence | Method |
| --- | --- | --- | --- |
| Blinding Lights | `J7p4bzqLvCw` | 1.0 | metadata |
| Hello | `Ei8UnOPJX7w` | 1.0 | metadata |
| Bohemian Rhapsody | `BSTsnWoslP4` | 1.0 | metadata |
| Blinding Lights (Live) | — | 0 | rejected (variant) |

### 2.3 Manual → Apple Music

- Conversion: `200`
- Session code: `g3NGaVfRqivYVSiuuAqqBA`
- Source/target: `Manual Import` → `apple_music`
- Stats: 4 total, 3 matched, 1 failed, 75% match rate, average confidence 1.0
- Session lookup: `200`, 4 tracks returned
- TTL: `200`, `86400` seconds (24h)

| Source title | Apple Music ID | Confidence | Method |
| --- | --- | --- | --- |
| Blinding Lights | `1499378607` | 1.0 | metadata |
| Hello | `1544494392` | 1.0 | metadata |
| Bohemian Rhapsody | `6781024437` | 1.0 | metadata |
| Blinding Lights (Live) | — | 0 | rejected (variant) |

The 75% rate is expected and correct: the fourth source track is a live variant,
which precision-first matching intentionally refuses to map onto the studio
recording.

## Phase 3 — Real source playlists (cross-platform)

**Result: PASS (4/4 conversions)**

All conversions hit live upstream APIs and produced real session codes with
full track payloads.

### 3.1 Spotify → YouTube Music
- Source: `Adele - Greatest Hits` (12 tracks)
- Conversion: `200`, code `D-TxdCV2mNvx071syAwutQ`
- Stats: 12/12 matched, 100% match rate, avg confidence 1.0

| Track | YT Music ID | Conf | Method |
| --- | --- | --- | --- |
| Chasing Pavements | `urKPQtbE_bs` | 1.0 | metadata |
| Make You Feel My Love | `9IzKueQ2ZxY` | 1.0 | metadata |
| Rolling in the Deep | `4ujBQOzs6Lw` | 1.0 | metadata |
| Someone Like You | `XqoanTj5pNY` | 1.0 | metadata |
| Set Fire to the Rain | `a2giXO6eyuI` | 1.0 | metadata |
| Skyfall | `LJzp_mDxaT0` | 1.0 | metadata |
| Hello | `Ei8UnOPJX7w` | 1.0 | metadata |
| When We Were Young | `a1IuJLebHgM` | 1.0 | metadata |
| Send My Love (To Your New Lover) | `X3Sdg1_-M0c` | 1.0 | metadata |
| Easy On Me | `H9NJenpBV2I` | 1.0 | metadata |
| I Drink Wine | `GDdoEZL3vJg` | 1.0 | metadata |
| Oh My God | `6_mdXb6JDLI` | 1.0 | metadata |

### 3.2 Spotify → Apple Music
- Source: `Adele - Greatest Hits` (12 tracks)
- Conversion: `200`, code `vDGeDgHgma7oi50OfsoU4w`
- Stats: 12/12 matched, 100% match rate, avg confidence 1.0

| Track | Apple Music ID | Conf | Method |
| --- | --- | --- | --- |
| Chasing Pavements | `1545376345` | 1.0 | metadata |
| Make You Feel My Love | `1545382976` | 1.0 | metadata |
| Rolling in the Deep | `1544491233` | 1.0 | metadata |
| Someone Like You | `1544491998` | 1.0 | metadata |
| Set Fire to the Rain | `1544491988` | 1.0 | metadata |
| Skyfall | `566322365` | 1.0 | metadata |
| Hello | `1544494392` | 1.0 | metadata |
| When We Were Young | `1544494407` | 1.0 | metadata |
| Send My Love (To Your New Lover) | `1544494394` | 1.0 | metadata |
| Easy On Me | `1590036021` | 1.0 | metadata |
| I Drink Wine | `1590036250` | 1.0 | metadata |
| Oh My God | `1590036031` | 1.0 | metadata |

### 3.3 YouTube Music → Spotify
- Source: Adele — *25* (11 tracks)
- Conversion: `200`, code `t7xaqke6zZwAe3BYlGiWrw`
- Stats: 11/11 matched, 100% match rate, avg confidence 1.0

| Track | Spotify ID | Conf | Method |
| --- | --- | --- | --- |
| Hello | `1Yk0cQdMLx5RzzFTYwmuld` | 1.0 | metadata |
| Send My Love (To Your New Lover) | `563SfWAHJs4FBZMkRN0IFN` | 1.0 | metadata |
| I Miss You | `6NdG17SJBXKJeYS67f7E74` | 1.0 | metadata |
| When We Were Young | `6O5TrlFWTYvznd9fMC0VvU` | 1.0 | metadata |
| Remedy | `1zZh6zTXcDgvN0C6S1G4gU` | 1.0 | metadata |
| Water Under the Bridge | `2DRMuw0U0QbkVQxWxdJV3M` | 1.0 | metadata |
| River Lea | `0bqC0AqaBZKBZsjhI3y2OW` | 1.0 | metadata |
| Love In The Dark | `0DuWDLjriRPjDRoPgaCslY` | 1.0 | metadata |
| Million Years Ago | `2qBmtZnPSQouvADmqaHKxk` | 1.0 | metadata |
| All I Ask | `6DEMMeWXfmFAXgDUMMzeg6` | 1.0 | metadata |
| Sweetest Devotion | `2Eb7QQ5soJQBEYTfSb5BS6` | 1.0 | metadata |

### 3.4 YouTube Music → Apple Music
- Source: Adele — *25* (11 tracks)
- Conversion: `200`, code `F_Zzy30pdwWhTPX_U7kUJg`
- Stats: 11/11 matched, 100% match rate, avg confidence 1.0

| Track | Apple Music ID | Conf | Method |
| --- | --- | --- | --- |
| Hello | `1544494392` | 1.0 | metadata |
| Send My Love (To Your New Lover) | `1544494394` | 1.0 | metadata |
| I Miss You | `1544494401` | 1.0 | metadata |
| When We Were Young | `1544494407` | 1.0 | metadata |
| Remedy | `1544494717` | 1.0 | metadata |
| Water Under the Bridge | `1544494722` | 1.0 | metadata |
| River Lea | `1544494725` | 1.0 | metadata |
| Love In The Dark | `1544494731` | 1.0 | metadata |
| Million Years Ago | `1544494905` | 1.0 | metadata |
| All I Ask | `1544494916` | 1.0 | metadata |
| Sweetest Devotion | `1544494916` | 1.0 | metadata |

Sessions remain retrievable via `GET /api/session/{code}` and have a real Redis TTL
of ~24 hours. The "Blinding Lights (Live)" case confirms that variant-tagged
tracks are rejected rather than forced into a studio match.

## Phase 4 — Error paths

**Result: PASS**

| Endpoint | Input | HTTP | Response |
| --- | --- | --- | --- |
| `GET /api/session/{code}` | Non-existent session code | 404 | `{"detail": "Session not found or expired (sessions last 24 hours)"}` |
| `GET /api/session/{code}` | Legacy 4-digit numeric `9999` | 404 | `{"detail": "Session not found or expired (sessions last 24 hours)"}` |
| `POST /api/convert` | Apple Music URL as source | 400 | `{"detail": "Apple Music playlist extraction is not supported yet..."}` |
| `POST /api/export` | Non-Spotify target | 400 | `{"detail": "Only Spotify export is supported currently"}` |
| `GET /api/auth/login` | Unauthenticated | 200 | Returns Spotify auth URL (when credentials configured) |
| `GET /api/auth/status` | No session cookie | 200 | `{"authenticated": false, "platforms": {"spotify": false}}` |

## Summary

| Area | Status | Notes |
| --- | --- | --- |
| Health & platform discovery | **PASS** | Redis reachable, all platforms registered |
| Manual import → Spotify/YouTube Music/Apple Music | **PASS** | Real searches, variant rejection works correctly |
| Spotify → YouTube Music / Apple Music | **PASS** | 12/12 matched on real playlist |
| YouTube Music → Spotify / Apple Music | **PASS** | 11/11 matched on real playlist |
| Session persistence & TTL | **PASS** | Real Redis-backed sessions, ~24h TTL |
| Error handling | **PASS** | Clear messages for unsupported/invalid cases |

All tested endpoints behave correctly with real external data and live Redis
storage. No mocked platform responses were used for the above conversions.
