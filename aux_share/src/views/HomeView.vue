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
      
      <!-- We'll add TrackList later when we have the tracks -->
    </div>
  </div>
</template>

<script setup>
import { usePlaylistStore } from '@/stores/playlist'
import PlaylistInput from '@/components/PlaylistInput.vue'
import ShareLink from '@/components/ShareLink.vue'
import MatchStats from '@/components/MatchStats.vue'

const playlistStore = usePlaylistStore()

function handleConverted() {
  console.log('Playlist converted successfully!')
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
</style>