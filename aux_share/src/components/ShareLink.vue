<!-- src/components/ShareLink.vue -->

<template>
  <div class="share-link">
    <div class="share-heading">
      <div>
        <p class="eyebrow">Ready to share</p>
        <h3>Send this playlist to your crew</h3>
      </div>
      <span class="share-icon">↗</span>
    </div>
    
    <div class="share-container">
      <div class="code-display">
        <span class="label">Session code</span>
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
          {{ copied ? 'Copied' : 'Copy link' }}
        </button>
      </div>
      
      <p class="info-text">
        Anyone with this link can view the matched tracks for the next 24 hours.
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
  margin: 16px 0;
  padding: 24px;
  background: var(--blue-900);
  border-radius: var(--radius-lg);
  color: #fff;
  box-shadow: 0 12px 28px rgba(11, 31, 77, .16);
}
.share-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.eyebrow { margin: 0 0 4px; color: var(--blue-300); font-size: 12px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
h3 { margin: 0 0 20px; color: #fff; font-size: 20px; }
.share-icon { font-size: 28px; color: var(--blue-300);
}

.share-container {
  background: rgba(255, 255, 255, 0.08);
  padding: 20px;
  border-radius: 12px;
}

.code-display {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  font-size: 1rem;
}

.code {
  font-family: 'Courier New', monospace;
  font-weight: 700;
  font-size: 1.25rem;
  padding: 8px 14px;
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
  background: #fff;
  color: var(--text);
}

.copy-button {
  padding: 12px 24px;
  background: var(--blue-50);
  color: var(--blue-700);
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.copy-button:hover {
  background: var(--blue-100);
}

.info-text {
  text-align: center;
  font-size: 0.85rem;
  opacity: 0.9;
  margin: 0;
}
</style>