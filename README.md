# AuxShare

AuxShare (shown as **AuxParty** in parts of the UI and API) converts public music
playlists between supported streaming platforms and creates a short-lived link
that other people can use to view and play the matched tracks.

The project is split into:

- A Vue 3 single-page application in [`aux_share/`](./aux_share/)
- A FastAPI service in [`backend/`](./backend/)
- Redis for temporary playlist sessions

## What it does

1. Paste a public Spotify or YouTube Music playlist URL.
2. Choose a target platform.
3. The backend fetches the source tracks and searches the target catalog.
4. Matching statistics and the converted track list are saved in Redis.
<!-- There should be a layer of creating a playlist on the reciever's platform and filling it with the just acquired music -->
5. The frontend displays a share URL such as
   `http://localhost:5173/join/<session-code>`.
6. Anyone with the link can view the session until it expires. Session codes are
   cryptographically random, URL-safe identifiers; legacy four-digit codes are
   still accepted during their deprecation window.

The frontend also includes a Spotify OAuth flow for exporting a Spotify-targeted
session to a private Spotify playlist.

## Supported platforms

| Platform | Source playlists | Target matching | Notes |
| --- | --- | --- | --- |
| Spotify | Yes | Yes | Uses Spotipy and Spotify Client Credentials |
| YouTube Music | Yes | Yes | Uses `ytmusicapi`; public playlists work best |
| Apple Music | No | Yes | Uses the free iTunes Search API; playlist extraction requires Apple Music MusicKit |

Apple Music can therefore be selected as a destination, but an Apple Music
playlist URL cannot currently be used as the source. YouTube Music requests may
also fail when the upstream site/API changes or a playlist is private.

### YouTube Music connection

