<template>
  <section v-if="stats" class="match-stats" aria-label="Match summary">
    <div class="summary">
      <div class="rate-block">
        <p class="rate tabular">{{ rateLabel }}</p>
        <p class="rate-caption">{{ matchedLabel }}</p>
      </div>

      <div class="bar-block">
        <div
          class="match-bar"
          role="img"
          :aria-label="barLabel"
        >
          <span class="bar-matched" :style="{ width: `${matchedShare}%` }"></span>
          <span class="bar-missing" :style="{ width: `${missingShare}%` }"></span>
        </div>
        <p class="bar-caption">
          <span class="key key-matched" aria-hidden="true"></span>Matched
          <span class="key key-missing" aria-hidden="true"></span>Not found
        </p>
      </div>
    </div>

    <dl class="metrics">
      <div class="metric">
        <dt>Matched</dt>
        <dd class="tabular">{{ safeMatched }}</dd>
      </div>
      <div class="metric" :class="{ 'has-missing': safeFailed > 0 }">
        <dt>Not found</dt>
        <dd class="tabular">{{ safeFailed }}</dd>
      </div>
      <div class="metric">
        <dt>Total</dt>
        <dd class="tabular">{{ safeTotal }}</dd>
      </div>
      <div v-if="avgConfidenceLabel" class="metric">
        <dt>Avg. confidence</dt>
        <dd class="tabular">{{ avgConfidenceLabel }}</dd>
      </div>
    </dl>

    <p v-if="confidenceBreakdown" class="confidence-line">
      Confidence: {{ confidenceBreakdown }}
    </p>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { pluralize, toPercent } from '@/lib/format'

const props = defineProps({
  stats: {
    type: Object,
    default: null,
  },
})

const safeTotal = computed(() => numberOrZero(props.stats?.total))
const safeMatched = computed(() => numberOrZero(props.stats?.matched))
const safeFailed = computed(() => numberOrZero(props.stats?.failed))

const ratePercent = computed(() => {
  const fromStats = toPercent(props.stats?.match_rate)
  if (fromStats !== null) return fromStats
  if (safeTotal.value === 0) return 0
  return Math.round((safeMatched.value / safeTotal.value) * 100)
})

const rateLabel = computed(() => `${ratePercent.value}%`)
const matchedLabel = computed(
  () => `${safeMatched.value} of ${pluralize(safeTotal.value, 'track')} matched`,
)

const matchedShare = computed(() =>
  safeTotal.value === 0 ? 0 : (safeMatched.value / safeTotal.value) * 100,
)
const missingShare = computed(() =>
  safeTotal.value === 0 ? 0 : (safeFailed.value / safeTotal.value) * 100,
)

const barLabel = computed(
  () => `${safeMatched.value} matched and ${safeFailed.value} not found out of ${pluralize(safeTotal.value, 'track')}.`,
)

const avgConfidenceLabel = computed(() => {
  if (safeMatched.value === 0) return ''
  return toPercent(props.stats?.avg_confidence) === null
    ? ''
    : `${toPercent(props.stats.avg_confidence)}%`
})

const confidenceBreakdown = computed(() => {
  if (safeMatched.value === 0) return ''
  const high = numberOrZero(props.stats?.high_confidence)
  const medium = numberOrZero(props.stats?.medium_confidence)
  const low = numberOrZero(props.stats?.low_confidence)
  if (high + medium + low === 0) return ''
  const parts = []
  if (high) parts.push(`${high} high`)
  if (medium) parts.push(`${medium} medium`)
  if (low) parts.push(`${low} low`)
  return parts.join(' · ')
})

function numberOrZero(value) {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0
}
</script>

<style scoped>
.match-stats {
  padding: clamp(18px, 3vw, 28px);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow);
}

.summary {
  display: flex;
  align-items: center;
  gap: var(--space-5);
}

.rate-block {
  flex: 0 0 auto;
  min-width: 132px;
}

.rate {
  color: var(--text);
  font-size: 42px;
  font-weight: var(--weight-bold);
  letter-spacing: var(--tracking-display);
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.rate-caption {
  margin-top: 5px;
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.bar-block {
  flex: 1 1 auto;
  min-width: 0;
}

.match-bar {
  display: flex;
  width: 100%;
  height: 8px;
  overflow: hidden;
  border-radius: var(--radius-pill);
  background: var(--warning-bg);
  border: 1px solid var(--warning-border);
}

.bar-matched {
  height: 100%;
  background: var(--success);
}

.bar-missing {
  height: 100%;
  background:
    repeating-linear-gradient(
      -45deg,
      var(--warning-border) 0 4px,
      transparent 4px 8px
    ),
    var(--warning-bg);
}

.bar-caption {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 7px;
  color: var(--text-faint);
  font-size: var(--text-2xs);
  font-weight: var(--weight-medium);
}

.key {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}

.key-matched {
  background: var(--success);
}

.key-missing {
  margin-left: 10px;
  border: 1px solid var(--warning-border);
  background: var(--warning-bg);
}

.metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-2);
  margin: var(--space-4) 0 0;
  padding-top: var(--space-3);
  border-top: 1px solid var(--divider);
}

.metric {
  min-width: 0;
}

.metric dt {
  color: var(--text-faint);
  font-size: var(--text-2xs);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
}

.metric dd {
  margin: 2px 0 0;
  color: var(--text);
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
}

.metric.has-missing dd {
  color: var(--warning-strong);
}

.confidence-line {
  margin-top: var(--space-2);
  color: var(--text-faint);
  font-size: var(--text-xs);
}

@media (max-width: 640px) {
  .summary {
    flex-direction: column;
    align-items: stretch;
    gap: var(--space-3);
  }

  .rate-block {
    display: flex;
    align-items: baseline;
    gap: var(--space-2);
  }

  .rate {
    font-size: var(--text-xl);
  }

  .rate-caption {
    margin: 0;
  }

  .metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    row-gap: var(--space-3);
  }
}
</style>
