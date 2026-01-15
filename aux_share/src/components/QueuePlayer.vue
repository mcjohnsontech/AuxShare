<template>
  <div v-if="isOpen" class="queue-player-overlay">
    <div class="player-container">
      <!-- Header / Close -->
      <div class="player-header">
        <h3>Now Playing</h3>
        <button class="close-button" @click="close">
          <X class="close-icon" />
        </button>
      </div>

      <!-- Main Content -->
      <div class="player-content">
        <!-- Visualization / Embed -->
        <div class="media-display">
          <!-- YouTube Iframe -->
          <div v-if="platform === 'youtube_music'" class="youtube-embed-container">
            <iframe
              width="100%"
              height="100%"
              :src="getYoutubeEmbedUrl(currentTrack)"
              frameborder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowfullscreen
            ></iframe>
          </div>

          <!-- Album Art (for Audio based players) -->
          <div v-else class="album-art-container">
             <img 
               :src="currentTrack.artwork_url || currentTrack.album_art || '/placeholder-art.png'" 
               class="album-art"
               alt="Album Art"
             />
          </div>
        </div>

        <!-- Track Info -->
        <div class="track-details">
          <h2 class="track-title">{{ currentTrack.title }}</h2>
          <p class="track-artist">{{ currentTrack.artist }}</p>
          <p class="track-album" v-if="currentTrack.album">{{ currentTrack.album }}</p>
        </div>

        <!-- Progress (Placeholder for non-embeds) -->
        <div v-if="platform === 'apple_music'" class="progress-container">
           <div class="progress-bar">
             <div class="progress-fill" :style="{ width: progress + '%' }"></div>
           </div>
           <div class="time-labels">
             <span>0:{{ formatTime(currentTime) }}</span>
             <span>0:30</span> 
           </div>
        </div>
        
        <!-- Controls -->
        <div class="controls">
          <button class="control-btn prev" @click="prev" :disabled="!hasPrev">
            <SkipBack class="control-icon" />
          </button>
          
          <button class="control-btn play-pause" @click="togglePlay">
             <Pause v-if="isPlaying" class="play-icon" />
             <Play v-else class="play-icon ml-1" />
          </button>
          
          <button class="control-btn next" @click="next" :disabled="!hasNext">
            <SkipForward class="control-icon" />
          </button>
        </div>
        
        <!-- Platform Note -->
        <div class="player-note">
           <span v-if="platform === 'apple_music'">Playing 30s Preview (Apple Music)</span>
           <span v-if="platform === 'spotify'">Open Spotify to play full track</span>
        </div>

      </div>

      <!-- Hidden Audio Element for Apple Music -->
      <audio 
        v-if="platform === 'apple_music'"
        ref="audioPlayer"
        :src="currentTrack.preview_url"
        @ended="onTrackEnded"
        @timeupdate="onTimeUpdate"
      ></audio>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { X, Play, Pause, SkipBack, SkipForward } from 'lucide-vue-next'

const props = defineProps({
  tracks: {
    type: Array,
    required: true
  },
  initialIndex: {
    type: Number,
    default: 0
  },
  platform: {
    type: String, // 'youtube_music', 'apple_music', 'spotify'
    required: true
  },
  isOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'next-track', 'prev-track'])

const currentIndex = ref(props.initialIndex)
const isPlaying = ref(false)
const audioPlayer = ref(null)
const currentTime = ref(0)
const progress = ref(0)

// Sync internal index with prop if needed, though we manage it internally usually
watch(() => props.initialIndex, (newVal) => {
  currentIndex.value = newVal
  if (props.isOpen) {
    playCurrent()
  }
})

watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    playCurrent()
  } else {
    pause()
  }
})

const currentTrack = computed(() => {
  return props.tracks[currentIndex.value] || {}
})

const hasNext = computed(() => currentIndex.value < props.tracks.length - 1)
const hasPrev = computed(() => currentIndex.value > 0)

function getYoutubeEmbedUrl(track) {
  if (!track || !track.youtube_music_id) return ''
  // Enable autoplay
  return `https://www.youtube.com/embed/${track.youtube_music_id}?autoplay=1&enablejsapi=1`
}

