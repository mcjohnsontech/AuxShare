<!-- src/components/PlaylistInput.vue -->

<template>
  <div class="playlist-input">
    <h1 class="title">🎵 AuxParty</h1>
    <p class="subtitle">Share music across any platform in seconds</p>
    <p class="free-badge">✨ Now with FREE Apple Music support!</p>
    <div class="info-box">
      <h4>💡 Pro Tip</h4>
      <p>
        <strong>Spotify playlists work best!</strong><br>
        YouTube Music playlists may occasionally fail due to API limitations.
      </p>
    </div>
    <!-- Platform Selector -->
    <PlatformSelector v-model="targetPlatform" />

    <form @submit.prevent="handleSubmit" class="input-form">
      <input
        v-model="playlistUrl"
        type="text"
        placeholder="Paste your playlist URL (Spotify, YouTube Music, etc.)..."
        :disabled="loading"
        class="url-input"
      />
      
      <button 
        type="submit" 
        :disabled="loading || !playlistUrl"
        class="convert-button"
      >
        <span v-if="!loading">Convert Playlist</span>
        <span v-else>Converting... ⏳</span>
      </button>
    </form>

    <div v-if="error" class="error-message">
      ❌ {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'  // ✅ ADD computed HERE
import { usePlaylistStore } from '@/stores/playlist'
import PlatformSelector from './PlatformSelector.vue'

const playlistStore = usePlaylistStore()

const playlistUrl = ref('')
const targetPlatform = ref('apple_music')  // Default to Apple Music

const emit = defineEmits(['converted'])

const loading = computed(() => playlistStore.loading)
const error = computed(() => playlistStore.error)

async function handleSubmit() {
  if (!playlistUrl.value) return

  try {
    await playlistStore.convertPlaylist(playlistUrl.value, targetPlatform.value)
    emit('converted')
  } catch (err) {
    // Error is handled in store
  }
}
</script>

<style scoped>
.playlist-input {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.title {
  font-size: 3.5rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  font-size: 1.2rem;
  color: #666;
  margin-bottom: 1rem;
}

.free-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  display: inline-block;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 20px;
}

.input-form {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.url-input {
  flex: 1;
  padding: 15px 20px;
  font-size: 16px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  transition: border-color 0.3s;
}

.url-input:focus {
  outline: none;
  border-color: #667eea;
}

.url-input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.convert-button {
  padding: 15px 30px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.convert-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
}

.convert-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.error-message {
  padding: 15px;
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 8px;
  color: #c33;
  margin-top: 15px;
}
.info-box {
  background: #fff3cd;
  border: 2px solid #ffc107;
  border-radius: 12px;
  padding: 15px;
  margin: 20px 0;
}

.info-box h4 {
  margin: 0 0 8px 0;
  color: #856404;
}

.info-box p {
  margin: 0;
  color: #856404;
  font-size: 0.9rem;
  line-height: 1.5;
}
</style>