<template>
  <section class="export-panel" aria-labelledby="export-heading">
    <div class="export-head">
      <p class="export-eyebrow">
        <PlatformMark platform="spotify" size="sm" />
        <span id="export-heading">Spotify export</span>
      </p>
      <p class="export-desc">
        Save the matched tracks as a new playlist in your own Spotify account.
      </p>
    </div>

    <div class="export-actions">
      <a
        v-if="exported && playlistUrl"
        class="open-playlist"
        :href="playlistUrl"
        target="_blank"
        rel="noopener noreferrer"
      >
        <ExternalLink :size="16" aria-hidden="true" />
        Open playlist<span v-if="playlistTrackCount" class="count"> · {{ playlistTrackCount }} tracks</span>
      </a>

      <span v-if="exported" class="exported-chip">
        <CheckCircle2 :size="15" aria-hidden="true" />
        Exported
      </span>

      <button
        v-else
        type="button"
        class="export-button"
        :disabled="checkingStatus || isExporting"
        :aria-busy="isExporting"
        @click="handleExport"
      >
        <Loader2 v-if="checkingStatus || isExporting" :size="16" class="spin" aria-hidden="true" />
        <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="12" cy="12" r="9" fill="currentColor" opacity="0.16" />
          <path d="M7.6 9.4c3.2-.9 6.5-.5 9.1 1" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
          <path d="M8.2 12.5c2.6-.7 5.2-.4 7.3.8" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" />
          <path d="M8.8 15.5c2-.5 4-.3 5.6.6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
        </svg>
        <span>{{ buttonLabel }}</span>
      </button>
    </div>

    <p
      v-if="statusMessage"
      class="export-message"
      :class="`is-${statusType}`"
      :role="statusType === 'error' ? 'alert' : 'status'"
      aria-live="polite"
    >
      {{ statusMessage }}
    </p>
    <p v-else-if="showConnectHint" class="export-hint">
      You will be sent to Spotify to authorize, then brought back here to finish the export.
    </p>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  CheckCircle2,
  ExternalLink,
  Loader2,
} from 'lucide-vue-next'
import PlatformMark from './PlatformMark.vue'
import { API_BASE_URL } from '@/services/api'

const props = defineProps({
  sessionCode: {
    type: String,
    required: true,
  },
})

const isExporting = ref(false)
const checkingStatus = ref(true)
const exported = ref(false)
const authenticated = ref(null)
const playlistUrl = ref('')
const playlistTrackCount = ref(0)
const statusMessage = ref('')
const statusType = ref('info')
const failedOnce = ref(false)
const pendingExportKey = 'spotify_pending_export_session'

const buttonLabel = computed(() => {
  if (checkingStatus.value) return 'Checking Spotify…'
  if (isExporting.value) return 'Creating playlist…'
  if (failedOnce.value) return 'Try export again'
  if (authenticated.value === false) return 'Connect Spotify to export'
  return 'Export to Spotify'
})

const showConnectHint = computed(
  () => !exported.value && !checkingStatus.value && !isExporting.value && authenticated.value === false,
)

function applyExported(data) {
  exported.value = true
  authenticated.value = true
  playlistUrl.value = data.playlist_url || playlistUrl.value
  if (typeof data.tracks_in_playlist === 'number') {
    playlistTrackCount.value = data.tracks_in_playlist
  }
}

async function initiateLogin() {
  localStorage.setItem('auth_return_path', window.location.pathname)
  localStorage.setItem(pendingExportKey, props.sessionCode)
  statusMessage.value = 'Taking you to Spotify to authorize…'
  statusType.value = 'info'
  try {
    // Start OAuth on the backend origin: the state cookie is bound to that
    // origin, and the browser must hold it when Spotify redirects back.
    const cfgRes = await fetch(`${API_BASE_URL}/api/config`)
    const cfg = await cfgRes.json().catch(() => ({}))
    const startUrl = cfg.auth_start_url || `${API_BASE_URL}/api/auth/start`
    window.location.href = startUrl
  } catch (error) {
    console.error(error)
    localStorage.removeItem(pendingExportKey)
    failedOnce.value = true
    statusMessage.value = 'Spotify sign-in could not be started. Check your connection and try again.'
    statusType.value = 'error'
  }
}

