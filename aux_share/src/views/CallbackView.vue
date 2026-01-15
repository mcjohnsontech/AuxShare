<template>
  <div class="callback-view">
    <div class="content">
      <Loader2 class="spinner" />
      <h2>Connecting to Spotify...</h2>
      <p>Please wait while we verify your account.</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Loader2 } from 'lucide-vue-next'
import { usePlaylistStore } from '@/stores/playlist'

const router = useRouter()
const route = useRoute()
const playlistStore = usePlaylistStore()

onMounted(() => {
  const token = route.query.token
  const error = route.query.error
  
  if (token) {
    // Save token
    localStorage.setItem('spotify_access_token', token)
    
    // Check for return path
    const returnPath = localStorage.getItem('auth_return_path')
    if (returnPath) {
      localStorage.removeItem('auth_return_path')
      router.push(returnPath)
    } else {
      router.push('/')
    }
  } else if (error) {
    console.error('Auth error:', error)
    // Handle error (maybe redirect to home with error params)
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
  background: var(--mantine-color-dark-7);
  color: var(--mantine-color-gray-0);
}

.content {
  text-align: center;
}

.spinner {
  width: 48px;
  height: 48px;
  color: #1DB954; /* Spotify Green */
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
