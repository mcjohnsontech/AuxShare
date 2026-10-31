<p align="center">
  <img src="aux_share/public/favicon.svg" width="72" height="72" alt="AuxShare logo" />
</p>

<h1 align="center">AuxShare</h1>

<p align="center">
  Move a playlist. Keep the mix.<br />
  Convert playlists between Spotify, Apple Music and YouTube Music — then share one link, no account required.
</p>

<p align="center">
  <a href="https://vuejs.org/"><img alt="Vue 3" src="https://img.shields.io/badge/Vue-3-42b883?logo=vuedotjs&logoColor=white" /></a>
  <a href="https://fastapi.tiangolo.com/"><img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi&logoColor=white" /></a>
  <a href="https://redis.io/"><img alt="Redis" src="https://img.shields.io/badge/Redis-7-dc382d?logo=redis&logoColor=white" /></a>
  <a href="https://www.docker.com/"><img alt="Docker" src="https://img.shields.io/badge/Docker-Compose-2496ed?logo=docker&logoColor=white" /></a>
</p>

---

## Overview

AuxShare is a self-hostable playlist converter. Paste a public Spotify or YouTube Music playlist link, choose a destination platform, and AuxShare searches the target catalog, scores every match by confidence, and stores the result as a shareable link. Recipients open the link and browse the converted track list — no login needed.

Three services make up the stack:

- **Frontend** — Vue 3 SPA built with Vite, served as static files.
- **Backend** — FastAPI service that extracts playlists, matches tracks, manages OAuth and exports to Spotify.
- **Redis** — Session storage for converted playlists, OAuth state and export idempotency.

## Features

- Convert **Spotify** and **YouTube Music** playlists to **Spotify**, **Apple Music** or **YouTube Music**.
- Confidence-scored matching with high, medium and low buckets surfaced in the UI.
- Review the full track list before sharing, with direct links to each matched track.
- One shareable link per conversion with no account requirement for listeners.
- In-page playback where supported: Apple Music previews and YouTube playback.
- Spotify OAuth export to a private playlist, idempotent per account and session.
- Responsive, accessible interface with keyboard support and reduced-motion handling.
- Docker Compose deployment with health checks, Redis persistence and an nginx reverse proxy.

## Supported platforms

| Platform | Source | Destination | Notes |
|---|:---:|:---:|---|
| Spotify | ✓ | ✓ | Client credentials for reads; OAuth + PKCE for export |
| YouTube Music | ✓ | ✓ | Anonymous `ytmusicapi`; public playlists |
| Apple Music | — | ✓ | iTunes Search API; no Apple credentials required |

Apple Music is destination-only. YouTube Music extraction depends on public playlist availability.

## Architecture

```
Browser
  │
  ├── Vue 3 SPA (Vite build)
  │      │
  │      └── /api/* ──► nginx (Docker) or Netlify proxy
  │                           │
  │                           ▼
  │                     FastAPI backend
  │                      ├── platform adapters
  │                      ├── confidence-scored matching
  │                      ├── OAuth / PKCE / CSRF
  │                      ├── export idempotency
  │                      └── Redis session storage
  │
  └── Share link: /join/<session-code>
```

The frontend calls the API on its own origin. In Docker, nginx proxies `/api` to the backend container. On Netlify, `netlify.toml` configures the same behavior. Keeping the API same-origin avoids CORS and cross-site cookie issues.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3, Vue Router, Pinia, Vite |
| Styling | Custom CSS design tokens, Lucide icons |
| Backend | Python 3.11+, FastAPI, Pydantic, Uvicorn |
| Music APIs | Spotipy, `ytmusicapi`, iTunes Search API |
| Storage | Redis 7 |
| Deployment | Docker Compose, nginx, Netlify |

## Quick start with Docker

**Prerequisites:** Docker Desktop (or Docker Engine + Compose v2) and a Spotify developer application.

```bash
# 1. Copy and fill in the environment file
cp .env.example .env

# 2. Build and start the stack
docker compose up --build -d

# 3. Open http://localhost:5173
```

The API is available at `http://localhost:8000` with interactive docs at `/docs` and `/redoc`.

```bash
docker compose logs -f          # all logs
docker compose logs -f backend  # API logs only
docker compose down             # stop, keep Redis data
docker compose down -v          # stop and delete Redis data
docker compose exec redis redis-cli
```

## Local development

