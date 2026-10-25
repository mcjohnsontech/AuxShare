<!-- src/components/TrackList.vue -->

<template>
  <div class="track-list">
    <div class="list-heading">
      <div>
        <p class="eyebrow">Track details</p>
        <h3>Matched songs</h3>
      </div>
      <span class="count">{{ tracks.length }} songs</span>
    </div>
    
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
  margin: 16px 0;
  padding: 24px;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow);
}
.list-heading { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 18px; }
.eyebrow { margin: 0 0 4px; color: var(--blue-500); font-size: 12px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
h3 { margin: 0; color: var(--text); font-size: 20px; }
.count { color: var(--text-muted); font-size: 13px;
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
  padding: 13px;
  margin-bottom: 8px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  transition: border-color 150ms ease-out, background 150ms ease-out;
}
.track-item:hover {
  border-color: var(--blue-300);
  background: var(--blue-50);
}
.track-item.not-matched {
  background: var(--warning-bg);
  border-color: #f2dfac;
}

.track-number {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-faint);
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
  color: var(--text);
  margin-bottom: 5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-artist {
  font-size: 0.95rem;
  color: var(--text-muted);
  margin-bottom: 3px;
}

.track-album {
  font-size: 0.85rem;
  color: var(--text-faint);
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
  background: var(--success-bg);
  color: var(--success);
}

.status-badge.error {
  background: var(--danger-bg);
  color: var(--danger);
}

.confidence {
  font-size: 0.8rem;
  color: var(--text-muted);
}

/* Custom scrollbar */
.list-container::-webkit-scrollbar {
  width: 8px;
}

.list-container::-webkit-scrollbar-track {
  background: var(--bg-subtle);
  border-radius: 4px;
}

.list-container::-webkit-scrollbar-thumb {
  background: var(--blue-300);
  border-radius: 4px;
}
@media (max-width: 560px) {
  .track-item { align-items: flex-start; }
  .track-status { align-items: flex-start; }
  .track-number { min-width: 22px; }
}
</style>