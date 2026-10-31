<template>
  <header class="app-header">
    <div class="app-header-inner">
      <RouterLink to="/" class="brand" aria-label="AuxShare — go to the converter">
        <span class="brand-name"><span>Aux</span>Share<span class="brand-period">.</span></span>
      </RouterLink>

      <p v-if="tagline" class="brand-tagline">{{ tagline }}</p>
      <nav class="header-nav" aria-label="Main navigation"><RouterLink to="/#how-it-works">How it works</RouterLink></nav>

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
.app-header { border-bottom: 1px solid var(--border); background: rgba(252,250,247,.94); }
.app-header-inner { display: flex; align-items: center; gap: 24px; max-width: var(--container); min-height: var(--header-height); margin: auto; padding: 0 var(--page-gutter); }
.brand { display: inline-flex; color: var(--text); text-decoration: none; border-radius: 6px; }
.brand-name { font-size: 30px; font-weight: 850; letter-spacing: -.065em; }
.brand-name > span { color: var(--brand); }
.brand-period { margin-left: 1px; }
.brand-tagline { color: var(--text-faint); font-size: 12px; }
.header-nav { margin-left: auto; }
.header-nav a { color: var(--text-muted); font-size: 12px; font-weight: 600; text-decoration: none; }
.header-nav a:hover { color: var(--brand); }
.header-actions { display: flex; align-items: center; gap: 8px; }
.brand:focus-visible { outline: 2px solid var(--focus-color); outline-offset: 4px; }
@media (max-width: 720px) { .brand-tagline, .header-nav { display: none; }.header-actions { margin-left: auto; }.app-header-inner { min-height: 72px; } }
</style>
