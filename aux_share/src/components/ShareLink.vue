<!-- src/components/ShareLink.vue -->

<template>
  <div class="share-link">
    <h3>🔗 Share This Playlist</h3>
    
    <div class="share-container">
      <div class="code-display">
        <span class="label">Session Code:</span>
        <span class="code">{{ code }}</span>
      </div>
      
      <div class="url-container">
        <input 
          ref="urlInput"
          type="text" 
          :value="shareUrl" 
          readonly
          class="share-url"
        />
        <button @click="copyToClipboard" class="copy-button">
          {{ copied ? '✓ Copied!' : '📋 Copy' }}
        </button>
      </div>
      
      <p class="info-text">
        Share this link with the driver so they can access the converted playlist!
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'  // ✅ MAKE SURE THIS IS HERE

const props = defineProps({
  code: {
    type: String,
    required: true
  },
  shareUrl: {
    type: String,
    required: true
  }
})

const urlInput = ref(null)
const copied = ref(false)

function copyToClipboard() {
  urlInput.value.select()
  document.execCommand('copy')
  
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 2000)
}
</script>

<style scoped>
.share-link {
  margin: 30px 0;
  padding: 25px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: white;
}

h3 {
  margin-bottom: 20px;
}

.share-container {
  background: rgba(255, 255, 255, 0.1);
  padding: 20px;
  border-radius: 12px;
}

.code-display {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  font-size: 1.5rem;
}

.code {
  font-family: 'Courier New', monospace;
  font-weight: 700;
  font-size: 2rem;
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
}

.url-container {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.share-url {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  color: #333;
}

.copy-button {
  padding: 12px 24px;
  background: white;
  color: #667eea;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.copy-button:hover {
  background: #f0f0f0;
}

.info-text {
  text-align: center;
  font-size: 0.9rem;
  opacity: 0.9;
  margin: 0;
}
</style>