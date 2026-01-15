<template>
  <div class="playable-track-list">
    <div class="header">
      <div class="header-content">
        <h3 class="header-title">
          <Music class="header-icon" />
          {{ tracks.length }} Songs Ready to Play
        </h3>
        <button 
          v-if="canPlayQueue" 
          class="play-all-button" 
          @click="$emit('play-all')"
        >
          <Play class="btn-icon" /> Play Queue
        </button>
      </div>
      <div class="platform-badge">
        <component :is="getPlatformIcon(targetPlatform)" class="badge-icon" />
        <span class="name">{{ getPlatformName(targetPlatform) }}</span>
      </div>
    </div>
    
    <div class="list-container">
      <div 
        v-for="(track, index) in tracks" 
        :key="index"
        class="track-item"
        :class="{ 'unavailable': !getTrackUrl(track) }"
      >
        <div class="track-number">{{ index + 1 }}</div>
        
        <div class="track-info">
          <div class="track-title">{{ track.title }}</div>
          <div class="track-artist">{{ track.artist }}</div>
          <div class="track-album" v-if="track.album">{{ track.album }}</div>
        </div>
        
        <div class="track-actions">
          <a 
            v-if="getTrackUrl(track)" 
            :href="getTrackUrl(track)"
            target="_blank"
            class="play-button"
            @click.prevent="trackPlayClick(track, index)"
          >
            <Play class="action-icon" /> Play
          </a>
          <span v-else class="unavailable-text">
            Not Available
          </span>
        </div>
      </div>
    </div>

    <!-- Summary at bottom -->
    <div class="summary">
      <p>
        <strong>{{ availableCount }}</strong> of <strong>{{ tracks.length }}</strong> songs available
      </p>
      
      <a 
        v-if="playlistUrl" 
        :href="playlistUrl"
        target="_blank"
        class="open-playlist-button"
      >
        <ExternalLink class="btn-icon" /> 
        Open Playlist in {{ getPlatformName(targetPlatform) }}
      </a>
      
      <p v-else class="help-text">
        Click any song above to play it in {{ getPlatformName(targetPlatform) }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Music, Play, ExternalLink, Disc, Youtube, Headphones } from 'lucide-vue-next'

const props = defineProps({
  tracks: {
    type: Array,
    required: true
  },
  targetPlatform: {
    type: String,
    required: true
  }
})

// Get only tracks with valid URLs
const availableTracks = computed(() => {
  return props.tracks.filter(track => getTrackUrl(track) !== null)
})

const availableCount = computed(() => availableTracks.value.length)

// Generate playlist URL based on platform
const playlistUrl = computed(() => {
  const trackIds = availableTracks.value
    .map(track => {
      const idKey = `${props.targetPlatform}_id`
      return track[idKey]
    })
    .filter(id => id)
  
  if (trackIds.length === 0) return null
  
  switch (props.targetPlatform) {
    case 'spotify':
      if (trackIds.length === 1) {
        return `https://open.spotify.com/track/${trackIds[0]}`
      }
      return `https://open.spotify.com/track/${trackIds[0]}`
    
    case 'apple_music':
      if (trackIds.length > 0) {
        return `https://music.apple.com/us/song/${trackIds[0]}`
      }
      return null
    
    case 'youtube_music':
      if (trackIds.length === 1) {
        return `https://music.youtube.com/watch?v=${trackIds[0]}`
      }
      const videoIds = trackIds.join(',')
      return `https://music.youtube.com/watch?v=${trackIds[0]}&list=RD${trackIds[0]}`
    
    default:
      return null
  }
})

function getTrackUrl(track) {
  const urlKey = `${props.targetPlatform}_url`
  if (track[urlKey]) {
    return track[urlKey]
  }
  
  const idKey = `${props.targetPlatform}_id`
  const trackId = track[idKey]
  
  if (!trackId) return null
  
  switch (props.targetPlatform) {
    case 'apple_music':
      return `https://music.apple.com/us/song/${trackId}`
    
    case 'spotify':
      return `https://open.spotify.com/track/${trackId}`
    
    case 'youtube_music':
      return `https://music.youtube.com/watch?v=${trackId}`
    
    default:
      return null
  }
}

