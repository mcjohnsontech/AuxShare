<!-- src/components/TrackList.vue -->

<template>
  <div class="track-list">
    <h3>🎵 Tracks ({{ tracks.length }})</h3>
    
    <div class="list-container">
      <div 
        v-for="(track, index) in tracks" 
        :key="index"
        class="track-item"
        :class="{ 'not-matched': !isMatched(track) }"
      >
        <div class="track-number">{{ index + 1 }}</div>
        
        <div class="track-info">
          <div class="track-title">{{ track.title }}</div>
          <div class="track-artist">{{ track.artist }}</div>
          <div class="track-album">{{ track.album }}</div>
        </div>
        
        <div class="track-status">
          <span v-if="isMatched(track)" class="status-badge success">
            ✓ Matched
          </span>
          <span v-else class="status-badge error">
            ✗ Not Found
          </span>
          
          <div v-if="getConfidence(track)" class="confidence">
            {{ (getConfidence(track) * 100).toFixed(0) }}% confidence
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  tracks: {
    type: Array,
    required: true
  },
  targetPlatform: {
    type: String,
    default: 'youtube_music'
  }
})

function isMatched(track) {
  const idKey = `${props.targetPlatform}_id`
  return !!track[idKey]
}

function getConfidence(track) {
  const confidenceKey = `${props.targetPlatform}_confidence`
  return track[confidenceKey] || 0
}
</script>

<style scoped>
.track-list {
  margin: 30px 0;
}

h3 {
  margin-bottom: 20px;
  color: #333;
}

.list-container {
  max-height: 500px;
  overflow-y: auto;
  padding-right: 10px;
}

.track-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  margin-bottom: 10px;
  background: white;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  transition: all 0.3s;
}

.track-item:hover {
  border-color: #667eea;
  transform: translateX(5px);
}

.track-item.not-matched {
  opacity: 0.6;
  border-color: #fcc;
}

.track-number {
  font-size: 1.2rem;
  font-weight: 700;
  color: #999;
  min-width: 30px;
  text-align: center;
}

.track-info {
  flex: 1;
  min-width: 0;
}

.track-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-artist {
  font-size: 0.95rem;
  color: #666;
  margin-bottom: 3px;
}

.track-album {
  font-size: 0.85rem;
  color: #999;
}

.track-status {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 5px;
}

.status-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  white-space: nowrap;
}

.status-badge.success {
  background: #d4edda;
  color: #155724;
}

.status-badge.error {
  background: #f8d7da;
  color: #721c24;
}

.confidence {
  font-size: 0.8rem;
  color: #666;
}

/* Custom scrollbar */
.list-container::-webkit-scrollbar {
  width: 8px;
}

.list-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.list-container::-webkit-scrollbar-thumb {
  background: #667eea;
  border-radius: 4px;
}
</style>