import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const usePlaylistStore = defineStore('playlist', () => {
  // State
  const tracks = ref([])
  const loading = ref(false)
  const error = ref(null)
  const sessionCode = ref(null)
  const shareUrl = ref(null)
  const stats = ref(null)
  const sourcePlatform = ref(null)
  const targetPlatform = ref(null)

  // Computed
  const hasResults = computed(() => tracks.value.length > 0)
  const matchRate = computed(() => {
    if (!stats.value) return 0
    return stats.value.match_rate * 100
  })

  // Actions
  async function convertPlaylist(url, target = 'youtube_music') {
    loading.value = true
    error.value = null
    tracks.value = []
    sessionCode.value = null
    shareUrl.value = null
    stats.value = null

    try {
      const response = await api.convertPlaylist(url, target)
      const data = response.data

      sessionCode.value = data.code
      shareUrl.value = data.share_url
      stats.value = data.stats
      sourcePlatform.value = data.source_platform
      targetPlatform.value = data.target_platform

      console.log('✅ Conversion successful:', data)

      return data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to convert playlist'
      console.error('❌ Conversion error:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

// src/stores/playlist.js (UPDATE loadSession)

async function loadSession(code) {
  loading.value = true
  error.value = null
  tracks.value = []

  try {
    const response = await api.getSession(code)
    const data = response.data

    tracks.value = data.tracks
    stats.value = data.stats
    sessionCode.value = code
    targetPlatform.value = data.target_platform  // ✅ Store it!
    sourcePlatform.value = data.source_platform  // ✅ Store source too!

    console.log('✅ Session loaded:', {
      tracks: tracks.value.length,
      targetPlatform: targetPlatform.value,
      sourcePlatform: sourcePlatform.value
    })

    return data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Session not found or expired'
    console.error('❌ Session error:', err)
    throw err
  } finally {
    loading.value = false
  }
}

  function reset() {
    tracks.value = []
    loading.value = false
    error.value = null
    sessionCode.value = null
    shareUrl.value = null
    stats.value = null
    sourcePlatform.value = null
    targetPlatform.value = null
  }

  return {
    // State
    tracks,
    loading,
    error,
    sessionCode,
    shareUrl,
    stats,
    sourcePlatform,
    targetPlatform,
    // Computed
    hasResults,
    matchRate,
    // Actions
    convertPlaylist,
    loadSession,
    reset
  }
})