function getPlatformIcon(platform) {
  const icons = {
    'spotify': Disc,
    'apple_music': Music,
    'youtube_music': Youtube
  }
  return icons[platform] || Music
}

function getPlatformName(platform) {
  const names = {
    'spotify': 'Spotify',
    'apple_music': 'Apple Music',
    'youtube_music': 'YouTube Music'
  }
  return names[platform] || platform
}

const canPlayQueue = computed(() => {
  return ['apple_music', 'youtube_music'].includes(props.targetPlatform)
})

function trackPlayClick(track, index) {
  if (canPlayQueue.value) {
    emit('play-track', index)
  } else {
    window.open(getTrackUrl(track), '_blank')
  }
}

const emit = defineEmits(['play-all', 'play-track'])

</script>

<style scoped>
.playable-track-list {
  background: var(--mantine-color-dark-6); /* Surface */
  border-radius: 8px; /* Mantine Radius MD */
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 10px 15px -5px rgba(0,0,0,0.1);
  border: 1px solid #373A40;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #373A40;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-title {
  margin: 0;
  color: var(--mantine-color-gray-0);
  font-size: 1.25rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  width: 24px;
  height: 24px;
  color: var(--mantine-color-grape-9);
}

.play-all-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--mantine-color-grape-9);
  color: white;
  border: none;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.play-all-button:hover {
  background: var(--mantine-color-grape-7);
}

.btn-icon {
  width: 16px;
  height: 16px;
}

.platform-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--mantine-color-dark-7);
  color: var(--mantine-color-gray-5);
  border: 1px solid #373A40;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 500;
}

.badge-icon {
  width: 16px;
  height: 16px;
}

.list-container {
  max-height: 500px;
  overflow-y: auto;
  margin-bottom: 24px;
}

.track-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px;
  margin-bottom: 8px;
  background: transparent;
  border-radius: 4px;
  transition: background-color 0.2s;
  border: 1px solid transparent;
}

.track-item:hover {
  background: var(--mantine-color-dark-7);
  border-color: #373A40;
}

.track-item.unavailable {
  opacity: 0.5;
}

.track-number {
  font-size: 1rem;
  font-weight: 600;
  color: var(--mantine-color-gray-5);
  min-width: 30px;
  text-align: center;
}

.track-info {
  flex: 1;
  min-width: 0;
}

.track-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--mantine-color-gray-0);
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-artist {
  font-size: 0.875rem;
  color: var(--mantine-color-gray-5);
}

.track-album {
  font-size: 0.75rem;
  color: #5c5f66;
  margin-top: 2px;
}

.track-actions {
  min-width: 100px;
  text-align: right;
}

.play-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(134, 46, 156, 0.1);
  color: var(--mantine-color-grape-7);
  text-decoration: none;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.play-button:hover {
  background: rgba(134, 46, 156, 0.2);
}

.action-icon {
  width: 14px;
  height: 14px;
}

.unavailable-text {
  color: #5c5f66;
  font-size: 0.875rem;
  font-style: italic;
}

.summary {
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid #373A40;
}

.summary p {
  color: var(--mantine-color-gray-5);
  margin-bottom: 16px;
}

.summary strong {
  color: var(--mantine-color-gray-0);
}

.open-playlist-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: var(--mantine-color-green-9); /* Green for action */
  color: white;
  text-decoration: none;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 600;
  transition: background-color 0.2s;
  cursor: pointer;
}

.open-playlist-button:hover {
  background: var(--mantine-color-green-7);
}

.help-text {
  font-size: 0.875rem;
  color: #5c5f66;
}

/* Custom scrollbar */
.list-container::-webkit-scrollbar {
  width: 6px;
}

.list-container::-webkit-scrollbar-track {
  background: transparent;
}

.list-container::-webkit-scrollbar-thumb {
  background: #373A40;
  border-radius: 3px;
}
</style>