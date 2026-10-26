<template>
  <header class="app-header">
    <div class="app-header-inner">
      <RouterLink to="/" class="brand" aria-label="AuxShare — go to the converter">
        <span class="brand-mark" aria-hidden="true">
          <span class="brand-bar" style="height: 8px"></span>
          <span class="brand-bar" style="height: 15px"></span>
          <span class="brand-bar" style="height: 11px"></span>
        </span>
        <span class="brand-name">AuxShare</span>
      </RouterLink>

      <p v-if="tagline" class="brand-tagline">{{ tagline }}</p>

      <div class="header-actions">
        <slot />
      </div>
    </div>
  </header>
</template>

<script setup>
import { RouterLink } from 'vue-router'

defineProps({
  tagline: {
    type: String,
    default: '',
  },
})
</script>

<style scoped>
.app-header {
  border-bottom: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: saturate(140%) blur(10px);
}

.app-header-inner {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  max-width: var(--container);
  min-height: var(--header-height);
  margin: 0 auto;
  padding: 0 var(--page-gutter);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--text);
  text-decoration: none;
  border-radius: var(--radius-sm);
}

.brand-mark {
  display: inline-flex;
  align-items: flex-end;
  justify-content: center;
  gap: 2.5px;
  width: 32px;
  height: 32px;
  padding-bottom: 8px;
  border-radius: 9px;
  background: var(--brand);
  box-shadow: inset 0 -6px 12px rgba(11, 31, 77, 0.18);
}

.brand-bar {
  width: 3.5px;
  border-radius: 2px;
  background: #fff;
}

.brand-name {
  font-size: var(--text-md);
  font-weight: var(--weight-bold);
  letter-spacing: var(--tracking-tight);
}

.brand-tagline {
  margin: 0 0 0 var(--space-2);
  padding-left: var(--space-4);
  border-left: 1px solid var(--border);
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-left: auto;
}

.brand:focus-visible {
  outline: 2px solid var(--focus-color);
  outline-offset: 4px;
}

@media (max-width: 720px) {
  .brand-tagline {
    display: none;
  }
}
</style>
