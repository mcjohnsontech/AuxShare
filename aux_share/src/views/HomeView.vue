<template>
  <div class="home">
    <div class="container">
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
          <ChevronUp v-if="showDetails" class="icon" />
          <ChevronDown v-else class="icon" />
          {{ showDetails ? 'Hide Details' : 'Show Details' }}
        </button>
      </div>
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
import { ChevronDown, ChevronUp } from 'lucide-vue-next'

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
  background-color: var(--mantine-color-dark-7);
  padding: 40px 20px;
}

.container {
  max-width: 900px;
  margin: 0 auto;
}

.results-container {
  max-width: 800px;
  margin: 40px auto 0;
}

.toggle-details {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 24px auto;
  padding: 10px 20px;
  background: var(--mantine-color-dark-6);
  color: var(--mantine-color-grape-9);
  border: 1px solid var(--mantine-color-grape-9);
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-details:hover {
  background: rgba(134, 46, 156, 0.1);
}

.icon {
  width: 16px;
  height: 16px;
}
</style>