<template>
  <span
    class="platform-mark"
    :class="`is-${size}`"
    :style="{ '--mark-color': color, '--mark-soft': soft }"
    aria-hidden="true"
  >
    <span class="monogram">{{ platform.monogram }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { getPlatform, platformColor, platformSoftColor } from '@/lib/platforms'

const props = defineProps({
  platform: {
    type: String,
    default: '',
  },
  size: {
    type: String,
    default: 'md', // sm | md | lg
  },
})

const platform = computed(() => getPlatform(props.platform))
const color = computed(() => platformColor(props.platform))
const soft = computed(() => platformSoftColor(props.platform))
</script>

<style scoped>
.platform-mark {
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
  width: 34px;
  height: 34px;
  border: 1px solid color-mix(in srgb, var(--mark-color) 22%, transparent);
  border-radius: 10px;
  background: var(--mark-soft);
  color: var(--mark-color);
  font-weight: var(--weight-bold);
  line-height: 1;
}

.monogram {
  font-size: 0.95rem;
  letter-spacing: -0.02em;
}

.is-sm {
  width: 26px;
  height: 26px;
  border-radius: 8px;
}

.is-sm .monogram {
  font-size: 0.72rem;
}

.is-lg {
  width: 48px;
  height: 48px;
  border-radius: 14px;
}

.is-lg .monogram {
  font-size: 1.3rem;
}
</style>
