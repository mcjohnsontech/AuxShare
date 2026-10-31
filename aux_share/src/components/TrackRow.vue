<template>
  <li
    class="track-row"
    :class="{
      'is-active': active,
      'is-playing': active && playing,
      'is-unmatched': !matched,
      'is-compact': compact,
    }"
    :aria-current="active ? 'true' : undefined"
  >
    <div class="lead" aria-hidden="true">
      <span v-if="active" class="eq-bars" :class="{ 'is-paused': !playing }">
        <span></span><span></span><span></span><span></span>
      </span>
      <span v-else-if="typeof index === 'number'" class="index tabular">{{ index }}</span>
      <Music2 v-else :size="14" />
    </div>

    <div class="art">
      <img
        v-if="artworkUrl && !artworkFailed"
        :src="artworkUrl"
        alt=""
        loading="lazy"
        decoding="async"
        width="44"
        height="44"
        @error="artworkFailed = true"
      />
      <span v-else class="art-fallback" aria-hidden="true">
        <Music2 :size="18" />
      </span>
    </div>

    <div class="main">
      <div class="title-line">
        <a
          v-if="url"
          :href="url"
          target="_blank"
          rel="noopener noreferrer"
          class="title"
          :title="`${title} — opens on ${platform.name}`"
        >{{ title }}</a>
        <span v-else class="title" :title="title">{{ title }}</span>
        <ExternalLink v-if="url" :size="12" class="ext-icon" aria-hidden="true" />
      </div>

      <p class="meta">
        <span class="artist">{{ artist }}</span>
        <template v-if="album">
          <span class="sep" aria-hidden="true">·</span>
          <span class="album">{{ album }}</span>
        </template>
        <template v-if="duration">
          <span class="sep" aria-hidden="true">·</span>
          <span class="duration tabular">{{ duration }}</span>
        </template>
      </p>

      <p v-if="showStatus" class="status-line">
        <span class="badge" :class="matched ? 'badge-success' : 'badge-danger'">
          <Check v-if="matched" :size="12" aria-hidden="true" />
          <Minus v-else :size="12" aria-hidden="true" />
          {{ matched ? 'Matched' : `Not on ${platform.name}` }}
        </span>
        <span v-if="matched && showConfidence && confidencePercent !== null" class="quality">
          {{ confidencePercent }}% · {{ confidenceLabel }}
        </span>
        <span v-else-if="matched && methodLabel" class="quality">{{ methodLabel }}</span>
      </p>
    </div>

    <div class="actions">
      <a
        v-if="url"
        :href="url"
        target="_blank"
        rel="noopener noreferrer"
        class="icon-button"
        :aria-label="`Open ${title} on ${platform.name} in a new tab`"
      >
        <ExternalLink :size="16" aria-hidden="true" />
      </a>

      <button
        v-if="showPlay"
        type="button"
        class="icon-button play-button"
        :disabled="!playable"
        :aria-label="playButtonLabel"
        @click="$emit('play', track)"
      >
        <Pause v-if="active && playing" :size="16" aria-hidden="true" />
        <Play v-else :size="16" aria-hidden="true" />
      </button>
    </div>
  </li>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Check, ExternalLink, Minus, Music2, Pause, Play } from 'lucide-vue-next'
import {
  canPlayTrack,
  getPlatform,
  isTrackMatched,
  trackConfidence,
  trackMatchMethod,
  trackUrl,
} from '@/lib/platforms'
import { formatDuration } from '@/lib/format'

const props = defineProps({
  track: {
    type: Object,
    required: true,
  },
  index: {
    type: Number,
    default: null,
  },
  platform: {
    type: String,
    required: true,
  },
  active: {
    type: Boolean,
    default: false,
  },
  playing: {
    type: Boolean,
    default: false,
  },
  showPlay: {
    type: Boolean,
    default: false,
  },
  showStatus: {
    type: Boolean,
    default: true,
  },
  showConfidence: {
    type: Boolean,
    default: true,
  },
  compact: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['play'])

const platform = computed(() => getPlatform(props.platform))
const title = computed(() => props.track.title || 'Untitled track')
const artist = computed(() => props.track.artist || props.track.artists?.join(', ') || 'Unknown artist')
const album = computed(() => props.track.album || '')
const duration = computed(() => formatDuration(props.track.duration_ms))
const url = computed(() => trackUrl(props.track, props.platform))
const matched = computed(() => isTrackMatched(props.track, props.platform))
const playable = computed(() => canPlayTrack(props.track, props.platform))

const artworkUrl = computed(() => {
  const candidate =
    props.track.artwork_url ||
    props.track.album_art ||
    props.track.image_url ||
    ''
  return typeof candidate === 'string' && /^https?:\/\//i.test(candidate) ? candidate : ''
})

const artworkFailed = ref(false)
watch(artworkUrl, () => {
  artworkFailed.value = false
})

const confidence = computed(() => trackConfidence(props.track, props.platform))
const confidencePercent = computed(() =>
  confidence.value === null ? null : Math.round(confidence.value * 100),
)
const confidenceLabel = computed(() => {
  if (confidence.value === null) return ''
  if (confidence.value >= 0.85) return 'High confidence'
  if (confidence.value >= 0.7) return 'Medium confidence'
  return 'Low confidence'
})

const methodLabel = computed(() => {
  const raw = trackMatchMethod(props.track, props.platform)
  if (!raw) return ''
  const labels = {
    isrc: 'ISRC match',
    metadata: 'Metadata match',
    fuzzy: 'Fuzzy match',
    search: 'Search match',
  }
  return labels[raw] || raw.replace(/[_-]+/g, ' ')
})

const playButtonLabel = computed(() => {
  if (!playable.value) return `${title.value} is not playable here`
  if (props.active && props.playing) return `Pause ${title.value}`
  return `Play ${title.value}`
})
</script>

<style scoped>
.track-row {
  display: grid;
  grid-template-columns: 28px 44px minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-3);
  padding: 10px var(--space-2);
  border-radius: var(--radius-md);
  list-style: none;
  transition: background var(--dur-1) var(--ease-out);
}