async function checkExportStatus() {
  checkingStatus.value = true
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/export/status?session_code=${encodeURIComponent(props.sessionCode)}&target_platform=spotify`,
      { credentials: 'include' },
    )
    if (res.ok) {
      const data = await res.json()
      authenticated.value = typeof data.authenticated === 'boolean' ? data.authenticated : null
      if (data.exported) {
        applyExported(data)
        statusMessage.value = ''
      }
    }
  } catch (error) {
    // Status is only a convenience gate; never block exporting on it.
    console.error(error)
  } finally {
    checkingStatus.value = false
  }
}

async function handleExport() {
  if (exported.value || isExporting.value || checkingStatus.value) return

  // Purge any legacy token from localStorage.
  localStorage.removeItem('spotify_access_token')

  isExporting.value = true
  failedOnce.value = false
  statusMessage.value = 'Creating your Spotify playlist…'
  statusType.value = 'info'

  try {
    const res = await fetch(`${API_BASE_URL}/api/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        session_code: props.sessionCode,
        target_platform: 'spotify',
      }),
    })

    if (res.status === 401) {
      await initiateLogin()
      return
    }

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
      throw new Error(errData.detail || 'The playlist could not be created.')
    }

    const data = await res.json()
    if (data.already_existed) {
      statusMessage.value = `This playlist was already exported (${data.tracks_in_playlist} tracks). Opening the existing one.`
    } else {
      const failed = data.failed || 0
      statusMessage.value =
        failed > 0
          ? `Playlist created with ${data.tracks_added} of ${data.tracks_requested} tracks. ${failed} could not be found.`
          : `Playlist created with all ${data.tracks_added} tracks.`
    }
    statusType.value = 'success'
    localStorage.removeItem(pendingExportKey)
    applyExported(data)
  } catch (error) {
    console.error(error)
    failedOnce.value = true
    statusMessage.value =
      error?.message || 'The Spotify playlist could not be created. Check your connection and try again.'
    statusType.value = 'error'
  } finally {
    isExporting.value = false
  }
}

onMounted(async () => {
  await checkExportStatus()

  if (exported.value) {
    localStorage.removeItem(pendingExportKey)
    return
  }

  if (localStorage.getItem(pendingExportKey) === props.sessionCode) {
    void handleExport()
  }
})
</script>

<style scoped>
.export-panel {
  padding: clamp(18px, 3vw, 28px);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow);
}

.export-head {
  margin-bottom: var(--space-3);
}

.export-eyebrow {
  display: flex;
  align-items: center;
  gap: 7px;
  color: var(--text);
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
}

.export-desc {
  margin-top: 4px;
  color: var(--text-muted);
  font-size: var(--text-xs);
}

.export-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
}

.export-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  padding: 0 16px;
  border: 1px solid #19a34a;
  border-radius: var(--radius-pill);
  background: #1db954;
  color: #062310;
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
  transition:
    background var(--dur-1) var(--ease-out),
    transform var(--dur-1) var(--ease-out);
}

.export-button:hover:not(:disabled) {
  background: #24cc5f;
}

.export-button:active:not(:disabled) {
  transform: translateY(1px);
}

.export-button:disabled {
  opacity: 0.62;
}

.export-button:focus-visible {
  outline: 2px solid var(--focus-color);
  outline-offset: 2px;
}

.open-playlist {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 40px;
  padding: 0 16px;
  border: 1px solid #19a34a;
  border-radius: var(--radius-pill);
  background: #e6f7ec;
  color: #07542a;
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
  text-decoration: none;
  transition: background var(--dur-1) var(--ease-out);
}

.open-playlist:hover {
  background: #d3f1df;
}

.open-playlist:focus-visible {
  outline: 2px solid var(--focus-color);
  outline-offset: 2px;
}

.open-playlist .count {
  font-weight: var(--weight-medium);
  opacity: 0.8;
}

.exported-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border: 1px solid var(--success-border);
  border-radius: var(--radius-pill);
  background: var(--success-bg);
  color: var(--success-strong);
  font-size: var(--text-2xs);
  font-weight: var(--weight-semibold);
}

.export-message {
  margin-top: var(--space-2);
  font-size: var(--text-xs);
  line-height: 1.45;
}

.export-message.is-success {
  color: var(--success-strong);
}

.export-message.is-error {
  color: var(--danger-strong);
}

.export-message.is-info {
  color: var(--text-muted);
}

.export-hint {
  margin-top: var(--space-2);
  color: var(--text-faint);
  font-size: var(--text-2xs);
  line-height: 1.45;
}

@media (max-width: 420px) {
  .export-button,
  .open-playlist {
    width: 100%;
    justify-content: center;
  }
}
</style>
