<template>
  <span :class="['badge', `badge-${variant}`]">
    <slot />
  </span>
</template>

<script setup>
defineProps({
  variant: { type: String, default: 'neutral' } // success, warning, danger, neutral, info
})
</script>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  font-size: 12px;
  font-weight: 500;
  line-height: 1.5;
}
.badge-neutral {
  background: var(--bg-subtle);
  color: var(--text-muted);
  border: 1px solid var(--border);
}
.badge-success {
  background: var(--success-bg);
  color: var(--success);
}
.badge-warning {
  background: var(--warning-bg);
  color: var(--warning);
}
.badge-danger {
  background: var(--danger-bg);
  color: var(--danger);
}
.badge-info {
  background: var(--info-bg);
  color: var(--blue-700);
}
</style>
