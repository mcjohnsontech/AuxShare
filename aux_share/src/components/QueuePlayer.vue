<template>
  <div
    v-show="isOpen"
    class="player-overlay"
    :aria-hidden="!isOpen"
    @click.self="close"
  >
    <div
      ref="dialog"
      class="player"
      role="dialog"
      aria-modal="true"
      aria-labelledby="player-title"
      @keydown="onKeydown"
    >
      <header class="player-top">
        <div class="top-meta">
          <span class="state-dot" :class="`is-${playbackState}`" aria-hidden="true"></span>
          <span class="top-eyebrow">Now playing</span>
          <span v-if="tracks.length" class="top-count tabular">
            {{ currentIndex + 1 }} / {{ tracks.length }}
          </span>
        </div>
        <button
          ref="closeButton"
          type="button"
          class="close-button"
          aria-label="Close the player"
          @click="close"
        >
          <X :size="18" aria-hidden="true" />
        </button>
      </header>

      <div class="player-body">
        <div class="media">
          <div v-if="isYouTube" class="yt-frame">
            <div ref="ytHost" class="yt-host"></div>
          </div>

          <div v-else class="art-frame">
            <img
              v-if="artworkUrl && !artworkFailed"
              :src="artworkUrl"
              alt=""
              class="artwork"
              @error="artworkFailed = true"
            />
            <div v-else class="artwork artwork-fallback" aria-hidden="true">
              <Music4 :size="42" />
            </div>
            <span v-if="isApple" class="preview-tag">30-second preview</span>
          </div>
        </div>

        <div class="info">
          <p class="kicker">
            <PlatformMark :platform="platform.key" size="sm" />
            <span>{{ platform.name }}</span>
          </p>

          <h2 id="player-title" class="now-title">{{ title }}</h2>
          <p class="now-artist">
            {{ artist }}<template v-if="album"> · {{ album }}</template>
          </p>

          <a
            v-if="currentUrl"
            class="open-link"
            :href="currentUrl"
            target="_blank"
            rel="noopener noreferrer"
          >
            Open on {{ platform.name }}
            <ExternalLink :size="13" aria-hidden="true" />
          </a>

          <div class="progress-wrap">
            <div
              class="progress-track"
              role="progressbar"
              aria-label="Playback progress"
              :aria-valuemin="0"
              :aria-valuemax="100"
              :aria-valuenow="Math.round(progressPercent)"
              :aria-valuetext="`${formatSeconds(currentTime)} of ${duration ? formatSeconds(duration) : 'unknown length'}`"
            >
              <span class="progress-fill" :style="{ width: `${progressPercent}%` }"></span>
            </div>
            <div class="progress-times tabular">
              <span>{{ formatSeconds(currentTime) }}</span>
              <span>{{ duration ? formatSeconds(duration) : '—:—' }}</span>
            </div>
          </div>

          <div class="controls">
            <button
              type="button"
              class="control-button"
              :disabled="!hasPrev"
              aria-label="Previous track"
              @click="prev"
            >
              <SkipBack :size="19" aria-hidden="true" />
            </button>

            <button
              type="button"
              class="control-button primary"
              :aria-label="toggleLabel"
              @click="togglePlay"
            >
              <Loader2 v-if="playbackState === 'loading'" :size="22" class="spin" aria-hidden="true" />
              <Pause v-else-if="isPlaying" :size="22" aria-hidden="true" />
              <RotateCcw v-else-if="playbackState === 'ended'" :size="20" aria-hidden="true" />
              <Play v-else :size="22" class="play-glyph" aria-hidden="true" />
            </button>

            <button
              type="button"
              class="control-button"
              :disabled="!hasNext"
              aria-label="Next track"
              @click="next"
            >
              <SkipForward :size="19" aria-hidden="true" />
            </button>
          </div>

          <p v-if="playbackState === 'error'" class="notice is-error" role="alert">
            <AlertCircle :size="15" aria-hidden="true" />
            <span>{{ errorMessage }}</span>
            <button v-if="hasNext" type="button" class="notice-action" @click="next">Skip</button>
          </p>

          <p v-else-if="autoplayBlocked && !isPlaying" class="notice" role="status">
            <Info :size="15" aria-hidden="true" />
            <span>If playback did not start, your browser may have blocked autoplay. Press play to continue.</span>
          </p>

          <p v-else-if="playbackState === 'ended' && !hasNext" class="notice" role="status">
            <CheckCircle2 :size="15" aria-hidden="true" />
            <span>That was the last track in the queue.</span>
            <button type="button" class="notice-action" @click="replayQueue">Play again</button>
          </p>

          <p class="provider-note">{{ platform.playbackNote }}</p>
        </div>

        <div v-if="tracks.length > 1" class="queue-panel">
          <div class="queue-head">
            <h3>Queue</h3>
            <span>{{ tracks.length }} tracks</span>
          </div>
          <ol class="queue-list">
            <li v-for="(track, index) in tracks" :key="`${queueKey(track, index)}-${index}`">
              <button
                type="button"
                class="queue-row"
                :class="{ 'is-current': index === currentIndex }"
                :aria-current="index === currentIndex ? 'true' : undefined"
                :aria-label="`Play ${track.title || 'track'}${track.artist ? ` by ${track.artist}` : ''}`"
                @click="selectTrack(index)"
              >
                <span class="queue-index tabular" aria-hidden="true">
                  <span v-if="index === currentIndex" class="eq-bars" :class="{ 'is-paused': !isPlaying }">
                    <span></span><span></span><span></span><span></span>
                  </span>
                  <template v-else>{{ index + 1 }}</template>
                </span>
                <span class="queue-copy">
                  <span class="queue-title">{{ track.title || 'Untitled track' }}</span>
                  <span class="queue-artist">{{ track.artist || 'Unknown artist' }}</span>
                </span>
              </button>
            </li>
          </ol>
        </div>
      </div>

      <p class="sr-only" aria-live="polite">{{ liveMessage }}</p>

      <audio
        v-if="isApple"
        ref="audioEl"
        :src="previewUrl"
        preload="metadata"
        @play="onAudioPlay"
        @pause="onAudioPause"
        @ended="handleEnded"
        @loadedmetadata="syncAudioTime"
        @timeupdate="syncAudioTime"
        @error="onAudioError"
      ></audio>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import {
  AlertCircle,
  CheckCircle2,
  ExternalLink,
  Info,
  Loader2,
  Music4,
  Pause,
  Play,
  RotateCcw,
  SkipBack,
  SkipForward,
  X,
} from 'lucide-vue-next'
import PlatformMark from './PlatformMark.vue'
import { canPlayTrack, getPlatform, trackKey, trackUrl } from '@/lib/platforms'
import { formatSeconds } from '@/lib/format'
import { loadYouTubeIframeApi } from '@/lib/youtube'

