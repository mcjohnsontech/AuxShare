<template>
  <div class="home">
    <AppHeader tagline="Playlist converter">
      <span class="header-note">
        <LockKeyhole :size="13" aria-hidden="true" />
        No login required
      </span>
    </AppHeader>

    <main id="main" class="page">
      <div class="page-inner">
        <div v-if="authError" class="auth-banner" role="alert">
          <AlertCircle :size="17" aria-hidden="true" />
          <p>{{ authError }}</p>
          <button type="button" class="auth-dismiss" @click="dismissAuthError">Dismiss</button>
        </div>

        <!-- ---------------------------------------------------------- -->
        <!-- Conversion                                                 -->
        <!-- ---------------------------------------------------------- -->
        <div v-show="mode === 'convert'" class="convert-layout">
          <section class="hero" aria-labelledby="hero-heading">
            <p class="eyebrow"><span class="eyebrow-tick" aria-hidden="true"></span>Playlist converter</p>
            <h1 id="hero-heading" class="hero-title">
              Move a playlist.<br />
              <span>Keep the mix.</span>
            </h1>
            <p class="hero-lede">
              Bring a Spotify or YouTube Music playlist to another service in seconds.
              Review what matched, then share one link that opens instantly — with in-page
              playback where the destination allows it.
            </p>

            <ul class="proof">
              <li>
                <span class="proof-icon" aria-hidden="true"><ListChecks :size="17" /></span>
                <span class="proof-copy">
                  <strong>See every match</strong>
                  <span>All converted tracks are shown up front, with confidence and direct links.</span>
                </span>
              </li>
              <li>
                <span class="proof-icon" aria-hidden="true"><Share2 :size="17" /></span>
                <span class="proof-copy">
                  <strong>One link, no account</strong>
                  <span>Send the playlist to friends. They open it on any device — no sign-up.</span>
                </span>
              </li>
              <li>
                <span class="proof-icon" aria-hidden="true"><AudioLines :size="17" /></span>
                <span class="proof-copy">
                  <strong>Play where it can</strong>
                  <span>Apple Music previews and YouTube playback get a queue that advances automatically. Spotify tracks open in Spotify.</span>
                </span>
              </li>
            </ul>

            <div class="source-line">
              <span class="source-label">Sources</span>
              <span class="source-platform"><PlatformMark platform="spotify" size="sm" />Spotify</span>
              <span class="source-platform"><PlatformMark platform="youtube_music" size="sm" />YouTube Music</span>
            </div>
            <div class="source-line is-destinations">
              <span class="source-label">Destinations</span>
              <span class="source-platform"><PlatformMark platform="spotify" size="sm" />Spotify</span>
              <span class="source-platform"><PlatformMark platform="apple_music" size="sm" />Apple Music</span>
              <span class="source-platform"><PlatformMark platform="youtube_music" size="sm" />YouTube Music</span>
            </div>
          </section>

          <div class="form-column">
            <PlaylistInput ref="playlistInput" @converted="handleConverted" />
            <p class="form-footnote">
              <Info :size="13" aria-hidden="true" />
              Large playlists can take up to a minute. Keep this tab open while it runs.
            </p>
          </div>
        </div>

        <!-- ---------------------------------------------------------- -->
        <!-- Results                                                     -->
        <!-- ---------------------------------------------------------- -->
        <div v-if="mode === 'results'" class="results">
          <div class="results-head">
            <div class="results-title">
              <p class="eyebrow is-success">
                <CheckCircle2 :size="14" aria-hidden="true" />
                Conversion complete
              </p>
              <h1 ref="resultsHeading" tabindex="-1">Your playlist is ready.</h1>
              <p class="results-sub">
                <span class="route">
                  <PlatformMark :platform="playlistStore.sourcePlatform" size="sm" />
                  {{ sourceName }}
                  <ArrowRight :size="13" aria-hidden="true" />
                  <PlatformMark :platform="playlistStore.targetPlatform" size="sm" />
                  {{ targetName }}
                </span>
                <span class="dot" aria-hidden="true">·</span>
                <span class="tabular">{{ pluralize(trackCount, 'track') }}</span>
              </p>
            </div>

            <div class="results-actions">
              <RouterLink
                v-if="playlistStore.sessionCode"
                class="button secondary"
                :to="`/join/${playlistStore.sessionCode}`"
              >
                <Headphones :size="16" aria-hidden="true" />
                Listener view
              </RouterLink>
              <button type="button" class="button ghost" @click="startAnother">
                <Plus :size="16" aria-hidden="true" />
                New conversion
              </button>
            </div>
          </div>

          <div class="summary-grid">
            <ShareLink
              v-if="playlistStore.sessionCode"
              :code="playlistStore.sessionCode"
              :share-url="playlistStore.shareUrl"
            />
            <MatchStats :stats="playlistStore.stats" />
          </div>

          <ExportButton
            v-if="isSpotifyTarget && playlistStore.sessionCode"
            :session-code="playlistStore.sessionCode"
          />

          <div v-if="playlistStore.tracksError" class="tracks-error" role="alert">
            <AlertTriangle :size="18" aria-hidden="true" />
            <div class="tracks-error-copy">
              <p class="tracks-error-title">The track list could not be loaded</p>
              <p class="tracks-error-text">{{ playlistStore.tracksError }}</p>
            </div>
            <button type="button" class="button secondary" @click="retryTracks">Retry</button>
          </div>

          <div v-else-if="playlistStore.tracksLoading" class="skeleton-card">
            <p class="skeleton-title">Loading the converted tracks…</p>
            <TrackListSkeleton :rows="6" />
          </div>

          <TrackList
            v-else-if="playlistStore.targetPlatform"
            :tracks="playlistStore.tracks"
            :target-platform="playlistStore.targetPlatform"
          />
        </div>
      </div>
    </main>

    <footer class="site-footer">
      <p>AuxShare · Move playlists between services without losing the mix.</p>
      <p>Shared links expire after 24 hours.</p>
    </footer>
  </div>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  AudioLines,
  CheckCircle2,
  Headphones,
  Info,
  ListChecks,
  LockKeyhole,
  Plus,
  Share2,
} from 'lucide-vue-next'
import AppHeader from '@/components/AppHeader.vue'
import PlaylistInput from '@/components/PlaylistInput.vue'
import ShareLink from '@/components/ShareLink.vue'
import MatchStats from '@/components/MatchStats.vue'
import ExportButton from '@/components/ExportButton.vue'
import TrackList from '@/components/TrackList.vue'
import TrackListSkeleton from '@/components/TrackListSkeleton.vue'
import PlatformMark from '@/components/PlatformMark.vue'
import { usePlaylistStore } from '@/stores/playlist'
import { getPlatform } from '@/lib/platforms'
import { pluralize } from '@/lib/format'

