<template>
  <div class="callback-view">
    <div class="content">
      <Loader2 class="spinner" />
      <h2>{{ message }}</h2>
      <p>Please wait while we verify your account.</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Loader2 } from 'lucide-vue-next'
import { API_BASE_URL } from '@/services/api'

const router = useRouter()
const route = useRoute()
const message = ref('Connecting to Spotify...')

async function adoptSession(handoff) {
  const res = await fetch(`${API_BASE_URL}/api/auth/handoff`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ code: handoff })
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || 'Could not complete Spotify sign-in')
  }
}

function goBack() {
  const returnPath = localStorage.getItem('auth_return_path')
  if (returnPath) {
    localStorage.removeItem('auth_return_path')
    router.push(returnPath)
  } else {
    router.push('/')
  }
}

onMounted(async () => {
  // Clear any legacy plaintext token stored in localStorage for security
  localStorage.removeItem('spotify_access_token')

  const { status, error, handoff } = route.query

  if (error) {
    console.error('Auth error:', error)
    localStorage.removeItem('spotify_pending_export_session')
    localStorage.removeItem('auth_return_path')
    router.push('/?auth_error=' + encodeURIComponent(error))
    return
  }

  if (status === 'success' || handoff) {
    try {
      if (handoff) {
        message.value = 'Finishing sign-in...'
        await adoptSession(handoff)
      }
      goBack()
    } catch (e) {
      console.error(e)
      message.value = 'Spotify sign-in failed'
      localStorage.removeItem('spotify_pending_export_session')
      localStorage.removeItem('auth_return_path')
      router.push('/?auth_error=' + encodeURIComponent(e.message || 'handoff_failed'))
    }
  } else {
    router.push('/')
  }
})
</script>

<style scoped>
.callback-view {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg, #f5f7fb);
  color: var(--color-text, #0f172a);
}

.content {
  text-align: center;
}

.spinner {
  width: 48px;
  height: 48px;
  color: #1db954;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
