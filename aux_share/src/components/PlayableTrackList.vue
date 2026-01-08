<!-- src/components/PlayableTrackList.vue (UPDATED) -->

<template>
    <div class="playable-track-list">
      <div class="header">
        <h3>🎵 {{ tracks.length }} Songs Ready to Play</h3>
        <div class="platform-badge">
          <span class="icon">{{ getPlatformIcon(targetPlatform) }}</span>
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
              @click="trackPlayClick(track)"
            >
              ▶️ Play
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
          🎶 Open Playlist in {{ getPlatformName(targetPlatform) }}
        </a>
        
        <p v-else class="help-text">
          Click any song above to play it in {{ getPlatformName(targetPlatform) }}
        </p>
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
        // Spotify doesn't support direct playlist URLs without creating a playlist
        // But we can create a search query with multiple tracks
        if (trackIds.length === 1) {
          return `https://open.spotify.com/track/${trackIds[0]}`
        }
        // For multiple tracks, open the first one
        // (Spotify requires API to create playlists)
        return `https://open.spotify.com/track/${trackIds[0]}`
      
      case 'apple_music':
        // Apple Music requires authentication to create playlists
        // Open first song
        if (trackIds.length > 0) {
          return `https://music.apple.com/us/song/${trackIds[0]}`
        }
        return null
      
      case 'youtube_music':
        // YouTube Music supports playlist URLs!
        if (trackIds.length === 1) {
          return `https://music.youtube.com/watch?v=${trackIds[0]}`
        }
        // Create a queue with multiple videos
        const videoIds = trackIds.join(',')
        return `https://music.youtube.com/watch?v=${trackIds[0]}&list=RD${trackIds[0]}`
      
      default:
        return null
    }
  })
  
  function getTrackUrl(track) {
    // Check for platform-specific URL first
    const urlKey = `${props.targetPlatform}_url`
    if (track[urlKey]) {
      return track[urlKey]
    }
    
    // Fallback: construct URL from ID
    const idKey = `${props.targetPlatform}_id`
    const trackId = track[idKey]
    
    if (!trackId) return null
    
    // Generate URL based on platform
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
      'spotify': '🟢',
      'apple_music': '🎵',
      'youtube_music': '🔴'
    }
    return icons[platform] || '🎵'
  }
  
  function getPlatformName(platform) {
    const names = {
      'spotify': 'Spotify',
      'apple_music': 'Apple Music',
      'youtube_music': 'YouTube Music'
    }
    return names[platform] || platform
  }
  
  function trackPlayClick(track) {
    console.log('Playing track:', track.title)
  }
  </script>
  
  <style scoped>
  .playable-track-list {
    background: white;
    border-radius: 16px;
    padding: 25px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }
  
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 2px solid #e0e0e0;
  }
  
  h3 {
    margin: 0;
    color: #333;
    font-size: 1.5rem;
  }
  
  .platform-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 20px;
    font-weight: 600;
  }
  
  .icon {
    font-size: 1.2rem;
  }
  
  .list-container {
    max-height: 500px;
    overflow-y: auto;
    margin-bottom: 20px;
  }
  
  .track-item {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 15px;
    margin-bottom: 10px;
    background: #f8f9fa;
    border-radius: 12px;
    transition: all 0.3s;
  }
  
  .track-item:hover {
    background: #e9ecef;
    transform: translateX(5px);
  }
  
  .track-item.unavailable {
    opacity: 0.5;
  }
  
  .track-number {
    font-size: 1.2rem;
    font-weight: 700;
    color: #999;
    min-width: 35px;
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
  
  .track-actions {
    min-width: 100px;
    text-align: right;
  }
  
  .play-button {
    display: inline-block;
    padding: 10px 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-decoration: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.3s;
  }
  
  .play-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
  }
  
  .unavailable-text {
    color: #999;
    font-size: 0.85rem;
    font-style: italic;
  }
  
  .summary {
    text-align: center;
    padding-top: 20px;
    border-top: 2px solid #e0e0e0;
  }
  
  .summary p {
    color: #666;
    margin-bottom: 15px;
    font-size: 1.1rem;
  }
  
  .summary strong {
    color: #667eea;
  }
  
  .open-playlist-button {
    display: inline-block;
    padding: 15px 30px;
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    color: white;
    text-decoration: none;
    border: none;
    border-radius: 12px;
    font-size: 1rem;
    font-weight: 700;
    transition: all 0.3s;
    cursor: pointer;
  }
  
  .open-playlist-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(40, 167, 69, 0.3);
  }
  
  .help-text {
    font-size: 0.9rem;
    color: #999;
    font-style: italic;
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