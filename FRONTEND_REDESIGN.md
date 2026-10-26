# AuxShare frontend redesign — working notes

## Audit (what was actually wrong)

**Styling was not "a bit inconsistent" — it was partly undefined.**
`JoinView`, `PlayableTrackList`, `QueuePlayer` and the export status text used
`--mantine-color-*` custom properties, but Mantine is not a dependency and no
Mantine CSS is imported. Those declarations resolve to invalid values, so the
"now playing" title rendered dark-on-dark over the overlay and the shared page
had no theme at all. `assets/base.css` (Vue scaffold, dark-mode override) was
never imported. Two different brands were shown: "AuxParty" in the header/hero
and "AuxShare" in the page title.

**Results were hidden by design.**
`HomeView` kept tracks behind `showDetails` (false by default) even though
`handleConverted()` force-opened it. Worse, `convertPlaylist()` never populates
`tracks`; a second `loadSession()` request did, and it flipped the global
`loading` flag back on. Results also sat below a full-height centred hero,
two large cards and a toggle, so they were below the fold.

**Links were fake or missing.**
`PlayableTrackList` fabricated `music.apple.com/us/song/{id}` and
`music.youtube.com/watch?v=…&list=RD…` URLs from ids (and a "playlist" link
that was really one track). `TrackList` showed no links at all, even though the
backend supplies `${target}_url`. The share URL was a readonly input.

**The player could not advance.**
YouTube was a plain `<iframe>`; no `enablejsapi` listener or IFrame API was
used, so the `ended` event was never observed. `isPlaying` was set to `true`
before calling `play()` and never rolled back on failure. Apple previews
advanced only if `preview_url` existed. Progress was a hardcoded `0:30` bar,
`formatTime()` produced broken labels past 59 s, the queue included unplayable
rows, and there was no Escape/focus handling, no close label, no queue list.

**Other concrete issues.** "Debug: Show if platform is missing" in the UI;
badges with the word "Needs attention" and colour-only meaning; emoji platform
icons; a missing `/placeholder-art.png`; no loading skeleton; duplicate
`components/HomeView.vue`; unused scaffold (`HelloWorld`, `TheWelcome`,
`WelcomeItem`, `icons/`, `ui/`, `ReviewQueue.jsx`); share-link copy depended on
`document.execCommand`; export auto-opened a popup after a network response;
export never said "connect Spotify" before the redirect.

## Design direction

Keep the existing blue identity, but make it a system: a soft off-white canvas,
white working surfaces with a single hairline border, deep-ink "stage" surfaces
for sharing and playback, strong display type, tabular numerals for stats, and
one restrained motion language. The signature motif is a small equaliser
("track ticks") used in the mark, the conversion progress panel and the active
queue row — meaningful, not decorative.

Information architecture: **home = convert & review, shared page = listen &
share**. Home is a two-state view (conversion form → results) rather than a
disclosure toggle. Results lead with a success line, share actions and compact
stats; the track list follows immediately, filterable, with real links.

Platform identity is expressed with colour + name + monogram (no emoji, no
invented logos). Only backend-supplied `${platform}_url` values become links —
URLs are never manufactured in the client.

Playback: YouTube uses the official IFrame Player API so `ENDED` is observed
and the same embedded provider advances; Apple Music uses the 30-second
`preview_url` with the native `<audio>` `ended` event. Where autoplay is
blocked, the UI says so and offers an explicit control. The queue contains only
playable tracks, the index is owned by the view (so closing/reopening does not
reset it), and last-track/end-of-queue is an explicit state.

## What was implemented

- **Design system.** `src/styles/tokens.css` defines the palette, type scale,
  spacing, radii, elevation, motion and control sizes. `src/assets/main.css`
  owns the global reset, focus language, skip link, reduced-motion override and
  shared utility classes. The old scaffold stylesheet and logo were removed.
- **Shell and shared UI.** `App.vue` now provides the skip link and route view.
  `AppHeader`, `PlatformMark`, `TrackRow`, `TrackListSkeleton` and the
  `AppHeader`/platform primitives replace the duplicated and emoji-based UI.
- **Home (`/`).** `views/HomeView.vue` is a two-state convert → results view.
  `PlaylistInput` validates and classifies Spotify/YouTube Music URLs, disables
  the form while converting, shows staged progress, and renders errors next to
  the form. Results include the share card, stats, filters, all tracks and the
  Spotify export panel. Copy explicitly separates **sources** (Spotify and
  YouTube Music) from **destinations** (Spotify, Apple Music and YouTube Music);
  Apple Music is not advertised as a source because the backend does not support
  it.
- **Shared page (`/join/:code`).** `views/JoinView.vue` loads the session,
  shows the route and match/playability counts, and exposes the queue only when
  the destination supports in-page playback. `PlayableTrackList` marks playable
  rows, explains unmatched/unplayable rows, and changes its heading to “Open the
  playlist” when the service does not allow in-page listening. Partial queues
  use a precise “Play 4 of 6” label instead of claiming “Play all”.