const props = defineProps({
  tracks: {
    type: Array,
    required: true,
  },
  initialIndex: {
    type: Number,
    default: 0,
  },
  platform: {
    type: String,
    required: true,
  },
  isOpen: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'track-change', 'playing-change'])

const dialog = ref(null)
const closeButton = ref(null)
const ytHost = ref(null)
const audioEl = ref(null)

const platform = computed(() => getPlatform(props.platform))
const isYouTube = computed(() => platform.value.key === 'youtube_music')
const isApple = computed(() => platform.value.key === 'apple_music')

const currentIndex = ref(clampIndex(props.initialIndex))
const playbackState = ref('idle') // idle | loading | playing | paused | ended | error
const errorMessage = ref('')
const autoplayBlocked = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const artworkFailed = ref(false)

let ytPlayer = null
let ytReady = false
let ytInitializing = false
let ytCreatedVideoId = null
let pendingVideoId = null
let shouldAutoplay = true
let endedHandledForIndex = -1
let progressTimer = null
let autoplayTimer = null
let lastFocusedElement = null
let previousBodyOverflow = ''
let openToken = 0
let lastLoadedKey = ''

const currentTrack = computed(() => props.tracks[currentIndex.value] || null)
const title = computed(() => currentTrack.value?.title || 'Nothing queued')
const artist = computed(
  () => currentTrack.value?.artist || currentTrack.value?.artists?.join(', ') || 'Unknown artist',
)
const album = computed(() => currentTrack.value?.album || '')
const previewUrl = computed(() => currentTrack.value?.preview_url || '')
const currentUrl = computed(() =>
  currentTrack.value ? trackUrl(currentTrack.value, props.platform) : null,
)
const artworkUrl = computed(() => {
  const candidate =
    currentTrack.value?.artwork_url ||
    currentTrack.value?.album_art ||
    currentTrack.value?.image_url ||
    ''
  return typeof candidate === 'string' && /^https?:\/\//i.test(candidate) ? candidate : ''
})

