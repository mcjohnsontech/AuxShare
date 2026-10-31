<template>
  <section class="track-list" aria-labelledby="tracks-heading">
    <div class="list-head">
      <div class="list-title">
        <p class="eyebrow">{{ pluralize(tracks.length, 'track') }} in this playlist</p>
        <h2 id="tracks-heading">Converted tracks</h2>
      </div>

      <div class="list-tools">
        <span class="target-chip">
          <PlatformMark :platform="targetPlatform" size="sm" />
          <span>{{ platform.name }}</span>
        </span>

        <div v-if="failedCount > 0" class="filters" role="group" aria-label="Filter the track list">
          <button
            v-for="option in filterOptions"
            :key="option.value"
            type="button"
            class="filter-button"
            :class="{ 'is-active': filter === option.value }"
            :aria-pressed="filter === option.value"
            @click="filter = option.value"
          >
            {{ option.label }}
            <span class="filter-count tabular">{{ option.count }}</span>
          </button>
        </div>
      </div>
    </div>

    <ol v-if="visibleTracks.length" class="rows">
      <TrackRow
        v-for="entry in visibleTracks"
        :key="`${trackKey(entry.track, targetPlatform)}-${entry.index}`"
        :track="entry.track"
        :index="entry.index + 1"
        :platform="targetPlatform"
        show-status
      />
    </ol>

    <p v-else class="empty-filter">
      {{ emptyMessage }}
    </p>

    <p class="list-footnote">
      Track titles open the matched song on {{ platform.name }} in a new tab when the service supplies a link.
    </p>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import TrackRow from './TrackRow.vue'
import PlatformMark from './PlatformMark.vue'
import { getPlatform, isTrackMatched, trackKey } from '@/lib/platforms'
import { pluralize } from '@/lib/format'

const props = defineProps({
  tracks: {
    type: Array,
    required: true,
  },
  targetPlatform: {
    type: String,
    required: true,
  },
})

const filter = ref('all')
const platform = computed(() => getPlatform(props.targetPlatform))

const matchedCount = computed(
  () => props.tracks.filter((track) => isTrackMatched(track, props.targetPlatform)).length,
)
const failedCount = computed(() => props.tracks.length - matchedCount.value)

const filterOptions = computed(() => [
  { value: 'all', label: 'All', count: props.tracks.length },
  { value: 'matched', label: 'Matched', count: matchedCount.value },
  { value: 'unmatched', label: 'Not found', count: failedCount.value },
])

const visibleTracks = computed(() => {
  const entries = props.tracks.map((track, index) => ({ track, index }))
  if (filter.value === 'matched') {
    return entries.filter((entry) => isTrackMatched(entry.track, props.targetPlatform))
  }
  if (filter.value === 'unmatched') {
    return entries.filter((entry) => !isTrackMatched(entry.track, props.targetPlatform))
  }
  return entries
})

const emptyMessage = computed(() => {
  if (!props.tracks.length) return 'No tracks were saved with this conversion.'
  if (filter.value === 'matched') return 'No tracks matched on this service.'
  if (filter.value === 'unmatched') return 'No unmatched tracks — everything was found.'
  return 'No tracks to show.'
})
</script>

<style scoped>
.track-list {
  padding: var(--space-4);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow-xs);
}

.list-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-3);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--divider);
}

.eyebrow {
  margin-bottom: 2px;
  color: var(--text-faint);
  font-size: var(--text-2xs);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
}

.list-title h2 {
  font-size: var(--text-lg);
}

.list-tools {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-2);
  padding-top: 2px;
}

.target-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 9px 3px 4px;
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  background: var(--surface-2);
  color: var(--text-muted);
  font-size: var(--text-2xs);
  font-weight: var(--weight-semibold);
  white-space: nowrap;
}

.filters {
  display: inline-flex;
  padding: 2px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
}

.filter-button {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 9px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  transition:
    background var(--dur-1) var(--ease-out),
    color var(--dur-1) var(--ease-out);
}

.filter-button:hover {
  color: var(--text);
}

.filter-button.is-active {
  background: var(--surface);
  color: var(--text);
  box-shadow: var(--shadow-xs);
}

.filter-button:focus-visible {
  outline: 2px solid var(--focus-color);
  outline-offset: 1px;
}

.filter-count {
  color: var(--text-faint);
  font-weight: var(--weight-regular);
  font-variant-numeric: tabular-nums;
}

.rows {
  margin: 0;
  padding: 0;
  list-style: none;
}

.empty-filter {
  padding: var(--space-6) var(--space-4);
  color: var(--text-muted);
  font-size: var(--text-sm);
  text-align: center;
}

.list-footnote {
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--divider);
  color: var(--text-faint);
  font-size: var(--text-2xs);
}

@media (max-width: 720px) {
  .list-head {
    flex-direction: column;
    gap: var(--space-3);
  }

  .list-tools {
    justify-content: flex-start;
    padding-top: 0;
  }

  .filters {
    max-width: 100%;
    overflow-x: auto;
  }
}

@media (max-width: 560px) {
  .track-list {
    padding: var(--space-3);
  }
}
</style>
