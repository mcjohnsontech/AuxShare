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
      <span>Export to Spotify</span>
    </div>
  </button>
  
  <p v-if="statusMessage" :class="['status-msg', statusType]">
    {{ statusMessage }}
  </p>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { Loader2 } from 'lucide-vue-next'
import { API_BASE_URL } from '@/services/api'

const props = defineProps({
  sessionCode: {
    type: String,
    required: true
  }
})

const isExporting = ref(false)
const statusMessage = ref('')
const statusType = ref('info')
const pendingExportKey = 'spotify_pending_export_session'

async function initiateLogin() {
  localStorage.setItem('auth_return_path', window.location.pathname)
  localStorage.setItem(pendingExportKey, props.sessionCode)
  statusMessage.value = "Connecting to Spotify..."
  statusType.value = "info"
  try {
    // Start the OAuth flow on the backend origin. The state is bound to a
    // cookie, and the browser must hold that cookie when Spotify redirects
    // back to the backend, so login cannot be initiated from this origin.
    const cfgRes = await fetch(`${API_BASE_URL}/api/config`)
    const cfg = await cfgRes.json().catch(() => ({}))
    const startUrl = cfg.auth_start_url || `${API_BASE_URL}/api/auth/start`
    window.location.href = startUrl
  } catch (e) {
    console.error(e)
    localStorage.removeItem(pendingExportKey)
    statusMessage.value = "Failed to start Spotify login"
    statusType.value = "error"
  }
}

async function handleExport() {
  // Purge any legacy token from localStorage
  localStorage.removeItem('spotify_access_token')
  
  isExporting.value = true
  statusMessage.value = "Creating your playlist..."
  statusType.value = "info"
  
  try {
    const res = await fetch(`${API_BASE_URL}/api/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        session_code: props.sessionCode,
        target_platform: 'spotify'
      })
    })
    
    if (res.status === 401) {
      // Not authenticated or token expired - initiate PKCE OAuth flow
      statusMessage.value = "Connecting to Spotify..."
      statusType.value = "info"
      await initiateLogin()
      return
    }
    
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
      throw new Error(errData.detail || "Export failed")
    }
    
    const data = await res.json()
    statusMessage.value = `Created! ${data.tracks_added} tracks added.`
    statusType.value = "success"
    localStorage.removeItem(pendingExportKey)
    
    // Open the new playlist
    if (data.playlist_url) {
      window.open(data.playlist_url, '_blank')
    }
    
  } catch (e) {
    console.error(e)
    statusMessage.value = e.message || "Failed to create playlist."
    statusType.value = "error"
  } finally {
    isExporting.value = false
  }
}

onMounted(() => {
  if (localStorage.getItem(pendingExportKey) === props.sessionCode) {
    void handleExport()
  }
})
</script>

<style scoped>
.export-button {
  background: #1DB954; /* Spotify Brand Color */
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 50px;
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