const hasPrev = computed(() => currentIndex.value > 0)
const hasNext = computed(() => currentIndex.value < props.tracks.length - 1)
const isPlaying = computed(() => playbackState.value === 'playing')
const progressPercent = computed(() => {
  if (!duration.value || duration.value <= 0) return 0
  return Math.min(100, Math.max(0, (currentTime.value / duration.value) * 100))
})

const toggleLabel = computed(() => {
  if (playbackState.value === 'loading') return 'Playback is loading'
  if (isPlaying.value) return `Pause ${title.value}`
  if (playbackState.value === 'ended') return `Replay ${title.value}`
  return `Play ${title.value}`
})

const liveMessage = computed(() => {
  if (!props.isOpen || !currentTrack.value) return ''
  return `Now playing ${title.value} by ${artist.value}. Track ${currentIndex.value + 1} of ${props.tracks.length}.`
})

watch(
  () => props.initialIndex,
  (value) => {
    const next = clampIndex(value)
    if (next === currentIndex.value) return
    currentIndex.value = next
    if (props.isOpen) {
      void loadCurrent({ autoplay: true })
    }
  },
)

watch(
  () => props.tracks.length,
  () => {
    const next = clampIndex(currentIndex.value)
    if (next !== currentIndex.value) currentIndex.value = next
  },
)

watch(
  () => props.isOpen,
  async (open) => {
    if (open) {
      await onOpen()
    } else {
      onClose()
    }
  },
  { immediate: true },
)

watch(currentTrack, () => {
  artworkFailed.value = false
})

async function onOpen() {
  openToken += 1
  const token = openToken
  lastFocusedElement = document.activeElement

  previousBodyOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'

  await nextTick()
  closeButton.value?.focus()
  startProgressLoop()

  const key = currentKey()
  const resumable =
    key &&
    key === lastLoadedKey &&
    (playbackState.value === 'paused' || playbackState.value === 'ended')

  if (resumable) {
    await resumeCurrent()
  } else {
    await loadCurrent({ autoplay: true })
  }

  if (token !== openToken || !props.isOpen) {
    pause()
  }
}

function onClose() {
  pause()
  stopProgressLoop()
  clearAutoplayTimer()
  document.body.style.overflow = previousBodyOverflow
  const target = lastFocusedElement
  lastFocusedElement = null
  nextTick(() => {
    if (target && typeof target.focus === 'function' && document.contains(target)) {
      target.focus()
    }
  })
}

function clampIndex(value) {
  if (!props.tracks.length) return 0
  const index = Number.isFinite(value) ? Math.trunc(value) : 0
  return Math.min(Math.max(index, 0), props.tracks.length - 1)
}

function currentKey() {
  return currentTrack.value ? trackKey(currentTrack.value, props.platform) : ''
}

async function loadCurrent({ autoplay = true } = {}) {
  clearAutoplayTimer()
  currentTime.value = 0
  duration.value = 0
  errorMessage.value = ''
  autoplayBlocked.value = false
  endedHandledForIndex = -1
  shouldAutoplay = autoplay

  if (!currentTrack.value) {
    playbackState.value = 'idle'
    return
  }

  lastLoadedKey = currentKey()
  playbackState.value = 'loading'

  if (!canPlayTrack(currentTrack.value, props.platform)) {
    playbackState.value = 'error'
    errorMessage.value = `No playable media was supplied for this track. Open it on ${platform.value.name} instead.`
    emitPlaying(false)
    return
  }

  if (isYouTube.value) {
    await setupYouTube({ autoplay })
    return
  }

  if (isApple.value) {
    await nextTick()
    const audio = audioEl.value
    if (!audio) {
      playbackState.value = 'error'
      errorMessage.value = 'The audio preview element is unavailable in this browser.'
      return
    }
    audio.currentTime = 0
    if (!autoplay) {
      playbackState.value = 'paused'
      return
    }
    try {
      await audio.play()
      playbackState.value = 'playing'
      emitPlaying(true)
    } catch (error) {
      if (error?.name === 'NotAllowedError') {
        autoplayBlocked.value = true
        playbackState.value = 'paused'
        emitPlaying(false)
      } else {
        playbackState.value = 'error'
        errorMessage.value =
          'This preview could not be played. It may have expired — open the track on Apple Music or skip.'
        emitPlaying(false)
      }
    }
    return
  }

  playbackState.value = 'error'
  errorMessage.value = `${platform.value.name} playback is not available in the browser. Open the track in ${platform.value.name}.`
  emitPlaying(false)
}