const playlistStore = usePlaylistStore()
const route = useRoute()
const router = useRouter()

const mode = ref('convert')
const resultsHeading = ref(null)
const playlistInput = ref(null)

const sourceName = computed(() => getPlatform(playlistStore.sourcePlatform).name)
const targetName = computed(() => getPlatform(playlistStore.targetPlatform).name)
const trackCount = computed(() => playlistStore.tracks.length || playlistStore.stats?.total || 0)
const isSpotifyTarget = computed(() => getPlatform(playlistStore.targetPlatform).key === 'spotify')

const authError = computed(() => {
  const raw = route.query.auth_error
  if (!raw) return ''
  const known = {
    handoff_failed: 'Spotify sign-in could not be completed. Please try connecting again.',
    access_denied: 'Spotify sign-in was cancelled. You can try again whenever you are ready.',
    invalid_state: 'The Spotify sign-in request expired or was invalid. Please try again.',
  }
  return known[raw] || 'Spotify sign-in could not be completed. Please try again.'
})

function dismissAuthError() {
  const query = { ...route.query }
  delete query.auth_error
  router.replace({ path: route.path, query })
}

function prefersReducedMotion() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
}

async function handleConverted() {
  mode.value = 'results'

  await nextTick()
  resultsHeading.value?.focus()
  window.scrollTo({ top: 0, behavior: prefersReducedMotion() ? 'auto' : 'smooth' })

  if (playlistStore.sessionCode && playlistStore.tracks.length === 0) {
    try {
      await playlistStore.loadTracks(playlistStore.sessionCode)
    } catch {
      // Rendered by the tracks-error state; the share link still works.
    }
  }
}

