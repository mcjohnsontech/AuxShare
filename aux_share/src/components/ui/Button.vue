<template>
  <button
    :class="['btn', `btn-${variant}`, { 'btn-loading': loading, 'btn-disabled': disabled }]"
    :disabled="disabled || loading"
    @click="$emit('click', $event)"
  >
    <span v-if="loading" class="btn-spinner"></span>
    <slot />
  </button>
</template>

<script setup>
defineProps({
  variant: { type: String, default: 'primary' }, // primary, secondary, ghost, danger
  loading: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false }
})
defineEmits(['click'])
</script>

<style scoped>
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: 10px 16px;
  border-radius: var(--radius-sm);
  font-family: var(--font-sans);
  font-weight: 500;
  font-size: 14px;
  line-height: 1.5;
  cursor: pointer;
  border: 1px solid transparent;
  min-height: 44px;
  min-width: 44px;
  transition: background 150ms ease-out, color 150ms ease-out, border-color 150ms ease-out;
}
.btn-primary {
  background: var(--blue-500);
  color: white;
}
.btn-primary:hover:not(:disabled) {
  background: var(--blue-600);
}
.btn-primary:active:not(:disabled) {
  background: var(--blue-700);
}
.btn-secondary {
  background: var(--surface);
  color: var(--text);
  border-color: var(--border);
}
.btn-secondary:hover:not(:disabled) {
  background: var(--surface-2);
}
.btn-ghost {
  background: transparent;
  color: var(--text);
}
.btn-ghost:hover:not(:disabled) {
  background: var(--surface-2);
}
.btn-danger {
  background: var(--danger);
  color: white;
}
.btn:disabled,
.btn-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
