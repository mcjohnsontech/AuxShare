<template>
  <div class="join">
    <AppHeader tagline="Shared playlist">
      <RouterLink class="header-cta" to="/">
        Create your own
        <ArrowRight :size="13" aria-hidden="true" />
      </RouterLink>
    </AppHeader>

    <main id="main" class="page">
      <div class="page-inner">
        <!-- Loading ---------------------------------------------------- -->
        <div v-if="playlistStore.loading" class="join-loading" aria-busy="true">
          <p class="sr-only" role="status">Loading the shared playlist…</p>
          <div class="skeleton-head" aria-hidden="true">
            <span class="bone bone-eyebrow"></span>
            <span class="bone bone-title"></span>
            <span class="bone bone-sub"></span>
          </div>
          <div class="skeleton-grid" aria-hidden="true">
            <span class="bone bone-panel"></span>
            <span class="bone bone-panel"></span>
          </div>
          <div class="skeleton-card" aria-hidden="true">
            <span class="bone bone-list-title"></span>
            <TrackListSkeleton :rows="7" />
          </div>
        </div>

        <!-- Error ------------------------------------------------------ -->
        <div v-else-if="loadError" class="status-page">
          <div class="status-card">
            <span class="status-icon" aria-hidden="true">
              <Link2Off :size="24" />
            </span>
            <p class="eyebrow">Shared playlist</p>
            <h1>{{ loadError.title }}</h1>
            <p class="status-text">{{ loadError.message }}</p>
            <div class="status-actions">
              <RouterLink class="button primary" to="/">Convert a playlist</RouterLink>
              <button type="button" class="button" @click="retry">Try again</button>
            </div>
          </div>
        </div>

        <!-- Playlist --------------------------------------------------- -->
        <div v-else-if="targetPlatform" class="playlist">
          <header class="playlist-head">
            <div class="playlist-title">
              <p class="eyebrow">
                <span class="live-tick" aria-hidden="true"></span>
                Shared playlist
              </p>
              <h1>{{ headline }}</h1>
              <p class="playlist-sub">
                <span class="route">
                  <PlatformMark :platform="playlistStore.sourcePlatform" size="sm" />
                  {{ sourceName }}
                  <ArrowRight :size="13" aria-hidden="true" />
                  <PlatformMark :platform="targetPlatform" size="sm" />
                  {{ targetName }}
                </span>
                <span class="dot" aria-hidden="true">·</span>
                <span>{{ playbackSubline }}</span>
              </p>
            </div>

            <div v-if="canPlayInApp && playableTracks.length > 0" class="playlist-actions">
              <button
                type="button"
                class="button primary"
                @click="openPlayerAt(0)"
              >
                <Play :size="16" aria-hidden="true" />
                {{ playAllLabel }}
              </button>
            </div>
          </header>

          <div class="summary-grid">
            <ShareLink :code="code" :share-url="playlistStore.shareUrl" />
            <MatchStats :stats="playlistStore.stats" />
          </div>

          <ExportButton
            v-if="isSpotifyTarget"
            :session-code="code"
          />

          <PlayableTrackList
            v-if="playlistStore.tracks.length"
            :tracks="playlistStore.tracks"
            :target-platform="targetPlatform"
            :active-key="activeKey"
            :is-playing="playerOpen && isPlaying"
            @play-track="playTrack"
          />

          <div v-else class="empty-playlist">
            <span class="status-icon is-neutral" aria-hidden="true"><Music2 :size="22" /></span>
            <div>
              <p class="empty-title">This playlist has no tracks</p>
              <p class="empty-text">The session exists, but no tracks were saved with it. Ask the sender to convert it again.</p>
            </div>
          </div>
        </div>

        <div v-else class="status-page">
          <div class="status-card">
            <span class="status-icon" aria-hidden="true"><AlertTriangle :size="24" /></span>
            <h1>This session is incomplete</h1>
            <p class="status-text">The playlist data is missing a destination service, so it cannot be played here.</p>
            <div class="status-actions">
              <RouterLink class="button primary" to="/">Convert a playlist</RouterLink>
            </div>
          </div>
        </div>
      </div>
    </main>

    <footer class="site-footer">
      <p>AuxShare · Share the music. Keep the mix.</p>
      <RouterLink to="/">Convert a playlist</RouterLink>
    </footer>

    <QueuePlayer
      v-if="targetPlatform && playableTracks.length"
      :tracks="playableTracks"
      :initial-index="currentIndex"
      :platform="targetPlatform"
      :is-open="playerOpen"
      @close="playerOpen = false"
      @track-change="onTrackChange"
      @playing-change="isPlaying = $event"
    />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import {
  AlertTriangle,
  ArrowRight,
  Link2Off,
  Music2,
  Play,
} from 'lucide-vue-next'
import AppHeader from '@/components/AppHeader.vue'
import PlatformMark from '@/components/PlatformMark.vue'
import ShareLink from '@/components/ShareLink.vue'
import MatchStats from '@/components/MatchStats.vue'
import ExportButton from '@/components/ExportButton.vue'
import PlayableTrackList from '@/components/PlayableTrackList.vue'
import QueuePlayer from '@/components/QueuePlayer.vue'
import TrackListSkeleton from '@/components/TrackListSkeleton.vue'
import { usePlaylistStore } from '@/stores/playlist'
import { canPlayTrack, getPlatform, trackKey } from '@/lib/platforms'
import { pluralize } from '@/lib/format'

