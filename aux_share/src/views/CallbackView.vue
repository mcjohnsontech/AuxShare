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

const router = useRouter()
const route = useRoute()

onMounted(() => {
  // Clear any legacy plaintext token stored in localStorage for security
  localStorage.removeItem('spotify_access_token')
  
  const status = route.query.status
  const error = route.query.error
  
  if (status === 'success' || route.query.token) {
    const returnPath = localStorage.getItem('auth_return_path')
    if (returnPath) {
      localStorage.removeItem('auth_return_path')
      router.push(returnPath)
    } else {
      router.push('/')
    }
  } else if (error) {
    console.error('Auth error:', error)
    router.push('/?auth_error=' + encodeURIComponent(error))
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
