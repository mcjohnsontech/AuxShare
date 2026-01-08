import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 180000 // 2 minutes for playlist conversion
})


apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response) {
      // Server returned an error
      const message = error.response.data?.detail || error.message
      console.error('API Error:', message)
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error: No response from server')
    } else {
      // Something else happened
      console.error('Error:', error.message)
    }
    return Promise.reject(error)
  }
)

export default {
  // Extract playlist tracks
  extractPlaylist(url) {
    return apiClient.post('/api/extract-playlist', { url })
  },

  // Convert playlist to another platform
  convertPlaylist(url, targetPlatform = 'youtube_music') {
    return apiClient.post('/api/convert', {
      url,
      target_platform: targetPlatform
    })
  },

  // Get session by code
  getSession(code) {
    return apiClient.get(`/api/session/${code}`)
  },

  // Get session TTL
  getSessionTTL(code) {
    return apiClient.get(`/api/session/${code}/ttl`)
  },

  // Get supported platforms
  getSupportedPlatforms() {
    return apiClient.get('/api/platforms')
  },

  getSupportedSources() {
    return apiClient.get('/api/platforms/sources')
  },

  getSupportedTargets() {
    return apiClient.get('/api/platforms/targets')
  },

  // Health check
  healthCheck() {
    return apiClient.get('/')
  }
}