async function setupYouTube({ autoplay }) {
  const videoId = currentTrack.value?.youtube_music_id
  if (!videoId) {
    playbackState.value = 'error'
    errorMessage.value = 'This track has no YouTube video id, so it cannot be played here.'
    return
  }

  if (!ytHost.value) {
    playbackState.value = 'error'
    errorMessage.value = 'The embedded player could not start. Close the player and try again.'
    return
  }

  if (ytPlayer) {
    if (!ytReady) {
      pendingVideoId = videoId
      return
    }
    pendingVideoId = null
    if (autoplay) {
      ytPlayer.loadVideoById({ videoId })
    } else {
      ytPlayer.cueVideoById({ videoId })
    }
    armAutoplayWatchdog()
    return
  }

  if (ytInitializing) {
    pendingVideoId = videoId
    return
  }
  ytInitializing = true

  try {
    await loadYouTubeIframeApi()
  } catch (error) {
    playbackState.value = 'error'
    errorMessage.value = error.message
    return
  } finally {
    ytInitializing = false
  }

  pendingVideoId = videoId
  const mount = document.createElement('div')
  mount.className = 'yt-mount'
  ytHost.value.replaceChildren(mount)

  ytPlayer = new window.YT.Player(mount, {
    width: '100%',
    height: '100%',
    videoId,
    playerVars: {
      autoplay: autoplay ? 1 : 0,
      playsinline: 1,
      rel: 0,
      origin: window.location.origin,
    },
    events: {
      onReady: (event) => {
        ytReady = true
        ytCreatedVideoId = videoId
        const frame = event.target.getIframe?.()
        if (frame) {
          frame.setAttribute(
            'allow',
            'autoplay; encrypted-media; picture-in-picture; fullscreen',
          )
          frame.setAttribute('title', 'YouTube player')
        }
        syncYouTubeTime()
        if (pendingVideoId && pendingVideoId !== ytCreatedVideoId) {
          ytCreatedVideoId = pendingVideoId
          event.target.loadVideoById({ videoId: pendingVideoId })
        } else if (shouldAutoplay) {
          event.target.playVideo()
        }
        armAutoplayWatchdog()
      },
      onStateChange: (event) => {
        handleYouTubeState(event.data)
      },
      onError: (event) => {
        handleYouTubeError(event.data)
      },
    },
  })
}

function handleYouTubeState(state) {
  if (!props.isOpen) return
  switch (state) {
    case 1: // playing
      playbackState.value = 'playing'
      autoplayBlocked.value = false
      clearAutoplayTimer()
      emitPlaying(true)
      syncYouTubeTime()
      break
    case 2: // paused
      if (playbackState.value !== 'ended' && playbackState.value !== 'error') {
        playbackState.value = 'paused'
        emitPlaying(false)
      }
      break
    case 3: // buffering
      if (playbackState.value !== 'ended' && playbackState.value !== 'error') {
        playbackState.value = 'loading'
        emitPlaying(false)
      }
      break
    case 0: // ended
      playbackState.value = 'ended'
      emitPlaying(false)
      handleEnded()
      break
    default:
      break
  }
}

