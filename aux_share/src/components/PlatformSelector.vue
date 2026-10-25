<!-- src/components/PlatformSelector.vue -->

<template>
    <div class="platform-selector" aria-label="Choose destination platform">
      
      <div class="platform-buttons">
        <button
          v-for="platform in platforms"
          :key="platform.name"
          @click="selectPlatform(platform.name)"
          :class="['platform-btn', { active: modelValue === platform.name }]"
          type="button"
        >
          <span class="platform-icon">{{ getPlatformInitial(platform) }}</span>
          <span class="platform-copy">
            <span class="name">{{ platform.display_name }}</span>
            <span class="note">{{ getPlatformNote(platform.name) }}</span>
          </span>
          <span v-if="modelValue === platform.name" class="selected-mark">✓</span>
        </button>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  import api from '@/services/api'
  
  const props = defineProps({
    modelValue: {
      type: String,
      default: 'youtube_music'
    }
  })
  
  const emit = defineEmits(['update:modelValue'])
  
  const platforms = ref([])
  
  onMounted(async () => {
    try {
      const response = await api.getSupportedTargets()
      platforms.value = response.data
    } catch (error) {
      console.error('Failed to load platforms:', error)
      // Fallback to default platforms
      platforms.value = [
        { name: 'youtube_music', display_name: 'YouTube Music', icon: '🔴' },
        { name: 'apple_music', display_name: 'Apple Music', icon: '🎵' },
        { name: 'spotify', display_name: 'Spotify', icon: '🟢' }
      ]
    }
  })
  
  function selectPlatform(name) {
    emit('update:modelValue', name)
  }

  function getPlatformInitial(platform) {
    return platform.name === 'youtube_music' ? 'Y' : platform.display_name.charAt(0)
  }

  function getPlatformNote(name) {
    const notes = {
      spotify: 'Best for playlist export',
      youtube_music: 'Play matched tracks',
      apple_music: 'Free catalog matching'
    }
    return notes[name] || 'Available destination'
  }
  </script>
  
  <style scoped>
  .platform-selector {
      margin-top: 22px;
    }
  
  .platform-buttons {
    display: flex;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
  }
  
  .platform-btn {
    display: flex;
    position: relative;
    display: flex;
    align-items: flex-start;
    gap: 10px;
    min-width: 0;
    padding: 14px 12px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    color: var(--text);
    cursor: pointer;
    text-align: left;
    transition: border-color 150ms ease-out, background 150ms ease-out, box-shadow 150ms ease-out;
  }
  
  .platform-btn:hover {
    border-color: var(--blue-300);
    background: var(--blue-50);
  }
  
  .platform-btn.active {
    border-color: var(--blue-500);
    background: var(--blue-50);
    box-shadow: 0 0 0 2px var(--blue-100);
  }
  .platform-icon {
    display: grid;
    place-items: center;
    flex: 0 0 32px;
    height: 32px;
    border-radius: 9px;
    background: var(--blue-100);
    color: var(--blue-700);
    font-size: 15px;
    font-weight: 700;
  }
  .platform-copy { min-width: 0; }
  .name { display: block; font-size: 13px; font-weight: 700; }
  .note { display: block; margin-top: 3px; color: var(--text-muted); font-size: 11px; line-height: 1.3; }
  .selected-mark { margin-left: auto; color: var(--blue-500); font-weight: 700; }
  @media (max-width: 640px) {
    .platform-buttons { grid-template-columns: 1fr; }
  }
  </style>