async function retryTracks() {
  if (!playlistStore.sessionCode) return
  try {
    await playlistStore.loadTracks(playlistStore.sessionCode)
  } catch {
    /* stays in the error state */
  }
}

async function startAnother() {
  playlistStore.reset()
  mode.value = 'convert'

  await nextTick()
  playlistInput.value?.focusUrl()
  window.scrollTo({ top: 0, behavior: prefersReducedMotion() ? 'auto' : 'smooth' })
}
</script>

<style scoped>
.home {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(1100px 420px at 18% -180px, rgba(47, 107, 255, 0.1), transparent 70%),
    var(--bg);
}

.header-note {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  background: var(--surface);
  color: var(--text-muted);
  font-size: var(--text-2xs);
  font-weight: var(--weight-medium);
}

.page {
  flex: 1 0 auto;
}

.page-inner {
  max-width: var(--container);
  margin: 0 auto;
  padding: clamp(20px, 4vw, 44px) var(--page-gutter) clamp(32px, 5vw, 64px);
}

.auth-banner {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: var(--space-4);
  padding: 10px 14px;
  border: 1px solid var(--danger-border);
  border-radius: var(--radius-sm);
  background: var(--danger-bg);
  color: var(--danger-strong);
  font-size: var(--text-sm);
}

.auth-banner p {
  flex: 1 1 auto;
}

.auth-banner svg {
  flex: 0 0 auto;
}

.auth-dismiss {
  flex: 0 0 auto;
  padding: 3px 6px;
  border: 0;
  border-radius: var(--radius-xs);
  background: transparent;
  color: inherit;
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-decoration: underline;
}

.auth-dismiss:focus-visible {
  outline: 2px solid var(--danger);
  outline-offset: 2px;
}

/* ---- Conversion layout -------------------------------------------- */

.convert-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(380px, 430px);
  align-items: start;
  gap: clamp(28px, 5vw, 72px);
  padding-top: clamp(4px, 2vw, 24px);
}

.hero {
  padding-top: var(--space-2);
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

.eyebrow-tick {
  width: 18px;
  height: 2px;
  border-radius: 2px;
  background: var(--blue-500);
}

.hero-title {
  margin-top: var(--space-3);
  color: var(--text);
  font-size: var(--text-3xl);
  line-height: 1.03;
  letter-spacing: var(--tracking-display);
}

.hero-title span {
  color: var(--blue-600);
}

.hero-lede {
  max-width: 44ch;
  margin-top: var(--space-4);
  color: var(--text-muted);
  font-size: var(--text-md);
  line-height: 1.6;
}

.proof {
  display: grid;
  gap: var(--space-3);
  max-width: 48ch;
  margin: var(--space-6) 0 0;
  padding: 0;
  list-style: none;
}

.proof li {
  display: flex;
  align-items: flex-start;
  gap: 11px;
}

.proof-icon {
  display: grid;
  place-items: center;
  flex: 0 0 34px;
  height: 34px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--blue-700);
  box-shadow: var(--shadow-subtle);
}

.proof-copy {
  display: block;
  min-width: 0;
}

.proof-copy strong {
  display: block;
  color: var(--text);
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
}

