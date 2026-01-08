<!-- src/components/MatchStats.vue -->

<template>
  <div v-if="stats" class="match-stats">
    <h3>📊 Match Statistics</h3>
    
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">Total Tracks</div>
      </div>
      
      <div class="stat-card success">
        <div class="stat-value">{{ stats.matched }}</div>
        <div class="stat-label">Matched</div>
      </div>
      
      <div class="stat-card warning" v-if="stats.failed">
        <div class="stat-value">{{ stats.failed }}</div>
        <div class="stat-label">Not Found</div>
      </div>
      
      <div class="stat-card">
        <div class="stat-value">{{ (stats.match_rate * 100).toFixed(1) }}%</div>
        <div class="stat-label">Match Rate</div>
      </div>
      
      <div class="stat-card">
        <div class="stat-value">{{ (stats.avg_confidence * 100).toFixed(1) }}%</div>
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
  margin: 30px 0;
  padding: 25px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

h3 {
  margin-bottom: 20px;
  color: #333;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.stat-card {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
  text-align: center;
  border: 2px solid transparent;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.stat-card.success {
  background: #d4edda;
  border-color: #28a745;
}

.stat-card.warning {
  background: #fff3cd;
  border-color: #ffc107;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #333;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 0.9rem;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.progress-bar {
  width: 100%;
  height: 12px;
  background: #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transition: width 1s ease;
}
</style>