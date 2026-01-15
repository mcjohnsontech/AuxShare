<template>
  <button 
    class="export-button" 
    @click="handleExport"
    :disabled="isExporting"
  >
    <div v-if="isExporting" class="content">
      <Loader2 class="icon spin" />
      <span>Creating Playlist...</span>
    </div>
    <div v-else class="content">
      <!-- <img src="@/assets/spotify-icon-white.png" class="icon-img" v-if="hasIcon" /> -->
      <span>Export to Spotify</span>
    </div>
  </button>
  
  <p v-if="statusMessage" :class="['status-msg', statusType]">
    {{ statusMessage }}
  </p>
</template>

<script setup>
import { ref } from 'vue'
import { Loader2 } from 'lucide-vue-next'
import { usePlaylistStore } from '@/stores/playlist'

const props = defineProps({
  sessionCode: {
    type: String,
    required: true
  }
})

const playlistStore = usePlaylistStore()
const isExporting = ref(false)
const statusMessage = ref('')
const statusType = ref('info')
const hasIcon = ref(false) // Placeholder until we verify asset

async function handleExport() {
  const token = localStorage.getItem('spotify_access_token')
  
  if (!token) {
    // Start Auth Flow
    // Save current path to return to
    localStorage.setItem('auth_return_path', window.location.pathname)
    
    // Get Auth URL from backend
    try {
      const res = await fetch('http://localhost:8000/api/auth/login')
      const data = await res.json()
      window.location.href = data.url
    } catch (e) {
      console.error(e)
      statusMessage.value = "Failed to start login"
      statusType.value = "error"
    }
    return
  }
  
  // Have token, try export
  isExporting.value = true
  statusMessage.value = "Creating your playlist..."
  statusType.value = "info"
  
  try {
    const res = await fetch('http://localhost:8000/api/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_code: props.sessionCode,
        target_platform: 'spotify',
        access_token: token
      })
    })
    
    if (!res.ok) {
      if (res.status === 401) {
        // Token expired? Clear and retry (simple recursive logic or just ask user)
        localStorage.removeItem('spotify_access_token')
        statusMessage.value = "Session expired. Please click again to re-login."
        statusType.value = "error"
        isExporting.value = false
        return
      }
      throw new Error("Export failed")
    }
    
    const data = await res.json()
    statusMessage.value = `✅ Created! ${data.tracks_added} tracks added.`
    statusType.value = "success"
    
    // Open the new playlist
    window.open(data.playlist_url, '_blank')
    
  } catch (e) {
    console.error(e)
    statusMessage.value = "Failed to create playlist."
    statusType.value = "error"
  } finally {
    isExporting.value = false
  }
}
</script>

<style scoped>
.export-button {
  background: #1DB954; /* Spotify Brand Color */
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 50px; /* Pill shape */
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s;
  box-shadow: 0 4px 15px rgba(29, 185, 84, 0.4);
  display: inline-block;
  margin-top: 10px;
}

.export-button:hover:not(:disabled) {
  background: #1ed760;
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 6px 20px rgba(29, 185, 84, 0.6);
}

.export-button:disabled {
  opacity: 0.7;
  cursor: wait;
}

.content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.icon {
  width: 20px;
  height: 20px;
}

.icon-img {
    width: 24px;
    height: 24px;
    object-fit: contain;
}

.spin {
  animation: spin 1s linear infinite;
}

.status-msg {
  margin-top: 10px;
  font-size: 0.9rem;
  font-weight: 500;
}

.status-msg.error { color: #ff6b6b; }
.status-msg.success { color: #1DB954; }
.status-msg.info { color: var(--mantine-color-gray-5); }

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
