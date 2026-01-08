<!-- src/components/PlatformSelector.vue -->

<template>
    <div class="platform-selector">
      <label class="label">Convert to:</label>
      
      <div class="platform-buttons">
        <button
          v-for="platform in platforms"
          :key="platform.name"
          @click="selectPlatform(platform.name)"
          :class="['platform-btn', { active: modelValue === platform.name }]"
          type="button"
        >
          <span class="icon">{{ platform.icon }}</span>
          <span class="name">{{ platform.display_name }}</span>
        </button>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'  // ✅ ADD onMounted
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
  </script>
  
  <style scoped>
  .platform-selector {
    margin: 20px 0;
  }
  
  .label {
    display: block;
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 15px;
    color: #333;
  }
  
  .platform-buttons {
    display: flex;
    gap: 15px;
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .platform-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 20px 30px;
    background: white;
    border: 3px solid #e0e0e0;
    border-radius: 16px;
    cursor: pointer;
    transition: all 0.3s;
    min-width: 140px;
  }
  
  .platform-btn:hover {
    border-color: #667eea;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
  }
  
  .platform-btn.active {
    border-color: #667eea;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }
  
  .icon {
    font-size: 2.5rem;
  }
  
  .name {
    font-size: 1rem;
    font-weight: 600;
  }
  </style>