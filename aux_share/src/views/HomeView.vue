<template>
  <div class="home">
    <header class="topbar">
      <div class="topbar-inner">
        <div class="topbar-brand"><span class="brand-dot"></span> AuxParty</div>
        <span class="topbar-note">Playlist converter</span>
      </div>
    </header>
    <main class="container">
      <div v-if="authError" class="auth-error" role="alert">
        <span>{{ authError }}</span>
        <button type="button" class="auth-error-dismiss" @click="dismissAuthError">Dismiss</button>
      </div>
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
    </main>
      <footer class="footer">Built for better music sharing <span>•</span> No account required to get started</footer>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlaylistStore } from '@/stores/playlist'
import PlaylistInput from '@/components/PlaylistInput.vue'
import ShareLink from '@/components/ShareLink.vue'
import MatchStats from '@/components/MatchStats.vue'
import TrackList from '@/components/TrackList.vue'
import { ChevronDown, ChevronUp } from 'lucide-vue-next'

const playlistStore = usePlaylistStore()
const showDetails = ref(false)

const route = useRoute()
const router = useRouter()

const authError = computed(() => {
  const raw = route.query.auth_error
  if (!raw) return ''
  if (raw === 'handoff_failed') {
    return 'Spotify sign-in could not be completed. Please try connecting again.'
  }
  return String(raw)
})

function dismissAuthError() {
  const query = { ...route.query }
  delete query.auth_error
  router.replace({ path: route.path, query })
}

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
  background:
    radial-gradient(circle at 50% -10%, var(--blue-100), transparent 35%),
    var(--bg-subtle);
  color: var(--text);
}
.container {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 24px;
}

.auth-error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 20px 0 0;
  padding: 12px 16px;
  border: 1px solid var(--red-200, #fecaca);
  border-radius: var(--radius-sm, 10px);
  background: var(--red-50, #fef2f2);
  color: var(--red-800, #991b1b);
  font-size: 0.9rem;
}

.auth-error-dismiss {
  flex: none;
  border: none;
  background: transparent;
  color: inherit;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  text-decoration: underline;
}
.topbar { border-bottom: 1px solid rgba(220, 229, 245, .8); background: rgba(255,255,255,.75); }
.topbar-inner { display: flex; justify-content: space-between; align-items: center; max-width: 960px; margin: 0 auto; padding: 18px 24px; }
.topbar-brand { display: flex; align-items: center; gap: 9px; color: var(--blue-900); font-size: 15px; font-weight: 700; }
.brand-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--blue-500); box-shadow: 0 0 0 5px var(--blue-100); }
.topbar-note { color: var(--text-faint); font-size: 13px; }
.footer { padding: 0 24px 28px; color: var(--text-faint); font-size: 12px; text-align: center; }
.footer span { padding: 0 5px; color: var(--blue-300); }

.results-container {
  max-width: 800px;
  margin: 0 auto 48px;
}

.toggle-details {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 24px auto;
  padding: 10px 20px;
  background: var(--surface);
  color: var(--blue-700);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-details:hover {
  background: var(--blue-50);
}

@media (max-width: 640px) {
  .container { padding: 0 16px; }
  .topbar-inner { padding: 16px; }
  .topbar-note { display: none; }
}

.icon {
  width: 16px;
  height: 16px;
}
</style>