- **Player.** `QueuePlayer.vue` implements the Apple `<audio>` and YouTube
  IFrame API paths, queue selection, previous/next, `ENDED` auto-advance with a
  duplicate guard, replay at the end, progress, autoplay/permission notices,
  focus trap, Escape close, scroll lock and focus restoration. `lib/youtube.js`
  lazily loads the official API and reports timeout/error states.
- **Sharing and export.** `ShareLink.vue` exposes a real absolute URL, opens it
  safely, copies with the Clipboard API plus a legacy fallback, and announces
  success/failure. `ExportButton.vue` preserves the existing authenticated
  Spotify export contract, OAuth handoff, pending-export recovery, idempotency
  handling and explicit connect/retry/success states.
- **Data and links.** `lib/platforms.js` is the single source for platform
  names, colours, notes, URL classification and `${platform}_url` validation.
  The client never synthesizes a provider URL. `stores/playlist.js` makes the
  convert → load-session flow explicit and separates conversion loading from
  track loading.
- **Honesty fixes.** Removed “plays right in the browser” as an unqualified
  promise; the copy now says playback is available where the destination allows
  it. Corrected “works with Apple Music” to distinguish sources from
  destinations. Spotify pages say “open in Spotify”, not “listen here”.
  YouTube target copy says playback requires embedding to be allowed. Shared
  links say “open”, not “listen”. Unmatched and unplayable rows never get
  fabricated links or enabled play controls.
- **Cleanup.** Removed the duplicate `src/components/HomeView.vue`,
  `ReviewQueue.jsx`, the Vue scaffold components, old `ui/`/`icons/`, unused
  `base.css`/`logo.svg`, debug `defineExpose`, unused `cx()` helper and other
  dead references.

## Verification

Verified against the built frontend served by Docker at
`http://localhost:5173`, using mocked API responses at the CDP network layer.
Date: 2026-10-26.

| Check | Command / method | Result |
| --- | --- | --- |
| Production build | `npm run build` in `aux_share/` | Pass; `index-Bw2Q6Poz.js` and `index-D82y8q2p.css` produced |
| Docker serve | `docker compose up -d --build frontend` | Pass; page and assets returned HTTP 200 |
| Accessibility | `node axe-run.mjs` (axe-core 4.10.2, WCAG A/AA) | **0 violations across 13 states** |
| Journeys | `node flow.mjs` (CDP, mocked API) | **122/122 checks pass** |
| Desktop results | 1440px snapshot | No horizontal overflow; 6 rows |
| Narrow/tablet results | 320px and 768px snapshots | No horizontal overflow; all rows inside viewport |
| Mobile results | 390px snapshot | No horizontal overflow; rows and touch targets fit |
| Home widths | 320/768/1024/1440px | No horizontal overflow; heading fits |
| Skip link | Keyboard Tab from page load | Link becomes visible, focuses, and points to `#main` |
| Reduced motion | Emulated `prefers-reduced-motion: reduce` | Animations/transitions reduced to 0.01ms; iteration count 1 |
| Apple player | Real `<audio>` fixture | Playback, pause/resume, next/previous, end auto-advance, last-track replay, queue sync and focus restoration pass |
| YouTube player | Mocked session, real player container | Dialog, iframe/notice, provider note, index advance pass; actual media/ENDED is not environment-testable |
| Export states | Mocked authenticated/unauth/error/pending | Connect, retry, already-exported and pending-resume states pass |

The axe states were: home convert, home results, join Apple playlist, desktop
player, mobile player, Spotify/export prompt, expired link, storage unavailable,
empty playlist, conversion error, converting/loading, auth error banner and
export failure.

The 12 console errors recorded by the journey harness are deliberate mocked
failures (422 conversion, refused network, 500 export, 404/503 sessions, etc.);
no unexpected application errors were observed. The accessibility and journey
harnesses live outside the repository under
`C:\Users\HomePC\AppData\Local\Temp\opencode\` and are not part of the commit.

## Limitations and dependencies

- **Live providers were not exercised.** Conversion, sessions and export used
  deterministic mocked responses; no live Spotify/YouTube Music credentials were
  used. The real OAuth redirect and Spotify playlist creation still require the
  backend/Spotify configuration.
- **YouTube playback cannot be fully verified here.** The player uses the
  official IFrame API and handles errors/notices, but actual video playback and
  `ENDED` depend on region, embedding permissions, cookies and the network.
- **Apple previews depend on Apple.** Tracks without a valid `preview_url` are
  correctly shown as unplayable rather than linked to a synthesized URL.
- **Autoplay policy.** Browsers may block audio/video after a track ends or on a
  new page load. The UI reports the block and provides an explicit play control;
  it cannot override browser policy.
- **Visual review.** Layout, overflow, focus, computed styles and bounds were
  checked programmatically; screenshots were not visually inspected by the
  implementation model.
- **Repository checks.** There are no lint, unit-test or type-check scripts in
  this frontend; `npm run build` is the available build-quality gate. No
  dependencies or backend files were changed. All changes are currently
  uncommitted on `frontend-redesign`.

