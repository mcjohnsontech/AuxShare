<template>
  <div class="home">
    <AppHeader tagline="Good music travels">
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
            <p class="eyebrow"><span class="eyebrow-tick" aria-hidden="true"></span>FOR THE PEOPLE YOU SEND MUSIC TO</p>
            <h1 id="hero-heading" class="hero-title">
              Your playlist.<br />
              <span>Their platform.</span>
            </h1>
            <p class="hero-lede">
              You found the perfect mix. They use a different music app.
              Turn your Spotify or YouTube Music playlist into a link
              they can enjoy on their platform.
            </p>

            <PlaylistBridge />
          </section>

          <div id="converter" class="form-column">
            <PlaylistInput ref="playlistInput" @converted="handleConverted" />
            <p class="form-footnote">
              <Info :size="13" aria-hidden="true" />
              Large playlists can take up to a minute. Keep this tab open while it runs.
            </p>
          </div>
        </div>

        <section v-show="mode === 'convert'" id="how-it-works" class="how-it-works" aria-labelledby="how-heading">
          <div class="section-intro"><p class="eyebrow">LESS FRICTION. MORE MUSIC.</p><h2 id="how-heading">A good playlist deserves<br />good company.</h2><p>No rebuilding it song by song. No “I don’t use that app.”</p></div>
          <ol class="how-steps">
            <li><span class="how-number">01</span><Link2 :size="24" aria-hidden="true" /><h3>Bring your playlist.</h3><p>Copy a public Spotify or YouTube Music playlist link. Paste it above.</p></li>
            <li><span class="how-number">02</span><ListChecks :size="24" aria-hidden="true" /><h3>Find their version.</h3><p>Choose their music app. Review the matches so you know what made the move.</p></li>
            <li><span class="how-number">03</span><Share2 :size="24" aria-hidden="true" /><h3>Send a little feeling.</h3><p>Share one link. They open the mix on their device, with no AuxShare account needed.</p></li>
          </ol>
          <div class="supported-services"><span>Good taste. More places.</span><span><PlatformMark platform="spotify" size="sm" />Spotify</span><span><PlatformMark platform="apple_music" size="sm" />Apple Music</span><span><PlatformMark platform="youtube_music" size="sm" />YouTube Music</span></div>
        </section>

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
      <p>AuxShare · Share the music. Keep the mix.</p>
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
  CheckCircle2,
  Headphones,
  Info,
  ListChecks,
  LockKeyhole,
  Link2,
  Plus,
  Share2,
} from 'lucide-vue-next'
import AppHeader from '@/components/AppHeader.vue'
import PlaylistBridge from '@/components/PlaylistBridge.vue'
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
  background: var(--bg);
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
  padding: clamp(32px, 5vw, 68px) var(--page-gutter) 48px;
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
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
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
  font-size: clamp(3rem, 5.6vw, 4.7rem);
  font-weight: 850;
  line-height: 1.02;
  letter-spacing: var(--tracking-display);
}

.hero-title span {
  color: var(--brand);
}

.hero-lede {
  max-width: 44ch;
  margin-top: var(--space-4);
  color: var(--text-muted);
  font-size: 17px;
  line-height: 1.7;
}

.form-column {
  position: relative;
  padding-top: 8px;
  scroll-margin-top: 24px;
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
  font-size: clamp(2.25rem, 4vw, 3.5rem);
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
    max-width: 620px;
    margin: 0 auto;
  }

  .hero-lede {
    max-width: 48ch;
  }
}

@media (max-width: 900px) {
  .hero-title {
    font-size: clamp(3rem, 8vw, 4.7rem);
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

/* The same bold, warm visual language as the sharing card. */
.how-it-works { margin-top: 100px; padding-top: 56px; border-top: 1px solid var(--border); scroll-margin-top: 32px; }
.section-intro { text-align: center; }
.section-intro h2 { margin-top: 14px; font-size: clamp(2rem, 4vw, 3.3rem); font-weight: 850; letter-spacing: -.06em; }
.section-intro > p:last-child { margin-top: 16px; color: var(--text-muted); font-size: 15px; }
.how-steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 32px; list-style: none; padding: 0; margin: 44px 0 0; }
.how-steps li { position: relative; padding: 24px 0; border-top: 2px solid var(--text); }
.how-steps svg { color: var(--brand); }
.how-number { position: absolute; top: 22px; right: 0; color: #a19b93; font-size: 13px; }
.how-steps h3 { margin-top: 22px; font-size: 20px; font-weight: 750; }
.how-steps p { margin-top: 10px; color: var(--text-muted); font-size: 14px; line-height: 1.7; max-width: 33ch; }
.supported-services { display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 28px; margin-top: 32px; padding: 26px 0; border-top: 1px solid var(--border); }
.supported-services > span { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; }
.supported-services > span:first-child { color: var(--text-faint); font-size: 12px; font-weight: 450; }
@media (max-width: 720px) { .how-it-works { margin-top: 60px; padding-top: 40px; }.how-steps { grid-template-columns: 1fr; gap: 8px; margin-top: 30px; }.how-steps li { padding: 22px 0; }.how-steps h3 { margin-top: 14px; }.how-steps p { max-width: 48ch; }.supported-services { gap: 16px; }.supported-services > span:first-child { flex-basis: 100%; justify-content: center; } }

@media (max-width: 360px) { .hero-title { font-size: 2.55rem; } }
</style>
