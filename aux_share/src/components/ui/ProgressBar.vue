<template>
  <div class="progress" role="progressbar" :aria-valuenow="value" aria-valuemin="0" :aria-valuemax="max">
    <div class="progress-bar" :style="{ width: percentage + '%' }"></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({
  value: { type: Number, default: 0 },
  max: { type: Number, default: 100 }
})
const percentage = computed(() => Math.min(100, Math.max(0, (props.value / props.max) * 100)))
</script>

<style scoped>
.progress {
  width: 100%;
  height: 8px;
  background: var(--surface-2);
  border-radius: var(--radius-pill);
  overflow: hidden;
}
.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--blue-500), var(--blue-300));
  transition: width 250ms ease-out;
}
</style>