YouTube Music is accessed through [`ytmusicapi`](https://github.com/sigma67/ytmusicapi)
using its anonymous client:

```python
YTMusic()
```

The current code does **not** use the official YouTube Data API, so no
`YOUTUBE_API_KEY`, OAuth client ID, or OAuth secret belongs in `.env`. The
backend can search tracks and read publicly available playlists without
YouTube credentials. This is also why the integration can be affected by
changes to YouTube Music, rate limits, network restrictions, or private
playlists.

If authenticated YouTube Music access is added later, it should be implemented
in [`backend/youtube_music_client.py`](./backend/youtube_music_client.py) and
documented with a specific credential variable; adding an unused environment
variable now would not change the connection behavior.

## Architecture

### Frontend

The Vue application uses Vue Router and Pinia:

- [`src/views/HomeView.vue`](./aux_share/src/views/HomeView.vue) hosts playlist
  conversion and the generated session details.
- [`src/views/JoinView.vue`](./aux_share/src/views/JoinView.vue) loads and plays  a shared session.
- [`src/components/PlaylistInput.vue`](./aux_share/src/components/PlaylistInput.vue)
  accepts the source URL and target platform.
- [`src/stores/playlist.js`](./aux_share/src/stores/playlist.js) manages
  conversion/session state.
- [`src/services/api.js`](./aux_share/src/services/api.js) calls the backend.

In the containerized deployment, `VITE_API_URL` is built as an empty string, so
the browser calls `/api/*` on the frontend's own origin. Nginx serves the built
frontend and proxies `/api` requests to the backend container — no CORS and no
cross-origin cookie problems.

When running the Vite dev server (`npm run dev`), set `VITE_API_URL` to the
backend origin, for example in `aux_share/.env.local`:

```dotenv
VITE_API_URL=http://localhost:8000
```

### Backend

[`backend/main.py`](./backend/main.py) exposes the FastAPI API. The conversion
pipeline is implemented by:

1. [`platform_detector.py`](./backend/platform_detector.py), which identifies
   the source URL and selects a platform adapter.
2. [`universal_converter.py`](./backend/universal_converter.py), which extracts
   tracks, searches the target platform, and calculates confidence statistics.
3. Platform adapters in [`backend/platforms/`](./backend/platforms/), which
   normalize platform-specific APIs into a common interface.
4. [`session_manager.py`](./backend/session_manager.py), which stores converted
   results in Redis under a cryptographically random, URL-safe session code.

Sessions expire after 24 hours by default.

## Prerequisites

- Python 3.10+ (3.11 is recommended)
- Node.js 20.19+ or 22.12+
- Redis running on `localhost:6379`
- Spotify developer credentials for Spotify playlist extraction
- A Spotify application with the backend redirect URI
  `http://127.0.0.1:8000/api/auth/callback` if Spotify export is needed.
  Set `SPOTIFY_REDIRECT_URI` if your deployment uses a different public backend URL.

## Setup

### 1. Start Redis

Run Redis locally and confirm that it is available on port `6379`. The backend
reads `REDIS_HOST`, `REDIS_PORT`, and `REDIS_DB` (defaults shown below) and
connects to:

```text
redis://localhost:6379/0
```

If you use Docker Compose, the `redis` service is only reachable inside the
Compose network. Run the backend in Compose as well, or start a separate Redis
instance on the host for a locally run backend.

### 2. Configure backend credentials

Create `backend/.env` (it is ignored by Git):

```dotenv
# Used by Spotify playlist extraction
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret

# Used by the Spotify OAuth export flow
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

# Redis (Docker Compose changes REDIS_HOST to "redis")
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Optional legacy Apple Music API client
APPLE_MUSIC_PRIVATE_KEY_PATH=
APPLE_TEAM_ID=
APPLE_KEY_ID=
```

The two Spotify variable pairs are currently both used by the code:
`SPOTIPY_*` by playlist extraction and `SPOTIFY_*` by OAuth login/callback.
The Apple Music values are optional; the active free integration uses the
iTunes Search API and does not need them.

The complete variable list is also available in
[`.env.example`](./.env.example). Never commit real credentials or private key
contents.

### 3. Install and run the backend

From the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API is then available at <http://localhost:8000>. Interactive API
documentation is available at <http://localhost:8000/swagger> (ReDoc at <http://localhost:8000/redoc>).

### 4. Install and run the frontend

In a second terminal:

```powershell
cd aux_share
npm install
npm run dev
```

Open the Vite URL shown in the terminal, normally
<http://localhost:5173>.

For local development the backend runs on a different origin, so create
`aux_share/.env.local` pointing at it:

```dotenv
VITE_API_URL=http://localhost:8000
```

## Docker Compose deployment

The repository is structured as a monorepo with one Compose stack containing:

- `frontend`: a production Vite build served by Nginx
- `backend`: the FastAPI service
- `redis`: Redis session storage with a persistent named volume

Copy the example environment file, add the required Spotify credentials, and
start the stack:

```powershell
Copy-Item .env.example .env
# Edit .env with your Spotify credentials and public FRONTEND_URL
docker compose up --build -d
```

The application is available at <http://localhost:5173>, the backend API at
<http://localhost:8000>, and the API documentation at
<http://localhost:8000/swagger> (ReDoc at <http://localhost:8000/redoc>). Follow service logs with:

```powershell
docker compose logs -f
```

Stop the services without deleting Redis data with:

```powershell
docker compose down
```

For a hosted deployment, set `FRONTEND_URL` to the public frontend URL and
register `<FRONTEND_URL>/callback` as an allowed redirect URI in the Spotify
developer dashboard. `FRONTEND_PORT` and `BACKEND_PORT` can be changed when the
host ports are already in use.

## API overview

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/` | Basic service information |
| `GET` | `/api/health` | Health check including Redis status |
| `GET` | `/api/platforms` | List all supported platforms |
| `GET` | `/api/platforms/sources` | List source-capable platforms |
| `GET` | `/api/platforms/targets` | List target platforms |
| `POST` | `/api/convert` | Convert a playlist and create a session |
| `GET` | `/api/session/{code}` | Retrieve a shared session |
| `GET` | `/api/session/{code}/ttl` | Check remaining session lifetime |
| `GET` | `/api/auth/login` | Get a Spotify authorization URL |
| `GET` | `/api/auth/callback` | Exchange a Spotify authorization code |
| `POST` | `/api/export` | Create a Spotify playlist from a Spotify-targeted session |

Example conversion request:

```powershell
curl -X POST http://localhost:8000/api/convert `
  -H "Content-Type: application/json" `
  -d '{"url":"https://open.spotify.com/playlist/PLAYLIST_ID","target_platform":"apple_music"}'
```

## Matching statistics

Each conversion reports:

- Total tracks
- Matched and failed tracks
- Overall match rate
- Average confidence
- High-confidence matches (`>= 90%`)
- Medium-confidence matches (`70%` to `< 90%`)
- Low-confidence matches (`< 70%`)

Matched tracks include platform-specific IDs and playback URLs where the
adapter can provide them. Matching is metadata-based for most cross-platform
searches, so results should be reviewed before treating them as exact.

## Useful development commands

Frontend commands are defined in [`aux_share/package.json`](./aux_share/package.json):

```powershell
npm run dev       # Start Vite development server
npm run build     # Create a production build
npm run preview   # Preview the production build
```

The backend has small executable checks in several modules, for example:

```powershell
cd backend
python platform_detector.py
python universal_converter.py
```

These checks may call external services and require valid credentials/network
access.

## Current limitations

- Redis must be reachable for session storage and lookup. Its connection is
  configured with `REDIS_HOST`, `REDIS_PORT`, and `REDIS_DB`; session lookup
  rate limiting fails open while Redis is unavailable.
- Sessions use high-entropy, URL-safe codes and expire after 24 hours. Legacy
  four-digit codes remain readable until their deprecation window ends.
- Apple Music playlist extraction is not available through the free integration.
- YouTube Music playlist extraction depends on the current `ytmusicapi`
  response format and public playlist availability.
- Spotify export currently supports Spotify as the target platform only.
- The default share URL is generated for local development
  (`http://localhost:5173`); deployments need a configured public frontend URL.
- Docker Compose uses Nginx to proxy frontend `/api` requests to the backend;
  direct API access remains available on the published backend port.
- There is no automated test suite in the repository yet.

## Project layout

```text
AuxShare/
├── docker-compose.yml         # Frontend, backend, and Redis orchestration
├── .env.example               # Container/deployment configuration template
├── aux_share/                 # Vue 3 + Vite frontend
│   ├── Dockerfile             # Production frontend image
│   ├── nginx.conf             # SPA fallback and API reverse proxy
│   ├── src/components/        # Input, results, player, sharing, export UI
│   ├── src/services/          # Axios API client
│   ├── src/stores/            # Pinia state
│   ├── src/views/             # Home, join, and OAuth callback pages
│   └── package.json
├── backend/                   # FastAPI service
│   ├── Dockerfile             # Backend image
│   ├── main.py                # API routes and request models
│   ├── universal_converter.py # Cross-platform conversion pipeline
│   ├── session_manager.py     # Redis session persistence
│   ├── platform_detector.py   # URL detection/platform registry
│   ├── platforms/             # Platform adapters
│   └── requirements.txt
└── README.md
```

## License

No license file is currently included in the repository. Add one before
redistributing the project.