.track-row + .track-row {
  box-shadow: inset 0 1px 0 var(--divider);
}

.track-row:hover {
  background: var(--surface-2);
}

.track-row.is-active {
  background: var(--blue-50);
  box-shadow: none;
}

.track-row.is-active + .track-row {
  box-shadow: none;
}

.lead {
  display: grid;
  place-items: center;
  color: var(--text-faint);
  font-size: var(--text-sm);
  font-variant-numeric: tabular-nums;
}

.is-active .lead {
  color: var(--blue-600);
}

.index {
  min-width: 1.6ch;
  text-align: right;
}

.art {
  position: relative;
  width: 44px;
  height: 44px;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
}

.art img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.art-fallback {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  color: #fff;
  background: radial-gradient(ellipse at 95% 0%, #ffd7a1, #f7a16a 20%, transparent 60%), linear-gradient(140deg, #91b8ff, #2452ff);
}

.main {
  min-width: 0;
}

.title-line {
  display: flex;
  align-items: center;
  gap: 5px;
  min-width: 0;
}

.title {
  overflow: hidden;
  color: var(--text);
  font-size: var(--text-base);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--tracking-tight);
  text-decoration: none;
  text-overflow: ellipsis;
  white-space: nowrap;
}

a.title:hover {
  color: var(--blue-600);
  text-decoration: underline;
}

a.title:focus-visible {
  outline: 2px solid var(--focus-color);
  outline-offset: 2px;
  border-radius: 2px;
}

.ext-icon {
  flex: 0 0 auto;
  color: var(--text-faint);
}

.meta {
  overflow: hidden;
  margin-top: 1px;
  color: var(--text-muted);
  font-size: var(--text-sm);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sep {
  padding: 0 5px;
  color: var(--text-faint);
}

.album {
  color: var(--text-faint);
}

.duration {
  color: var(--text-faint);
  font-variant-numeric: tabular-nums;
}

.status-line {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: 5px;
}

.is-unmatched .title {
  color: var(--text-muted);
}

.quality {
  color: var(--text-faint);
  font-size: var(--text-2xs);
  font-weight: var(--weight-medium);
}

.actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.icon-button {
  display: inline-grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  text-decoration: none;
  transition:
    background var(--dur-1) var(--ease-out),
    color var(--dur-1) var(--ease-out),
    border-color var(--dur-1) var(--ease-out);
}

.icon-button:hover {
  border-color: var(--border);
  background: var(--surface);
  color: var(--text);
}

.icon-button:focus-visible {
  outline: 2px solid var(--focus-color);
  outline-offset: 2px;
}

.play-button {
  color: var(--blue-700);
  background: var(--surface);
  border-color: var(--border);
}

.play-button:hover:not(:disabled) {
  background: var(--blue-50);
  border-color: var(--blue-200);
  color: var(--blue-700);
}

.is-active .play-button {
  background: var(--blue-600);
  border-color: var(--blue-600);
  color: #fff;
}

.play-button:disabled {
  opacity: 0.45;
  background: transparent;
  border-color: transparent;
}

@media (max-width: 560px) {
  .track-row {
    grid-template-columns: 22px 40px minmax(0, 1fr) auto;
    gap: 10px;
    padding: 10px 6px;
  }

  .art {
    width: 40px;
    height: 40px;
  }

  .album,
  .sep:has(+ .album) {
    display: none;
  }

  .quality {
    display: none;
  }

  .icon-button {
    width: 40px;
    height: 40px;
  }
}
</style>