function handleYouTubeError(code) {
  const messages = {
    2: 'YouTube rejected this video id. Skip to the next track or open it on YouTube Music.',
    5: 'This video could not be played in the browser. Skip to the next track or open it on YouTube Music.',
    100: 'This video is no longer available on YouTube. Skip to the next track.',
    101: 'The rights holder does not allow this video to be embedded. Open it on YouTube Music or skip.',
    150: 'The rights holder does not allow this video to be embedded. Open it on YouTube Music or skip.',
  }
  playbackState.value = 'error'
  errorMessage.value = messages[code] || 'The YouTube player reported an error. Try the next track.'
  emitPlaying(false)
}

function emitPlaying(value) {
  emit('playing-change', value)
}

function pause() {
  if (isYouTube.value && ytPlayer && ytReady) {
    try {
      ytPlayer.pauseVideo()
    } catch {
      /* player already disposed */
    }
  } else if (isApple.value && audioEl.value) {
    audioEl.value.pause()
  }
  if (playbackState.value === 'playing') {
    playbackState.value = 'paused'
    emitPlaying(false)
  }
}

async function resumeCurrent() {
  if (!currentTrack.value) return
  if (isYouTube.value && ytPlayer && ytReady) {
    playbackState.value = 'loading'
    ytPlayer.playVideo()
    armAutoplayWatchdog()
    return
  }
  if (isApple.value && audioEl.value) {
    try {
      await audioEl.value.play()
      playbackState.value = 'playing'
      emitPlaying(true)
    } catch (error) {
      autoplayBlocked.value = true
      playbackState.value = 'paused'
      emitPlaying(false)
    }
    return
  }
  await loadCurrent({ autoplay: true })
}

async function togglePlay() {
  if (playbackState.value === 'playing') {
    pause()
    return
  }

  if (playbackState.value === 'ended') {
    await replayCurrent()
    return
  }

  if (isYouTube.value) {
    if (ytPlayer && ytReady) {
      playbackState.value = 'loading'
      ytPlayer.playVideo()
      armAutoplayWatchdog()
    } else {
      await loadCurrent({ autoplay: true })
    }
    return
  }

  if (isApple.value && audioEl.value) {
    try {
      await audioEl.value.play()
      playbackState.value = 'playing'
      autoplayBlocked.value = false
      emitPlaying(true)
    } catch (error) {
      if (error?.name === 'NotAllowedError') {
        autoplayBlocked.value = true
        playbackState.value = 'paused'
      } else {
        playbackState.value = 'error'
        errorMessage.value = 'This preview could not be played. Open the track on Apple Music or skip.'
      }
    }
    return
  }

  await loadCurrent({ autoplay: true })
}

async function replayCurrent() {
  if (!currentTrack.value) return
  endedHandledForIndex = -1
  if (isYouTube.value && ytPlayer && ytReady) {
    playbackState.value = 'loading'
    ytPlayer.seekTo(0, true)
    ytPlayer.playVideo()
    armAutoplayWatchdog()
    return
  }
  if (isApple.value && audioEl.value) {
    audioEl.value.currentTime = 0
    try {
      await audioEl.value.play()
      playbackState.value = 'playing'
      emitPlaying(true)
    } catch {
      playbackState.value = 'paused'
    }
    return
  }
  await loadCurrent({ autoplay: true })
}

function handleEnded() {
  if (endedHandledForIndex === currentIndex.value) return
  endedHandledForIndex = currentIndex.value
  if (hasNext.value) {
    goTo(currentIndex.value + 1, { autoplay: true })
  } else {
    playbackState.value = 'ended'
    emitPlaying(false)
  }
}

function next() {
  if (!hasNext.value) return
  goTo(currentIndex.value + 1, { autoplay: true })
}

function prev() {
  if (!hasPrev.value) {
    void replayCurrent()
    return
  }
  goTo(currentIndex.value - 1, { autoplay: true })
}

function goTo(index, { autoplay = true } = {}) {
  const target = clampIndex(index)
  if (target === currentIndex.value) {
    void replayCurrent()
    return
  }
  currentIndex.value = target
  emit('track-change', target)
  void loadCurrent({ autoplay })
}

function selectTrack(index) {
  if (index === currentIndex.value) {
    void togglePlay()
    return
  }
  goTo(index, { autoplay: true })
}

function replayQueue() {
  if (!props.tracks.length) return
  if (currentIndex.value === 0) {
    void replayCurrent()
    return
  }
  goTo(0, { autoplay: true })
}

