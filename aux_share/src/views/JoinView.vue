<template>
  <div class="join-view">
    <div class="container">
      <div v-if="loading" class="loading-state">
        <Loader2 class="spinner-icon" />
        <p>Loading playlist...</p>
      </div>
      
      <div v-else-if="error" class="error-card">
        <AlertCircle class="error-icon" />
        <h2>Session Not Found</h2>
        <p>{{ error }}</p>
        <router-link to="/" class="home-button">
          Create New Session
        </router-link>
      </div>
      
      <div v-else class="content-wrapper">
        <h1 class="title">
          <Radio class="title-icon" />
          Join Playlist Session
        </h1>
        
        <div v-if="playlistStore.hasResults" class="results">
          <!-- Show source platform -->
          <div class="stats-summary">
            <p>
              Playlist converted from 
              <strong>{{ playlistStore.sourcePlatform || 'another platform' }}</strong>
            </p>
          </div>

          <!-- Helper Actions -->
          <div class="actions-bar" v-if="playlistStore.targetPlatform === 'spotify'">
             <ExportButton :session-code="route.params.code" />
          </div>

          <!-- Use PlayableTrackList with CORRECT platform -->
          <PlayableTrackList 
            v-if="playlistStore.targetPlatform"
            :tracks="playlistStore.tracks"
            :target-platform="playlistStore.targetPlatform"
            @play-all="startQueue(0)"
            @play-track="startQueue"
          />
          
          <!-- Debug: Show if platform is missing -->
          <div v-else class="error-card small">
            <AlertTriangle class="error-icon small" />
            <div class="error-text">
                <h3>Target platform not found!</h3>
                <p>This session is missing platform information.</p>
            </div>
          </div>
        </div>
      </div>
    
      <!-- Queue Player Overlay -->
      <QueuePlayer
        :is-open="isPlayerOpen"
        :tracks="playlistStore.tracks"
        :initial-index="currentTrackIndex"
        :platform="playlistStore.targetPlatform"
        @close="closePlayer"
        @next-track="onTrackChange"
        @prev-track="onTrackChange"
      />
    </div>
  </div>
</template>

<script setup>
import { onMounted, computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { usePlaylistStore } from '@/stores/playlist'
import PlayableTrackList from '@/components/PlayableTrackList.vue'
import QueuePlayer from '@/components/QueuePlayer.vue'
import ExportButton from '@/components/ExportButton.vue'
import { Loader2, AlertCircle, Radio, AlertTriangle } from 'lucide-vue-next'

const route = useRoute()
const playlistStore = usePlaylistStore()

const loading = computed(() => playlistStore.loading)
const error = computed(() => playlistStore.error)

// Player State
const isPlayerOpen = ref(false)
const currentTrackIndex = ref(0)

function startQueue(index = 0) {
  currentTrackIndex.value = index
  isPlayerOpen.value = true
}

function closePlayer() {
  isPlayerOpen.value = false
}

function onTrackChange(index) {
  currentTrackIndex.value = index
}

onMounted(async () => {
  const code = route.params.code
  
  if (code) {
    try {
      await playlistStore.loadSession(code)
    } catch (err) {
      console.error('Failed to load session:', err)
    }
  }
})
</script>

<style scoped>
.join-view {
  min-height: 100vh;
  /* Dark textured background */
  background-color: var(--mantine-color-dark-7);
  padding: 40px 20px;
}

.container {
  max-width: 900px;
  margin: 0 auto;
}

.title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 2.5rem;
  color: var(--mantine-color-gray-0);
  margin-bottom: 30px;
}

.title-icon {
  width: 40px;
  height: 40px;
  color: var(--mantine-color-grape-9);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: var(--mantine-color-gray-5);
}

.spinner-icon {
  width: 48px;
  height: 48px;
  color: var(--mantine-color-grape-7);
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-card {
  background: var(--mantine-color-dark-6);
  padding: 40px;
  border-radius: 8px;
  text-align: center;
  border: 1px solid #ff6b6b;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.error-card.small {
  flex-direction: row;
  padding: 24px;
  gap: 16px;
  border-color: #fab005; /* Warning color */
}

.error-icon {
  width: 48px;
  height: 48px;
  color: #ff6b6b; /* Red */
  margin-bottom: 16px;
}

.error-icon.small {
    width: 24px;
    height: 24px;
    color: #fab005;
    margin-bottom: 0;
}

.error-text {
    text-align: left;
}

.error-text h3 {
    margin: 0;
    color: #fab005;
}

.error h2 {
  color: #ff6b6b;
  margin-bottom: 15px;
}

.error p {
  color: var(--mantine-color-gray-5);
  margin-bottom: 25px;
}

.home-button {
  display: inline-block;
  padding: 12px 24px;
  background: var(--mantine-color-grape-9);
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-weight: 600;
  transition: background-color 0.2s;
}

.home-button:hover {
  background: var(--mantine-color-grape-7);
}

.results {
  margin-top: 20px;
}

.stats-summary {
  background: rgba(134, 46, 156, 0.1);
  color: var(--mantine-color-gray-0);
  padding: 16px;
  border-radius: 8px;
  text-align: center;
  margin-bottom: 24px;
  border: 1px solid rgba(134, 46, 156, 0.2);
}

.stats-summary p {
  margin: 0;
  font-size: 1.1rem;
}

.stats-summary strong {
  color: var(--mantine-color-grape-7);
}

.actions-bar {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}
</style>