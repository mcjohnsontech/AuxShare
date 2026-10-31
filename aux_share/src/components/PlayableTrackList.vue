<template>
  <section class="playable-list" aria-labelledby="playable-heading">
    <div class="list-head">
      <div class="list-title">
        <p class="eyebrow">{{ playableCount }} of {{ pluralize(tracks.length, 'track') }} playable here</p>
        <h2 id="playable-heading">{{ canPlayInApp && playableCount > 0 ? 'Listen to the playlist' : 'Tracks in this playlist' }}</h2>
      </div>

      <div class="head-actions">
        <span class="target-chip">
          <PlatformMark :platform="targetPlatform" size="sm" />
          <span>{{ platform.name }}</span>
        </span>
        <span v-if="canPlayInApp && playableCount > 0" class="head-note">Start with any track</span>
      </div>
    </div>

    <p v-if="!canPlayInApp" class="platform-note">
      <Info :size="15" aria-hidden="true" />
      <span>
        {{ platform.playbackNote }} Use the open-link button on any track to listen there.
      </span>
    </p>
    <p v-else-if="playableCount === 0" class="platform-note is-warning">
      <Info :size="15" aria-hidden="true" />
      <span>This session has no playable media yet. Open a track on {{ platform.name }} instead.</span>
    </p>

    <ol class="rows">
      <TrackRow
        v-for="(track, index) in tracks"
        :key="`${trackKey(track, targetPlatform)}-${index}`"
        :track="track"
        :index="index + 1"
        :platform="targetPlatform"
        :active="activeKey === trackKey(track, targetPlatform)"
        :playing="isPlaying"
        :show-play="canPlayInApp && isTrackMatched(track, targetPlatform)"
        show-status
        :show-confidence="false"
        @play="$emit('play-track', track)"
      />
    </ol>

    <p class="list-footnote">
      <template v-if="platform.key === 'apple_music'">
        Previews are 30 seconds and supplied by Apple Music. The queue advances when a preview ends.
      </template>
      <template v-else-if="platform.key === 'youtube_music'">
        Playback uses the YouTube player. Some tracks may be unavailable due to regional rights.
      </template>
      <template v-else>
        Spotify playback is not available in the browser here. Tracks open in Spotify.
      </template>
    </p>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { Info } from 'lucide-vue-next'
import TrackRow from './TrackRow.vue'
import PlatformMark from './PlatformMark.vue'
import { canPlayTrack, getPlatform, isTrackMatched, trackKey } from '@/lib/platforms'
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
  activeKey: {
    type: String,
    default: '',
  },
  isPlaying: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['play-track'])

const platform = computed(() => getPlatform(props.targetPlatform))
const canPlayInApp = computed(() => platform.value.canPlayInApp)
const playableCount = computed(
  () => props.tracks.filter((track) => canPlayTrack(track, props.targetPlatform)).length,
)
</script>

<style scoped>
.playable-list {
  padding: clamp(18px, 3vw, 28px);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow);
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

.head-actions {
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

.head-note {
  color: var(--text-faint);
  font-size: var(--text-2xs);
  white-space: nowrap;
}

.platform-note {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  margin-bottom: var(--space-3);
  padding: 8px 10px;
  border: 1px solid var(--info-border);
  border-radius: var(--radius-sm);
  background: var(--info-bg);
  color: var(--blue-800);
  font-size: var(--text-xs);
}

.platform-note.is-warning {
  border-color: var(--warning-border);
  background: var(--warning-bg);
  color: var(--warning-strong);
}

.platform-note svg {
  flex: 0 0 auto;
  margin-top: 1px;
}

.rows {
  margin: 0;
  padding: 0;
  list-style: none;
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

  .head-actions {
    justify-content: flex-start;
    padding-top: 0;
  }
}

@media (max-width: 560px) {
  .playable-list {
    padding: var(--space-3);
  }
}
</style>