function onAudioPlay() {
  playbackState.value = 'playing'
  autoplayBlocked.value = false
  emitPlaying(true)
}

function onAudioPause() {
  if (playbackState.value === 'playing' || playbackState.value === 'loading') {
    playbackState.value = 'paused'
    emitPlaying(false)
  }
}

function onAudioError() {
  if (!props.isOpen) return
  playbackState.value = 'error'
  errorMessage.value =
    'This preview could not be loaded. It may be unavailable in your region — open the track on Apple Music or skip.'
  emitPlaying(false)
}

function syncAudioTime() {
  const audio = audioEl.value
  if (!audio) return
  if (Number.isFinite(audio.currentTime)) currentTime.value = audio.currentTime
  if (Number.isFinite(audio.duration) && audio.duration > 0) duration.value = audio.duration
}

function syncYouTubeTime() {
  if (!ytPlayer || !ytReady) return
  try {
    const time = ytPlayer.getCurrentTime?.()
    const total = ytPlayer.getDuration?.()
    if (Number.isFinite(time) && time >= 0) currentTime.value = time
    if (Number.isFinite(total) && total > 0) duration.value = total
  } catch {
    /* player not ready */
  }
}

function startProgressLoop() {
  stopProgressLoop()
  progressTimer = setInterval(() => {
    if (isYouTube.value) syncYouTubeTime()
    else if (isApple.value) syncAudioTime()
  }, 500)
}

function stopProgressLoop() {
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
}

function armAutoplayWatchdog() {
  clearAutoplayTimer()
  autoplayTimer = setTimeout(() => {
    if (!props.isOpen) return
    if (playbackState.value === 'loading' || playbackState.value === 'paused') {
      autoplayBlocked.value = true
      if (playbackState.value === 'loading') playbackState.value = 'paused'
      emitPlaying(false)
    }
  }, 4000)
}

function clearAutoplayTimer() {
  if (autoplayTimer) {
    clearTimeout(autoplayTimer)
    autoplayTimer = null
  }
}

function close() {
  emit('close')
}

function queueKey(track, index) {
  return trackKey(track, props.platform) || `track-${index}`
}

function onKeydown(event) {
  if (event.key === 'Escape') {
    event.preventDefault()
    close()
    return
  }
  if (event.key !== 'Tab') return

  const focusable = dialog.value?.querySelectorAll(
    'button:not([disabled]), a[href], input:not([disabled]), [tabindex]:not([tabindex="-1"])',
  )
  if (!focusable || focusable.length === 0) return

  const first = focusable[0]
  const last = focusable[focusable.length - 1]

  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

onBeforeUnmount(() => {
  stopProgressLoop()
  clearAutoplayTimer()
  document.body.style.overflow = previousBodyOverflow
  if (ytPlayer) {
    try {
      ytPlayer.destroy()
    } catch {
      /* already gone */
    }
    ytPlayer = null
  }
})

</script>

<style scoped>
.player-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: grid;
  place-items: center;
  padding: clamp(0px, 2vw, 24px);
  background: rgba(4, 8, 20, 0.74);
  backdrop-filter: blur(6px);
  animation: overlay-in var(--dur-2) var(--ease-out);
}

@keyframes overlay-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.player {
  width: min(880px, 100%);
  max-height: min(760px, 94vh);
  overflow: auto;
  border: 1px solid var(--on-ink-line);
  border-radius: var(--radius-xl);
  background: var(--ink);
  color: var(--on-ink);
  box-shadow: var(--shadow-lift);
  animation: player-in var(--dur-2) var(--ease-out);
}

@keyframes player-in {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.995);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

.player-top {
  position: sticky;
  top: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: 12px 18px;
  border-bottom: 1px solid var(--on-ink-line);
  background: var(--ink);
}

.top-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.state-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--on-ink-faint);
}

.state-dot.is-playing {
  background: #45d483;
  box-shadow: 0 0 0 3px rgba(69, 212, 131, 0.16);
}

.state-dot.is-loading {
  background: #ffcf5c;
}

.state-dot.is-error {
  background: #ff7a6e;
}

