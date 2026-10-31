<template>
  <fieldset class="platform-selector">
    <legend class="sr-only">Destination platform</legend>

    <div v-if="loading" class="platform-options" aria-hidden="true">
      <span v-for="n in 3" :key="n" class="platform-skeleton"></span>
    </div>

    <div v-else class="platform-options">
      <label
        v-for="option in platforms"
        :key="option.name"
        class="platform-option"
        :class="{ 'is-selected': modelValue === option.name }"
      >
        <input
          class="sr-only"
          type="radio"
          name="destination-platform"
          :value="option.name"
          :checked="modelValue === option.name"
          @change="$emit('update:modelValue', option.name)"
        />
        <PlatformMark :platform="option.name" />
        <span class="option-copy">
          <span class="option-name">{{ platformName(option) }}</span>
          <span class="option-note">{{ platformNote(option.name) }}</span>
        </span>
        <span class="option-check" aria-hidden="true">
          <Check :size="13" />
        </span>
      </label>
    </div>
  </fieldset>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { Check } from 'lucide-vue-next'
import api from '@/services/api'
import PlatformMark from './PlatformMark.vue'
import { PLATFORMS, getPlatform } from '@/lib/platforms'

defineProps({
  modelValue: {
    type: String,
    default: 'youtube_music',
  },
})

defineEmits(['update:modelValue'])

const platforms = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const response = await api.getSupportedTargets()
    const list = Array.isArray(response.data) ? response.data : []
    platforms.value = list.length ? list : fallbackPlatforms()
  } catch (error) {
    // The three destinations are compiled into the backend; a failed metadata
    // request should not block conversion.
    console.warn('Could not load destination platforms; using built-in list.', error)
    platforms.value = fallbackPlatforms()
  } finally {
    loading.value = false
  }
})

function fallbackPlatforms() {
  return Object.values(PLATFORMS).map((platform) => ({
    name: platform.key,
    display_name: platform.name,
  }))
}

function platformName(option) {
  return getPlatform(option.name).name || option.display_name || option.name
}

function platformNote(name) {
  return getPlatform(name).targetNote
}
</script>

<style scoped>
.platform-selector {
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
}

.platform-options {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-2);
}

.platform-option {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-width: 0;
  padding: 11px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--surface);
  cursor: pointer;
  transition:
    border-color var(--dur-1) var(--ease-out),
    background var(--dur-1) var(--ease-out),
    box-shadow var(--dur-1) var(--ease-out);
}

.platform-option:hover {
  border-color: var(--border-strong);
  background: var(--surface-2);
}

.platform-option.is-selected {
  border-color: var(--blue-500);
  background: var(--blue-50);
  box-shadow: 0 0 0 1px var(--blue-500);
}

/* Keyboard ring lives on the visible tile, not the visually hidden input. */
.platform-option:has(input:focus-visible) {
  outline: 2px solid var(--focus-color);
  outline-offset: 2px;
}

.option-copy {
  min-width: 0;
  padding-right: 14px;
}

.option-name {
  display: block;
  overflow: hidden;
  color: var(--text);
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--tracking-tight);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.option-note {
  display: block;
  margin-top: 2px;
  color: var(--text-muted);
  font-size: var(--text-2xs);
  line-height: 1.35;
}

.option-check {
  position: absolute;
  top: 10px;
  right: 10px;
  display: grid;
  place-items: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--blue-600);
  color: #fff;
  opacity: 0;
  transform: scale(0.7);
  transition:
    opacity var(--dur-1) var(--ease-out),
    transform var(--dur-1) var(--ease-out);
}

.is-selected .option-check {
  opacity: 1;
  transform: scale(1);
}

.platform-skeleton {
  display: block;
  height: 62px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: linear-gradient(
    100deg,
    var(--surface-2) 20%,
    var(--surface-3) 40%,
    var(--surface-2) 60%
  );
  background-size: 220% 100%;
  animation: platform-shimmer 1.4s var(--ease-in-out) infinite;
}

@keyframes platform-shimmer {
  0% { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}

@media (max-width: 640px) {
  .platform-options {
    grid-template-columns: 1fr;
  }

  .platform-option {
    align-items: center;
    padding: 10px 12px;
  }

  .option-note {
    font-size: var(--text-xs);
  }
}
</style>
