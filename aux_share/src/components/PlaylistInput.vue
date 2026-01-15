<template>
  <div class="playlist-input">
    <h1 class="title">
      <Music class="title-icon" />
      AuxParty
    </h1>
    <p class="subtitle">Share music across any platform in seconds</p>
    <p class="free-badge">
      <Sparkles class="badge-icon" />
      Now with FREE Apple Music support!
    </p>
    <div class="info-box">
      <div class="info-header">
        <Lightbulb class="info-icon" />
        <h4>Pro Tip</h4>
      </div>
      <p>
        <strong>Spotify playlists work best!</strong><br>
        YouTube Music playlists may occasionally fail due to API limitations.
      </p>
    </div>
    <!-- Platform Selector -->
    <PlatformSelector v-model="targetPlatform" />

    <form @submit.prevent="handleSubmit" class="input-form">
      <div class="input-wrapper">
        <input
          v-model="playlistUrl"
          type="text"
          placeholder="Paste your playlist URL (Spotify, YouTube Music, etc.)..."
          :disabled="loading"
          class="url-input"
        />
      </div>
      
      <button 
        type="submit" 
        :disabled="loading || !playlistUrl"
        class="convert-button"
      >
        <Loader2 v-if="loading" class="spin-icon" />
        <span v-else>Convert Playlist</span>
      </button>
    </form>

    <div v-if="error" class="error-message">
      <AlertCircle class="error-icon" />
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { usePlaylistStore } from '@/stores/playlist'
import PlatformSelector from './PlatformSelector.vue'
import { Music, Sparkles, Lightbulb, Loader2, AlertCircle } from 'lucide-vue-next'

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
  padding: 40px;
  background: var(--mantine-color-dark-6);
  border-radius: 8px;
  border: 1px solid #373A40;
  text-align: center;
}

.title {
  font-size: 2.5rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
  color: var(--mantine-color-gray-0);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.title-icon {
  width: 40px;
  height: 40px;
  color: var(--mantine-color-grape-9);
}

.subtitle {
  font-size: 1.1rem;
  color: var(--mantine-color-gray-5);
  margin-bottom: 1.5rem;
}

.free-badge {
  background: rgba(134, 46, 156, 0.15);
  color: var(--mantine-color-grape-7);
  padding: 6px 16px;
  border-radius: 20px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 24px;
  border: 1px solid rgba(134, 46, 156, 0.3);
}

.badge-icon {
  width: 16px;
  height: 16px;
}

.input-form {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.input-wrapper {
  flex: 1;
  position: relative;
}

.url-input {
  width: 100%;
  padding: 12px 16px;
  font-size: 1rem;
  background: var(--mantine-color-dark-7);
  border: 1px solid #373A40;
  border-radius: 4px; /* Mantine default radius */
  color: var(--mantine-color-gray-0);
  transition: border-color 0.2s;
}

.url-input:focus {
  outline: none;
  border-color: var(--mantine-color-grape-9);
}

.url-input::placeholder {
  color: #5c5f66;
}

.url-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.convert-button {
  padding: 0 24px;
  font-size: 1rem;
  font-weight: 600;
  background: var(--mantine-color-grape-9);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 160px;
}

.convert-button:hover:not(:disabled) {
  background: var(--mantine-color-grape-7);
}

.convert-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.spin-icon {
  animation: spin 1s linear infinite;
  width: 20px;
  height: 20px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.error-message {
  padding: 12px;
  background: rgba(255, 107, 107, 0.1);
  border: 1px solid rgba(255, 107, 107, 0.3);
  border-radius: 4px;
  color: #ff6b6b;
  margin-top: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 0.9rem;
}

.error-icon {
  width: 18px;
  height: 18px;
}

.info-box {
  background: rgba(250, 176, 5, 0.1); /* Yellow/Orange tint */
  border: 1px solid rgba(250, 176, 5, 0.3);
  border-radius: 4px;
  padding: 16px;
  margin: 0 0 24px 0;
  text-align: left;
}

.info-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.info-icon {
  width: 18px;
  height: 18px;
  color: #fab005;
}

.info-box h4 {
  margin: 0;
  color: #fab005;
  font-size: 1rem;
}

.info-box p {
  margin: 0;
  color: var(--mantine-color-gray-5);
  font-size: 0.9rem;
  line-height: 1.5;
  padding-left: 26px; /* Align with text start */
}

.info-box strong {
  color: var(--mantine-color-gray-0);
}
</style>