.top-eyebrow {
  color: var(--on-ink-muted);
  font-size: var(--text-2xs);
  font-weight: var(--weight-bold);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
}

.top-count {
  padding-left: 8px;
  border-left: 1px solid var(--on-ink-line);
  color: var(--on-ink-faint);
  font-size: var(--text-2xs);
  font-variant-numeric: tabular-nums;
}

.close-button {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border: 1px solid var(--on-ink-line);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--on-ink-muted);
  transition:
    background var(--dur-1) var(--ease-out),
    color var(--dur-1) var(--ease-out);
}

.close-button:hover {
  background: var(--ink-3);
  color: var(--on-ink);
}

.close-button:focus-visible {
  outline: 2px solid #9db9ff;
  outline-offset: 2px;
}

.player-body {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
  grid-template-areas:
    'media info'
    'queue queue';
  gap: var(--space-5);
  padding: var(--space-5);
}

.media {
  grid-area: media;
  min-width: 0;
}

.yt-frame {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  border: 1px solid var(--on-ink-line);
  border-radius: var(--radius-md);
  background: #000;
}

.yt-host,
.yt-host :deep(.yt-mount) {
  width: 100%;
  height: 100%;
}

.yt-host :deep(iframe) {
  display: block;
  width: 100%;
  height: 100%;
  border: 0;
}

.art-frame {
  position: relative;
  aspect-ratio: 1 / 1;
  overflow: hidden;
  border: 1px solid var(--on-ink-line);
  border-radius: var(--radius-md);
  background: var(--ink-2);
}

.artwork {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.artwork-fallback {
  display: grid;
  place-items: center;
  color: #fff;
  background: radial-gradient(ellipse at 95% 0%, #ffd7a1, #f7a16a 20%, transparent 60%), linear-gradient(140deg, #91b8ff, #2452ff 70%, #ffa869);
}

.preview-tag {
  position: absolute;
  bottom: 10px;
  left: 10px;
  padding: 3px 8px;
  border-radius: var(--radius-pill);
  background: rgba(4, 8, 20, 0.72);
  color: var(--on-ink-muted);
  font-size: var(--text-2xs);
  font-weight: var(--weight-semibold);
}

.info {
  grid-area: info;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.kicker {
  display: flex;
  align-items: center;
  gap: 7px;
  color: var(--on-ink-muted);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
}

.now-title {
  margin-top: var(--space-2);
  color: var(--on-ink);
  font-size: clamp(1.25rem, 1rem + 1vw, 1.6rem);
  line-height: 1.2;
  letter-spacing: var(--tracking-tight);
  overflow-wrap: anywhere;
}

.now-artist {
  margin-top: 4px;
  color: var(--on-ink-muted);
  font-size: var(--text-sm);
  overflow-wrap: anywhere;
}

.open-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  align-self: flex-start;
  margin-top: 8px;
  padding: 3px 0;
  color: #9db9ff;
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-decoration: none;
}

.open-link:hover {
  text-decoration: underline;
}

.open-link:focus-visible {
  outline: 2px solid #9db9ff;
  outline-offset: 2px;
  border-radius: 2px;
}

.progress-wrap {
  margin-top: auto;
  padding-top: var(--space-4);
}

.progress-track {
  width: 100%;
  height: 6px;
  overflow: hidden;
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.14);
}

.progress-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--blue-400);
  transition: width 250ms linear;
}

.progress-times {
  display: flex;
  justify-content: space-between;
  margin-top: 5px;
  color: var(--on-ink-faint);
  font-size: var(--text-2xs);
  font-variant-numeric: tabular-nums;
}

.controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  padding-top: var(--space-3);
}

.control-button {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border: 1px solid var(--on-ink-line);
  border-radius: 50%;
  background: transparent;
  color: var(--on-ink);
  transition:
    background var(--dur-1) var(--ease-out),
    border-color var(--dur-1) var(--ease-out),
    opacity var(--dur-1) var(--ease-out);
}

.control-button:hover:not(:disabled) {
  background: var(--ink-3);
  border-color: #35456b;
}

.control-button:disabled {
  opacity: 0.35;
}

.control-button:focus-visible {
  outline: 2px solid #9db9ff;
  outline-offset: 2px;
}