const route = useRoute()
const playlistStore = usePlaylistStore()

const loadError = ref(null)
const playerOpen = ref(false)
const currentIndex = ref(0)
const isPlaying = ref(false)

const code = computed(() => String(route.params.code || ''))
const targetPlatform = computed(() => playlistStore.targetPlatform || '')
const platform = computed(() => getPlatform(targetPlatform.value))
const sourceName = computed(() => getPlatform(playlistStore.sourcePlatform).name)
const targetName = computed(() => platform.value.name)
const canPlayInApp = computed(() => platform.value.canPlayInApp)
const isSpotifyTarget = computed(() => platform.value.key === 'spotify')

const trackCount = computed(
  () => playlistStore.tracks.length || playlistStore.stats?.total || 0,
)

const playableTracks = computed(() =>
  playlistStore.tracks.filter((track) => canPlayTrack(track, targetPlatform.value)),
)

const activeKey = computed(() => {
  const track = playableTracks.value[currentIndex.value]
  return track ? trackKey(track, targetPlatform.value) : ''
})

const headline = computed(() => {
  const count = trackCount.value
  if (count === 0) return 'This playlist is empty.'
  if (platform.value.key === 'spotify') {
    return `${pluralize(count, 'track')}, ready to open in Spotify.`
  }
  if (canPlayInApp.value && playableTracks.value.length === count) {
    return `${pluralize(count, 'track')}, ready to play.`
  }
  return `${pluralize(count, 'track')}, matched and ready.`
})

const playbackSubline = computed(() => {
  if (platform.value.key === 'spotify') {
    return 'Converted and ready to open in Spotify.'
  }
  if (!canPlayInApp.value || playableTracks.value.length === 0) {
    return `Converted and matched. Open any track in ${platform.value.name}.`
  }
  if (playableTracks.value.length < trackCount.value) {
    return `Converted — some tracks open in ${platform.value.name}.`
  }
  return 'Converted and ready to listen.'
})

const playAllLabel = computed(() => {
  const playable = playableTracks.value.length
  if (playable === trackCount.value) return 'Play all'
  return `Play ${playable} of ${trackCount.value}`
})

function describeError(error) {
  const status = error?.response?.status
  const detail = error?.response?.data?.detail

  if (!error?.response) {
    return {
      title: 'We could not reach AuxShare',
      message: 'Check your connection, then try opening this link again.',
    }
  }
  if (status === 404) {
    return {
      title: 'This playlist link has expired',
      message:
        'Shared playlists are kept for 24 hours. Ask the sender for a new link, or convert a playlist yourself in about a minute.',
    }
  }
  if (status === 503) {
    return {
      title: 'Playlists are temporarily unavailable',
      message: 'The server cannot reach playlist storage right now. Please try again in a moment.',
    }
  }
  if (status === 429) {
    return {
      title: 'Too many requests',
      message: 'Give it a moment, then try opening the link again.',
    }
  }
  if (status && status < 500 && typeof detail === 'string' && detail.trim()) {
    return { title: 'This playlist could not be opened', message: detail }
  }
  return {
    title: 'This playlist could not be opened',
    message: 'Something went wrong while loading the session. Please try again.',
  }
}

async function loadSession(sessionCode) {
  loadError.value = null
  playerOpen.value = false
  currentIndex.value = 0
  isPlaying.value = false

  if (!sessionCode) {
    loadError.value = {
      title: 'No playlist code in this link',
      message: 'The link is missing its session code. Ask the sender to copy the full link again.',
    }
    return
  }

  try {
    const data = await playlistStore.loadSession(sessionCode)
    if (!data?.target_platform) {
      loadError.value = {
        title: 'This session is incomplete',
        message: 'The playlist data is missing a destination service. Ask the sender to share a new link.',
      }
    }
  } catch (error) {
    loadError.value = describeError(error)
  }
}

function retry() {
  void loadSession(code.value)
}

function openPlayerAt(index) {
  if (!canPlayInApp.value || playableTracks.value.length === 0) return
  currentIndex.value = Math.min(Math.max(index, 0), playableTracks.value.length - 1)
  playerOpen.value = true
}

function playTrack(track) {
  const index = playableTracks.value.indexOf(track)
  if (index === -1) return
  openPlayerAt(index)
}

function onTrackChange(index) {
  currentIndex.value = index
  isPlaying.value = true
}

watch(
  code,
  (value) => {
    void loadSession(value)
  },
  { immediate: true },
)
</script>

<style scoped>
.join {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg);
}

.header-cta {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: var(--radius-sm);
  color: var(--blue-700);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-decoration: none;
}

.header-cta:hover {
  background: var(--blue-50);
}

.header-cta:focus-visible {
  outline: 2px solid var(--focus-color);
  outline-offset: 2px;
}

.page {
  flex: 1 0 auto;
}

