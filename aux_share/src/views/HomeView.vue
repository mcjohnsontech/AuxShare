<!-- src/views/HomeView.vue -->

<template>
  <div class="home">
    <PlaylistInput @converted="handleConverted" />
    
    <div v-if="playlistStore.sessionCode" class="results-container">
      <ShareLink 
        :code="playlistStore.sessionCode"
        :share-url="playlistStore.shareUrl"
      />
      
      <MatchStats :stats="playlistStore.stats" />
      
      <!-- Show detailed matching stats for the creator -->
      <TrackList 
        v-if="showDetails"
        :tracks="sessionTracks"
        :target-platform="playlistStore.targetPlatform || 'youtube_music'"
      />
      
      <button @click="showDetails = !showDetails" class="toggle-details">
        {{ showDetails ? '🔼 Hide Details' : '🔽 Show Details' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { usePlaylistStore } from '@/stores/playlist'
import PlaylistInput from '@/components/PlaylistInput.vue'
import ShareLink from '@/components/ShareLink.vue'
import MatchStats from '@/components/MatchStats.vue'
import TrackList from '@/components/TrackList.vue'

const playlistStore = usePlaylistStore()
const showDetails = ref(false)

// Need to fetch tracks when showing details
const sessionTracks = computed(() => {
  // If we have tracks in store, use them
  if (playlistStore.tracks.length > 0) {
    return playlistStore.tracks
  }
  
  // Otherwise, we'll need to fetch them
  // For now, return empty array
  return []
})

async function handleConverted() {
  console.log('Playlist converted successfully!')
  showDetails.value = true // Auto-show details after conversion
  
  // Fetch the session to get tracks
  if (playlistStore.sessionCode) {
    try {
      await playlistStore.loadSession(playlistStore.sessionCode)
    } catch (err) {
      console.error('Failed to load session details:', err)
    }
  }
}
</script>

<style scoped>
.home {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px 20px;
}

.results-container {
  max-width: 800px;
  margin: 40px auto 0;
}

.toggle-details {
  display: block;
  margin: 20px auto;
  padding: 12px 24px;
  background: white;
  color: #667eea;
  border: 2px solid white;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.toggle-details:hover {
  background: transparent;
  color: white;
}
</style>