<!-- src/views/JoinView.vue (UPDATED) -->

<template>
  <div class="join-view">
    <div class="container">
      <h1 class="title">🚗 Join Playlist Session</h1>
      
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Loading playlist...</p>
      </div>
      
      <div v-else-if="error" class="error">
        <h2>❌ Session Not Found</h2>
        <p>{{ error }}</p>
        <router-link to="/" class="home-button">
          Create New Session
        </router-link>
      </div>
      
      <div v-else-if="playlistStore.hasResults" class="results">
        <!-- Show source platform -->
        <div class="stats-summary">
          <p>
            Playlist converted from 
            <strong>{{ playlistStore.sourcePlatform || 'another platform' }}</strong>
          </p>
        </div>

        <!-- Use PlayableTrackList with CORRECT platform -->
        <PlayableTrackList 
          v-if="playlistStore.targetPlatform"
          :tracks="playlistStore.tracks"
          :target-platform="playlistStore.targetPlatform"
        />
        
        <!-- Debug: Show if platform is missing -->
        <div v-else style="background: red; color: white; padding: 20px; border-radius: 12px;">
          <h3>⚠️ Error: Target platform not found!</h3>
          <p>This session is missing platform information.</p>
          <p>Please create a new session.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { usePlaylistStore } from '@/stores/playlist'
import PlayableTrackList from '@/components/PlayableTrackList.vue'

const route = useRoute()
const playlistStore = usePlaylistStore()

const loading = computed(() => playlistStore.loading)
const error = computed(() => playlistStore.error)

onMounted(async () => {
  const code = route.params.code
  
  if (code) {
    try {
      await playlistStore.loadSession(code)
      
      // Debug logging
      console.log('🎵 Session loaded in JoinView')
      console.log('   Tracks:', playlistStore.tracks.length)
      console.log('   Target Platform:', playlistStore.targetPlatform)
      console.log('   Source Platform:', playlistStore.sourcePlatform)
      
      // Log first track structure
      if (playlistStore.tracks.length > 0) {
        console.log('   First track keys:', Object.keys(playlistStore.tracks[0]))
      }
      
    } catch (err) {
      console.error('Failed to load session:', err)
    }
  }
})
</script>


<style scoped>
.join-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px 20px;
}

.container {
  max-width: 900px;
  margin: 0 auto;
}

.title {
  font-size: 3rem;
  color: white;
  text-align: center;
  margin-bottom: 20px;
}

.loading {
  text-align: center;
  color: white;
  padding: 60px 20px;
}

.spinner {
  width: 60px;
  height: 60px;
  border: 5px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error {
  background: white;
  padding: 40px;
  border-radius: 16px;
  text-align: center;
}

.error h2 {
  color: #c33;
  margin-bottom: 15px;
}

.error p {
  color: #666;
  margin-bottom: 25px;
}

.home-button {
  display: inline-block;
  padding: 15px 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-decoration: none;
  border-radius: 12px;
  font-weight: 600;
  transition: transform 0.2s;
}

.home-button:hover {
  transform: translateY(-2px);
}

.results {
  margin-top: 20px;
}

.stats-summary {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  padding: 15px;
  border-radius: 12px;
  text-align: center;
  margin-bottom: 20px;
}

.stats-summary p {
  margin: 0;
  font-size: 1.1rem;
}

.stats-summary strong {
  color: #ffd700;
}
</style>