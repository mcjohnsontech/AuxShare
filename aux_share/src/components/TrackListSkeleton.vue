<template>
  <div class="track-skeleton" aria-busy="true">
    <p class="sr-only" role="status">Loading the converted tracks…</p>
    <div v-for="row in rows" :key="row" class="skeleton-row" aria-hidden="true">
      <span class="bone bone-index"></span>
      <span class="bone bone-art"></span>
      <span class="bone-lines">
        <span class="bone bone-title" :style="{ width: titleWidth(row) }"></span>
        <span class="bone bone-meta" :style="{ width: metaWidth(row) }"></span>
      </span>
      <span class="bone bone-action"></span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  rows: {
    type: Number,
    default: 7,
  },
})

function titleWidth(row) {
  return `${58 - ((row * 13) % 22)}%`
}

function metaWidth(row) {
  return `${34 - ((row * 7) % 14)}%`
}
</script>

<style scoped>
.track-skeleton {
  padding: var(--space-2) 0;
}

.skeleton-row {
  display: grid;
  grid-template-columns: 28px 44px minmax(0, 1fr) 36px;
  align-items: center;
  gap: var(--space-3);
  padding: 11px var(--space-2);
}

.skeleton-row + .skeleton-row {
  box-shadow: inset 0 1px 0 var(--divider);
}

.bone {
  display: block;
  height: 12px;
  border-radius: var(--radius-pill);
  background: linear-gradient(
    100deg,
    var(--surface-2) 20%,
    var(--surface-3) 40%,
    var(--surface-2) 60%
  );
  background-size: 220% 100%;
  animation: skeleton-shimmer 1.4s var(--ease-in-out) infinite;
}

.bone-index {
  width: 14px;
  height: 9px;
}

.bone-art {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-sm);
}

.bone-lines {
  display: flex;
  flex-direction: column;
  gap: 7px;
  min-width: 0;
}

.bone-title {
  height: 13px;
}

.bone-meta {
  height: 10px;
}

.bone-action {
  width: 30px;
  height: 30px;
  border-radius: var(--radius-sm);
}

@keyframes skeleton-shimmer {
  0% {
    background-position: 100% 0;
  }
  100% {
    background-position: -100% 0;
  }
}

@media (max-width: 560px) {
  .skeleton-row {
    grid-template-columns: 22px 40px minmax(0, 1fr) 34px;
    gap: 10px;
  }

  .bone-art {
    width: 40px;
    height: 40px;
  }
}
</style>
