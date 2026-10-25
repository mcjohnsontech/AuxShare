<template>
  <div class="field">
    <label v-if="label" class="label" :for="id">{{ label }}</label>
    <input
      :id="id"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      class="input"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <div v-if="help && !error" class="help">{{ help }}</div>
    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script setup>
defineProps({
  modelValue: String,
  label: String,
  placeholder: String,
  type: { type: String, default: 'text' },
  help: String,
  error: String,
  disabled: Boolean,
  id: String
})
defineEmits(['update:modelValue'])
</script>

<style scoped>
.field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.label {
  font-weight: 500;
  font-size: 14px;
  color: var(--text);
}
.input {
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-family: var(--font-sans);
  font-size: 14px;
  color: var(--text);
  background: var(--surface);
  min-height: 44px;
}
.input:focus {
  outline: 2px solid var(--blue-500);
  outline-offset: 2px;
  border-color: var(--blue-500);
}
.input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.help {
  font-size: 12px;
  color: var(--text-muted);
}
.error {
  font-size: 12px;
  color: var(--danger);
}
</style>