.control-button.primary {
  width: 58px;
  height: 58px;
  border-color: var(--blue-500);
  background: var(--blue-500);
  color: #fff;
}

.control-button.primary:hover:not(:disabled) {
  background: var(--blue-400);
  border-color: var(--blue-400);
}

.play-glyph {
  margin-left: 2px;
}

.notice {
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: var(--space-3);
  padding: 8px 10px;
  border: 1px solid var(--on-ink-line);
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.04);
  color: var(--on-ink-muted);
  font-size: var(--text-xs);
}

.notice svg {
  flex: 0 0 auto;
  margin-top: 1px;
}

.notice.is-error {
  border-color: rgba(255, 122, 110, 0.4);
  background: rgba(255, 122, 110, 0.1);
  color: #ffc1bb;
}

.notice-action {
  margin-left: auto;
  padding: 2px 8px;
  border: 1px solid currentColor;
  border-radius: var(--radius-xs);
  background: transparent;
  color: inherit;
  font-size: var(--text-2xs);
  font-weight: var(--weight-semibold);
}

.notice-action:hover {
  background: rgba(255, 255, 255, 0.08);
}

.notice-action:focus-visible {
  outline: 2px solid #9db9ff;
  outline-offset: 2px;
}

.provider-note {
  margin-top: var(--space-3);
  color: var(--on-ink-faint);
  font-size: var(--text-2xs);
  line-height: 1.45;
}

.queue-panel {
  grid-area: queue;
  min-width: 0;
  padding-top: var(--space-4);
  border-top: 1px solid var(--on-ink-line);
}

.queue-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-2);
}

.queue-head h3 {
  color: var(--on-ink);
  font-size: var(--text-sm);
  letter-spacing: 0;
}

.queue-head span {
  color: var(--on-ink-faint);
  font-size: var(--text-2xs);
}

.queue-list {
  display: grid;
  gap: 2px;
  max-height: 210px;
  margin: 0;
  padding: 0;
  overflow: auto;
  list-style: none;
}

.queue-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 7px 8px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--on-ink-muted);
  text-align: left;
  transition:
    background var(--dur-1) var(--ease-out),
    border-color var(--dur-1) var(--ease-out),
    color var(--dur-1) var(--ease-out);
}

.queue-row:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--on-ink);
}

.queue-row.is-current {
  border-color: rgba(36, 82, 255, 0.5);
  background: rgba(36, 82, 255, 0.16);
  color: var(--on-ink);
}

.queue-row:focus-visible {
  outline: 2px solid #9db9ff;
  outline-offset: 2px;
}

.queue-index {
  display: grid;
  place-items: center;
  flex: 0 0 20px;
  color: var(--on-ink-faint);
  font-size: var(--text-2xs);
  font-variant-numeric: tabular-nums;
}

.queue-row.is-current .queue-index {
  color: #9db9ff;
}

.queue-copy {
  display: flex;
  align-items: baseline;
  gap: 8px;
  min-width: 0;
}

.queue-title {
  overflow: hidden;
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.queue-artist {
  overflow: hidden;
  color: var(--on-ink-faint);
  font-size: var(--text-2xs);
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 760px) {
  .player-overlay {
    padding: 0;
    align-items: end;
  }

  .player {
    width: 100%;
    max-height: 94vh;
    border-radius: var(--radius-xl) var(--radius-xl) 0 0;
    border-bottom: 0;
    padding-bottom: env(safe-area-inset-bottom, 0);
  }

  .player-body {
    grid-template-columns: minmax(0, 1fr);
    grid-template-areas:
      'media'
      'info'
      'queue';
    gap: var(--space-4);
    padding: var(--space-4);
  }

  .art-frame {
    aspect-ratio: 16 / 9;
    max-height: 220px;
  }

  .progress-wrap {
    margin-top: var(--space-4);
  }

  .controls {
    gap: var(--space-5);
  }

  .queue-list {
    max-height: 180px;
  }

  .queue-copy {
    flex-direction: column;
    gap: 0;
  }
}

@media (max-width: 420px) {
  .now-title {
    font-size: var(--text-lg);
  }

  .queue-artist {
    display: none;
  }
}
</style>