function playCurrent() {
  isPlaying.value = true
  
  if (props.platform === 'apple_music') {
    // Wait for DOM
    setTimeout(() => {
      if (audioPlayer.value) {
        audioPlayer.value.volume = 0.5
        audioPlayer.value.play().catch(e => console.error("Playback failed", e))
      }
    }, 100)
  }
}

function pause() {
  isPlaying.value = false
  if (audioPlayer.value) {
    audioPlayer.value.pause()
  }
}

function togglePlay() {
  if (isPlaying.value) {
    pause()
  } else {
    playCurrent()
  }
}

function next() {
  if (hasNext.value) {
    currentIndex.value++
    playCurrent()
    emit('next-track', currentIndex.value)
  }
}

function prev() {
  if (hasPrev.value) {
    currentIndex.value--
    playCurrent()
    emit('prev-track', currentIndex.value)
  }
}

function close() {
  pause()
  emit('close')
}

// Audio Events
function onTrackEnded() {
  if (hasNext.value) {
    next()
  } else {
    isPlaying.value = false
  }
}

function onTimeUpdate() {
  if (audioPlayer.value) {
    const curr = audioPlayer.value.currentTime
    const dur = audioPlayer.value.duration || 30 // Approx 30s for previews
    currentTime.value = curr
    progress.value = (curr / dur) * 100
  }
}

function formatTime(seconds) {
  const s = Math.floor(seconds)
  return s < 10 ? `0${s}` : s
}

</script>

<style scoped>
.queue-player-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(5px);
  z-index: 1000;
  display: flex;
  justify-content: center;
  align-items: center;
  animation: fadeIn 0.3s ease;
}

.player-container {
  width: 90%;
  max-width: 450px;
  background: var(--mantine-color-dark-6);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 20px 50px rgba(0,0,0,0.5);
  border: 1px solid #373A40;
  display: flex;
  flex-direction: column;
}

.player-header {
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #373A40;
}

.player-header h3 {
  margin: 0;
  color: var(--mantine-color-gray-0);
  font-size: 1rem;
  font-weight: 600;
}

.close-button {
  background: none;
  border: none;
  color: var(--mantine-color-gray-5);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-button:hover {
  color: var(--mantine-color-gray-0);
  background: rgba(255,255,255,0.1);
}

.close-icon {
    width: 20px;
    height: 20px;
}

.player-content {
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.media-display {
  width: 100%;
  aspect-ratio: 16/9; /* Standard video aspect ratio looks better for player */
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 24px;
  position: relative;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.youtube-embed-container {
  width: 100%;
  height: 100%;
}

.album-art-container {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.album-art {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.track-details {
  text-align: center;
  width: 100%;
  margin-bottom: 24px;
}

.track-title {
  color: var(--mantine-color-gray-0);
  margin: 0 0 4px 0;
  font-size: 1.25rem;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-artist {
  color: var(--mantine-color-gray-5);
  margin: 0;
  font-size: 1rem;
}

.track-album {
  color: #5c5f66;
  font-size: 0.875rem;
  margin-top: 4px;
}

.progress-container {
  width: 100%;
  margin-bottom: 24px;
}

.progress-bar {
  width: 100%;
  height: 4px;
  background: #373A40;
  border-radius: 2px;
  margin-bottom: 8px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--mantine-color-grape-9);
  border-radius: 2px;
  transition: width 0.1s linear;
}

.time-labels {
  display: flex;
  justify-content: space-between;
  color: #5c5f66;
  font-size: 0.75rem;
}

.controls {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 16px;
}

.control-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mantine-color-gray-0);
  transition: transform 0.1s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.control-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.control-btn:active:not(:disabled) {
  transform: scale(0.9);
}

.control-icon {
    width: 28px;
    height: 28px;
}

.play-pause {
  width: 56px;
  height: 56px;
  background: var(--mantine-color-grape-9);
  border-radius: 50%;
  color: white;
  box-shadow: 0 4px 12px rgba(134, 46, 156, 0.4);
  transition: all 0.2s;
}

.play-pause:hover {
    background: var(--mantine-color-grape-7);
    transform: scale(1.05);
}

.play-icon {
    width: 24px;
    height: 24px;
    fill: currentColor;
}

.ml-1 {
    margin-left: 2px; /* Visual center adjustment */
}

.player-note {
  font-size: 0.875rem;
  color: #5c5f66;
  margin-top: 8px;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