**Prerequisites:** Python 3.10+, Node.js 20+, Redis on `localhost:6379`.

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd aux_share
npm install
npm run dev
```

Create `aux_share/.env.local` to point the dev server at the local API:

```dotenv
VITE_API_URL=http://localhost:8000
VITE_SITE_URL=http://localhost:5173
```

Leave `VITE_API_URL` empty for Docker or Netlify, where `/api` is proxied on the same origin.

### Tests

```bash
python -m pytest
```

The test suite runs entirely against local fixtures and mocks. No Spotify, YouTube Music or Apple Music calls are made.

## Configuration

| Variable | Required | Description |
|---|:---:|---|
| `FRONTEND_URL` | Yes | Public frontend origin, used in share links and CORS. |
| `BACKEND_URL` | Yes | Public backend origin. |
| `SPOTIFY_REDIRECT_URI` | Yes | Spotify OAuth callback URL. Must match the dashboard exactly. |
| `SPOTIPY_CLIENT_ID` | Yes | Spotify application client ID. |
| `SPOTIPY_CLIENT_SECRET` | Yes | Spotify application client secret. |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` | Yes | Redis connection. Compose sets host to `redis`. |
| `ENVIRONMENT` | No | `production` restricts CORS to `FRONTEND_URL`. Defaults to `development`. |
| `COOKIE_SECURE` | Production | Set `true` when served over HTTPS. |
| `COOKIE_SAMESITE` | No | `lax` (default), `strict`, or `none`. |
| `AUXSHARE_ENCRYPTION_KEYS` | Production | Comma-separated Fernet key(s) for OAuth token encryption. Required in production. |
| `VITE_SITE_URL` | No | Canonical origin for Open Graph, Twitter and JSON-LD. Defaults to `https://aux-share.vercel.app`. |
| `VITE_API_URL` | No | Absolute API URL. Leave empty when `/api` is proxied. |

Never commit `.env`. Only `.env.example` belongs in version control.

## Spotify setup

1. Create an application in the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Under **Redirect URIs**, add:
   - Local: `http://127.0.0.1:8000/api/auth/callback`
   - Production: `https://auxshare-api-40b1a9433585.herokuapp.com/api/auth/callback`
3. Copy the client ID and secret into `SPOTIPY_CLIENT_ID` and `SPOTIPY_CLIENT_SECRET`.
4. Set `SPOTIFY_REDIRECT_URI` to match the registered callback exactly.

> **Note:** Spotify rejects `localhost` in redirect URIs — use `127.0.0.1` for local development.

## Production deployment

### Production: Vercel frontend and Heroku backend

- Frontend: https://aux-share.vercel.app
- Backend: https://auxshare-api-40b1a9433585.herokuapp.com

In Vercel, set the root directory to `aux_share`, framework to Vite, build
command to `npm run build`, and output directory to `dist`.
`aux_share/.env.production` contains the public production build URLs. Any
Vercel environment variables override these values, so update existing
`VITE_SITE_URL` and `VITE_API_URL` variables to match, then redeploy.

Set these Heroku Config Vars (the local `.env` is not uploaded to Heroku):

```dotenv
ENVIRONMENT=production
FRONTEND_URL=https://aux-share.vercel.app
BACKEND_URL=https://auxshare-api-40b1a9433585.herokuapp.com
SPOTIFY_REDIRECT_URI=https://auxshare-api-40b1a9433585.herokuapp.com/api/auth/callback
COOKIE_SECURE=true
COOKIE_SAMESITE=none
```

Keep Spotify credentials, `REDIS_URL`, and `AUXSHARE_ENCRYPTION_KEYS` in Heroku
Config Vars. Register the exact `SPOTIFY_REDIRECT_URI` above in the Spotify
Developer Dashboard. Deploy from the repository root using the existing
`Procfile` for the web and worker processes.

Docker retains its same-origin nginx API proxy and explicitly builds with an
empty `VITE_API_URL`. For local development, use the `.env.local` values above;
use localhost frontend/backend URLs and development cookie settings in your
local backend environment.

### Link previews

Open Graph and Twitter card tags are present in the built HTML, so crawlers do
not need to execute Vue. Both the homepage and `/join/:code` routes receive
this metadata through the SPA fallback. The public preview is the optimized
1200 × 630 `playlist-sharing-preview.jpg`; the PNG is the source asset.

After building, verify the preview locally or against your deployed frontend:

```bash
cd aux_share
npm run build
npm run check:preview
npm run check:preview -- https://aux-share.vercel.app
```

The deployed check verifies that a crawler can read metadata on the homepage
and a shared-link route, and that the image URL returns JPEG bytes. Deploy the
frontend changes before running it against production. Existing chat previews
may retain a cached card until that service fetches the page again.

