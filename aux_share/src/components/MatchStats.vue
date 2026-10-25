<!-- src/components/MatchStats.vue -->

<template>
  <div v-if="stats" class="match-stats">
    <div class="section-heading">
      <div>
        <p class="eyebrow">Conversion complete</p>
        <h3>Your match report</h3>
      </div>
      <span class="rate">{{ (stats.match_rate * 100).toFixed(0) }}% match rate</span>
    </div>
    
    <div class="stats-grid">
      <div class="stat-card primary">
        <div class="stat-value">{{ stats.matched }}</div>
        <div class="stat-label">Matched</div>
      </div>
      <div class="stat-card warning" v-if="stats.failed">
        <div class="stat-value">{{ stats.failed }}</div>
        <div class="stat-label">Needs attention</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">Total songs</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ (stats.avg_confidence * 100).toFixed(0) }}%</div>
        <div class="stat-label">Avg Confidence</div>
      </div>
    </div>

    <!-- Progress bar -->
    <div class="progress-bar">
      <div 
        class="progress-fill" 
        :style="{ width: (stats.match_rate * 100) + '%' }"
      ></div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  stats: {
    type: Object,
    required: true
  }
})
</script>

<style scoped>
.match-stats {
  margin: 16px 0;
  padding: 24px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow);
}
.section-heading { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 20px; }
.eyebrow { margin: 0 0 4px; color: var(--blue-500); font-size: 12px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
h3 { margin: 0; color: var(--text); font-size: 20px; }
.rate { padding: 6px 10px; border-radius: var(--radius-pill); background: var(--success-bg); color: var(--success); font-size: 12px; font-weight: 700; white-space: nowrap;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
  margin-bottom: 18px;
}

.stat-card {
  padding: 14px 10px;
  background: var(--bg-subtle);
  border-radius: var(--radius-sm);
  text-align: center;
  border: 1px solid var(--border);
}
.stat-card.primary {
  background: var(--blue-50);
  border-color: var(--blue-100);
}
.stat-card.warning {
  background: var(--warning-bg);
  border-color: #f2dfac;
}
.stat-value {
  font-size: 1.65rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 5px;
}
.stat-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}
.progress-bar {
  width: 100%;
  height: 8px;
  background: var(--blue-100);
  border-radius: 6px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: var(--blue-500);
  transition: width 250ms ease-out;
}
@media (max-width: 520px) {
  .section-heading { flex-direction: column; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>