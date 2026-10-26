import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

function shareUrlFor(code, provided) {
  if (provided) return provided
  if (typeof window === 'undefined') return ''
  return `${window.location.origin}/join/${code}`
}

export const usePlaylistStore = defineStore('playlist', () => {
  // Session state
  const tracks = ref([])
  const loading = ref(false)
  const tracksLoading = ref(false)
  const error = ref(null)
  const tracksError = ref(null)
  const sessionCode = ref(null)
  const shareUrl = ref('')
  const stats = ref(null)
  const sourcePlatform = ref(null)
  const targetPlatform = ref(null)

  const hasResults = computed(() => tracks.value.length > 0)
  const matchRate = computed(() => {
    if (!stats.value) return 0
    return stats.value.match_rate * 100
  })

  /**
   * Convert a playlist. The convert endpoint intentionally does not return
   * tracks (they are stored server-side), so callers should follow up with
   * `loadTracks()` to fill the review list.
   */
  async function convertPlaylist(url, target = 'youtube_music') {
    loading.value = true
    error.value = null
    tracksError.value = null
    tracks.value = []
    sessionCode.value = null
    shareUrl.value = ''
    stats.value = null
    sourcePlatform.value = null
    targetPlatform.value = null

    try {
      const response = await api.convertPlaylist(url, target)
      const data = response.data

      sessionCode.value = data.code
      shareUrl.value = shareUrlFor(data.code, data.share_url)
      stats.value = data.stats
      sourcePlatform.value = data.source_platform
      targetPlatform.value = data.target_platform

      return data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to convert playlist'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch tracks for an already-created session without toggling the global
   * page-loading flag. Used by the home results view so the convert button
   * does not appear to run twice.
   */
  async function loadTracks(code) {
    if (!code) return null

    tracksLoading.value = true
    tracksError.value = null

    try {
      const response = await api.getSession(code)
      const data = response.data

      tracks.value = Array.isArray(data.tracks) ? data.tracks : []
      if (data.stats) stats.value = data.stats
      sessionCode.value = code
      if (data.target_platform) targetPlatform.value = data.target_platform
      if (data.source_platform) sourcePlatform.value = data.source_platform
      if (!shareUrl.value) shareUrl.value = shareUrlFor(code)

      return data
    } catch (err) {
      tracksError.value =
        err.response?.data?.detail ||
        'The converted tracks could not be loaded. The session may have expired.'
      throw err
    } finally {
      tracksLoading.value = false
    }
  }

  /** Load a shared session and its tracks (join page). */
  async function loadSession(code) {
    loading.value = true
    error.value = null
    tracksError.value = null
    tracks.value = []

    try {
      const response = await api.getSession(code)
      const data = response.data

      tracks.value = Array.isArray(data.tracks) ? data.tracks : []
      stats.value = data.stats
      sessionCode.value = code
      shareUrl.value = shareUrlFor(code)
      targetPlatform.value = data.target_platform
      sourcePlatform.value = data.source_platform

      return data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Session not found or expired'
      throw err
    } finally {
      loading.value = false
    }
  }

  function reset() {
    tracks.value = []
    loading.value = false
    tracksLoading.value = false
    error.value = null
    tracksError.value = null
    sessionCode.value = null
    shareUrl.value = ''
    stats.value = null
    sourcePlatform.value = null
    targetPlatform.value = null
  }

  return {
    // State
    tracks,
    loading,
    tracksLoading,
    error,
    tracksError,
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
    loadTracks,
    loadSession,
    reset,
  }
})