.proof-copy span {
  display: block;
  margin-top: 1px;
  color: var(--text-muted);
  font-size: var(--text-xs);
  line-height: 1.45;
}

.source-line {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-top: var(--space-6);
  padding-top: var(--space-4);
  border-top: 1px solid var(--border);
  color: var(--text-faint);
  font-size: var(--text-2xs);
}

.source-line.is-destinations {
  margin-top: 8px;
  padding-top: 0;
  border-top: 0;
}

.source-label {
  font-weight: var(--weight-semibold);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
}

.source-platform {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
}

.form-column {
  position: relative;
}

.form-footnote {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: var(--space-3);
  color: var(--text-faint);
  font-size: var(--text-2xs);
  line-height: 1.5;
}

.form-footnote svg {
  flex: 0 0 auto;
  margin-top: 1px;
}

/* ---- Results ------------------------------------------------------- */

.results {
  max-width: 940px;
  margin: 0 auto;
  display: grid;
  gap: var(--space-4);
  animation: results-in var(--dur-3) var(--ease-out);
}

@keyframes results-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

.results-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-5);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border);
}

.eyebrow.is-success {
  color: var(--success);
}

.eyebrow.is-success svg {
  flex: 0 0 auto;
}

.results-title h1 {
  margin-top: 5px;
  font-size: clamp(1.6rem, 1.2rem + 1.6vw, 2.35rem);
  letter-spacing: var(--tracking-display);
}

.results-title h1:focus {
  outline: none;
}

.results-sub {
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

.results-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  padding-top: 4px;
}

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-height: 38px;
  padding: 0 13px;
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

.button.secondary {
  border-color: var(--blue-600);
  background: var(--blue-600);
  color: #fff;
}

.button.secondary:hover {
  background: var(--blue-700);
  border-color: var(--blue-700);
}

.button.ghost {
  background: transparent;
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

.skeleton-card {
  padding: var(--space-4);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow-xs);
}

.skeleton-title {
  margin-bottom: var(--space-2);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--divider);
  color: var(--text-faint);
  font-size: var(--text-2xs);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
}

.tracks-error {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--danger-border);
  border-radius: var(--radius-lg);
  background: var(--danger-bg);
  color: var(--danger-strong);
}

.tracks-error > svg {
  flex: 0 0 auto;
}

.tracks-error-copy {
  flex: 1 1 auto;
  min-width: 0;
}

.tracks-error-title {
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
}

.tracks-error-text {
  margin-top: 1px;
  font-size: var(--text-xs);
}

.site-footer {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--space-2);
  max-width: var(--container);
  width: 100%;
  margin: 0 auto;
  padding: var(--space-5) var(--page-gutter) var(--space-6);
  border-top: 1px solid var(--border);
  color: var(--text-faint);
  font-size: var(--text-2xs);
}

.site-footer p {
  margin: 0;
}

@media (max-width: 1020px) {
  .convert-layout {
    grid-template-columns: minmax(0, 1fr);
    gap: var(--space-5);
    max-width: 700px;
    margin: 0 auto;
  }

  .hero-lede {
    max-width: 60ch;
  }
}

@media (max-width: 900px) {
  .proof,
  .source-line {
    display: none;
  }

  .hero-title {
    font-size: clamp(1.85rem, 1.3rem + 3vw, 2.6rem);
  }
}

@media (max-width: 880px) {
  .summary-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 720px) {
  .results-head {
    flex-direction: column;
    gap: var(--space-3);
  }

  .results-actions {
    width: 100%;
  }

  .results-actions .button {
    flex: 1 1 auto;
  }

  .site-footer {
    flex-direction: column;
  }
}

@media (max-width: 520px) {
  .page-inner {
    padding-top: var(--space-4);
  }

  .header-note {
    display: none;
  }

  .hero-lede {
    font-size: var(--text-base);
  }

  .tracks-error {
    flex-wrap: wrap;
  }
}
</style>