### Frontend on Netlify

The repo includes [`netlify.toml`](./netlify.toml). Configure the Netlify build as:

- Base directory: `aux_share`
- Build command: `npm run build`
- Publish directory: `dist`

Set `VITE_SITE_URL` in Netlify to your production domain. To proxy the API on the same origin, uncomment the redirect in `netlify.toml`:

```toml
[[redirects]]
  from = "/api/*"
  to = "https://auxshare-api-40b1a9433585.herokuapp.com/api/:splat"
  status = 200
  force = true
```

Leave `VITE_API_URL` empty in that case.

### Backend with Docker Compose

```bash
cp .env.example .env
# Edit .env for production values
docker compose up --build -d
```

Production checklist:

- `ENVIRONMENT=production`
- `COOKIE_SECURE=true`
- `AUXSHARE_ENCRYPTION_KEYS` set — generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- `FRONTEND_URL` and `BACKEND_URL` are HTTPS origins
- Production Spotify redirect URI registered
- API behind HTTPS (reverse proxy or TLS terminator)
- Redis not exposed on a public port
- `/api/health` monitored for liveness

## API reference

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/health` | Redis and service health. |
| `GET` | `/api/platforms` | All supported platforms. |
| `GET` | `/api/platforms/sources` | Platforms usable as a source. |
| `GET` | `/api/platforms/targets` | Platforms usable as a destination. |
| `POST` | `/api/convert` | Convert a playlist and create a session. |
| `GET` | `/api/session/{code}` | Retrieve a session and its tracks. |
| `GET` | `/api/session/{code}/ttl` | Remaining session lifetime. |
| `GET` | `/api/auth/login` | Get a Spotify authorization URL. |
| `GET` | `/api/auth/callback` | Exchange a Spotify authorization code. |
| `GET` | `/api/auth/status` | Current Spotify authentication status. |
| `POST` | `/api/export` | Create or reuse a Spotify playlist for a session. |

```bash
# Convert a playlist
curl -X POST http://localhost:8000/api/convert \
  -H "Content-Type: application/json" \
  -d '{"url":"https://open.spotify.com/playlist/PLAYLIST_ID","target_platform":"apple_music"}'
```

Export is idempotent per `(Spotify account, session code)`. Repeating the request returns the existing playlist.

## Project structure

```
AuxShare/
├── aux_share/                 # Vue 3 + Vite frontend
│   ├── public/                # Icons, OG image, web manifest, robots.txt
│   ├── src/components/        # Converter, results, player, sharing and export UI
│   ├── src/views/             # Home, join and OAuth callback pages
│   ├── src/stores/            # Pinia state
│   ├── src/services/          # API client
│   ├── nginx.conf             # SPA fallback and /api reverse proxy
│   └── Dockerfile
├── backend/                   # FastAPI service
│   ├── main.py                # API routes
│   ├── universal_converter.py # Conversion pipeline
│   ├── platform_detector.py   # URL detection and platform registry
│   ├── platforms/             # Spotify, YouTube Music, Apple Music adapters
│   ├── matching/              # Normalization, scoring and policy
│   ├── jobs/                  # Background job pipeline
│   ├── security/              # OAuth, PKCE, CSRF, encryption, redaction
│   ├── evaluation/            # Offline matching harness and fixtures
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── Dockerfile
├── tests/                     # Pytest suite
├── docker-compose.yml
├── netlify.toml
├── pytest.ini
└── .env.example
```

## Security

- Spotify OAuth uses PKCE with state bound to an httpOnly session cookie.
- State-changing requests are protected by CSRF origin validation.
- OAuth tokens are encrypted at rest; `code` and `state` query parameters are redacted from access logs.
- Share codes are cryptographically random URL-safe identifiers.
- Sessions expire after 24 hours; exports are idempotent per account and session.
- Session lookup is rate-limited per IP.
- The backend refuses to start in production if `AUXSHARE_ENCRYPTION_KEYS` is unset.

## Limitations

- Apple Music is destination-only. Source extraction requires Apple Developer MusicKit credentials.
- YouTube Music extraction depends on `ytmusicapi` and public playlist availability.
- Matching is metadata-based and cannot guarantee an exact recording (live vs. studio, remix, etc.).
- Sessions require Redis and expire after 24 hours.

## Trademarks

AuxShare is an independent project and is not affiliated with, endorsed by, or sponsored by Spotify, Apple, Google or YouTube. All platform names and logos are trademarks of their respective owners.
