import axios from 'axios'

// In Docker the app is served by nginx, which proxies /api to the backend, so
// the base URL is intentionally empty (relative requests). In local dev
// (npm run dev) it falls back to the backend on port 8000.
const configuredBase = import.meta.env.VITE_API_URL
export const API_BASE_URL =
  configuredBase === undefined ? 'http://localhost:8000' : configuredBase.replace(/\/+$/, '')

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
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