.page-inner {
  max-width: 1060px;
  margin: 0 auto;
  padding: clamp(32px, 5vw, 64px) var(--page-gutter) clamp(32px, 5vw, 56px);
}

/* ---- Playlist header ------------------------------------------------ */

.playlist {
  display: grid;
  gap: var(--space-4);
}

.playlist-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-5);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border);
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--blue-700);
  font-size: var(--text-2xs);
  font-weight: var(--weight-bold);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
}

.live-tick {
  width: 18px;
  height: 2px;
  border-radius: 2px;
  background: var(--blue-500);
}

.playlist-title h1 {
  margin-top: var(--space-2);
  font-size: clamp(2.1rem, 4.5vw, 3.6rem);
  font-weight: 850;
  letter-spacing: var(--tracking-display);
}

.playlist-sub {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: var(--space-2);
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.route {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text);
  font-weight: var(--weight-medium);
}

.route svg {
  color: var(--text-faint);
}

.dot {
  color: var(--text-faint);
}

.playlist-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  padding-top: 4px;
}

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-height: 38px;
  padding: 0 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-decoration: none;
  white-space: nowrap;
  transition:
    background var(--dur-1) var(--ease-out),
    border-color var(--dur-1) var(--ease-out);
}

.button:hover {
  border-color: var(--border-strong);
  background: var(--surface-2);
}

.button.primary {
  border-color: var(--blue-700);
  background: var(--blue-600);
  color: #fff;
}

.button.primary:hover {
  background: var(--blue-700);
  border-color: var(--blue-700);
}

.button:focus-visible {
  outline: 2px solid var(--focus-color);
  outline-offset: 2px;
}

.summary-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.32fr) minmax(0, 1fr);
  align-items: stretch;
  gap: var(--space-3);
}

.status-icon.is-neutral {
  flex: 0 0 44px;
  width: 44px;
  height: 44px;
  margin: 0;
  border-color: var(--border);
  background: var(--surface-2);
  color: var(--text-muted);
}

.empty-playlist {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--surface);
}

.empty-title {
  color: var(--text);
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
}

.empty-text {
  margin-top: 2px;
  color: var(--text-muted);
  font-size: var(--text-xs);
  line-height: 1.5;
}

/* ---- Status pages / loading ---------------------------------------- */

.status-page {
  display: grid;
  place-items: center;
  min-height: 58vh;
}

.status-card {
  width: min(520px, 100%);
  padding: var(--space-6);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow);
  text-align: center;
}

.status-icon {
  display: inline-grid;
  place-items: center;
  width: 52px;
  height: 52px;
  margin-bottom: var(--space-3);
  border: 1px solid var(--warning-border);
  border-radius: var(--radius-md);
  background: var(--warning-bg);
  color: var(--warning-strong);
}

.status-card h1 {
  margin-top: var(--space-2);
  font-size: var(--text-2xl);
  letter-spacing: var(--tracking-tight);
}

.status-text {
  margin-top: var(--space-2);
  color: var(--text-muted);
  font-size: var(--text-sm);
  line-height: 1.6;
}

.status-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-2);
  margin-top: var(--space-4);
}

.join-loading {
  display: grid;
  gap: var(--space-4);
}

.skeleton-head {
  display: grid;
  gap: 9px;
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border);
}

.bone {
  display: block;
  border-radius: var(--radius-pill);
  background: linear-gradient(
    100deg,
    var(--surface-2) 20%,
    var(--surface-3) 40%,
    var(--surface-2) 60%
  );
  background-size: 220% 100%;
  animation: join-shimmer 1.4s var(--ease-in-out) infinite;
}

.bone-eyebrow { width: 120px; height: 10px; }
.bone-title { width: min(460px, 80%); height: 30px; border-radius: var(--radius-sm); }
.bone-sub { width: min(320px, 60%); height: 13px; }

.skeleton-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.32fr) minmax(0, 1fr);
  gap: var(--space-3);
}

.bone-panel {
  height: 130px;
  border-radius: var(--radius-lg);
}

.skeleton-card {
  padding: var(--space-4);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--surface);
}

.bone-list-title {
  width: 160px;
  height: 12px;
  margin-bottom: var(--space-3);
}

@keyframes join-shimmer {
  0% { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}

.site-footer {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--space-2);
  width: 100%;
  max-width: 1060px;
  margin: 0 auto;
  padding: var(--space-5) var(--page-gutter) var(--space-6);
  border-top: 1px solid var(--border);
  color: var(--text-faint);
  font-size: var(--text-2xs);
}

.site-footer p {
  margin: 0;
}

.site-footer a {
  color: var(--text-muted);
}

@media (max-width: 880px) {
  .summary-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .skeleton-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 720px) {
  .playlist-head {
    flex-direction: column;
    gap: var(--space-3);
  }

  .playlist-actions {
    width: 100%;
  }

  .playlist-actions .button {
    flex: 1 1 auto;
  }
}

@media (max-width: 520px) {
  .status-card {
    padding: var(--space-5) var(--space-4);
  }

  .site-footer {
    flex-direction: column;
  }
}
</style>
