<template>
  <section class="share-card" aria-labelledby="share-heading">
    <div class="share-head">
      <div class="share-title">
        <h2 id="share-heading">Share this playlist</h2>
        <p>Anyone with the link can open it — no account needed. The link expires after 24 hours.</p>
      </div>
      <span class="session-chip" :title="`Session code ${code}`">Session <strong>{{ code }}</strong></span>
    </div>

    <div class="share-actions">
      <a
        class="share-url"
        :href="displayUrl"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Open the shared playlist page in a new tab"
      >
        <Link2 :size="16" aria-hidden="true" />
        <span class="url-text">{{ displayUrl }}</span>
        <ExternalLink :size="14" class="url-ext" aria-hidden="true" />
      </a>

      <button
        type="button"
        class="copy-button"
        :class="{ 'is-copied': copyState === 'copied' }"
        @click="copyLink"
      >
        <Check v-if="copyState === 'copied'" :size="16" aria-hidden="true" />
        <Copy v-else :size="16" aria-hidden="true" />
        {{ copyLabel }}
      </button>
    </div>

    <p v-if="copyState === 'error'" class="copy-error">
      Copying was blocked by the browser. Select the link above and copy it manually.
    </p>

    <p class="sr-only" role="status" aria-live="polite">{{ announcement }}</p>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { Check, Copy, ExternalLink, Link2 } from 'lucide-vue-next'
import { useClipboard } from '@/composables/useClipboard'

const props = defineProps({
  code: {
    type: String,
    required: true,
  },
  shareUrl: {
    type: String,
    default: '',
  },
})

const { state: copyState, copy } = useClipboard()

const displayUrl = computed(() => {
  if (props.shareUrl) return props.shareUrl
  const origin = typeof window === 'undefined' ? '' : window.location.origin
  return `${origin}/join/${props.code}`
})

const copyLabel = computed(() => {
  if (copyState.value === 'copied') return 'Link copied'
  if (copyState.value === 'error') return 'Copy failed'
  return 'Copy link'
})

const announcement = computed(() => {
  if (copyState.value === 'copied') return 'Share link copied to the clipboard.'
  if (copyState.value === 'error') return 'The share link could not be copied.'
  return ''
})

function copyLink() {
  void copy(displayUrl.value)
}
</script>

<style scoped>
.share-card {
  padding: var(--space-4) var(--space-5);
  border: 1px solid var(--on-ink-line);
  border-radius: var(--radius-lg);
  background: var(--ink);
  color: var(--on-ink);
  box-shadow: var(--shadow-md);
}

.share-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-3);
}

.share-title h2 {
  color: var(--on-ink);
  font-size: var(--text-md);
  letter-spacing: var(--tracking-tight);
}

.share-title p {
  max-width: 54ch;
  margin-top: 3px;
  color: var(--on-ink-muted);
  font-size: var(--text-xs);
}

.session-chip {
  flex: 0 0 auto;
  padding: 3px 9px;
  border: 1px solid var(--on-ink-line);
  border-radius: var(--radius-pill);
  color: var(--on-ink-muted);
  font-size: var(--text-2xs);
  white-space: nowrap;
}

.session-chip strong {
  margin-left: 2px;
  color: var(--on-ink);
  font-family: var(--font-mono);
  font-weight: var(--weight-semibold);
  letter-spacing: 0.02em;
}

.share-actions {
  display: flex;
  align-items: stretch;
  gap: var(--space-2);
}

.share-url {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1 1 auto;
  min-width: 0;
  padding: 9px 12px;
  border: 1px solid var(--on-ink-line);
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.06);
  color: var(--on-ink);
  font-size: var(--text-sm);
  text-decoration: none;
  transition:
    background var(--dur-1) var(--ease-out),
    border-color var(--dur-1) var(--ease-out);
}

.share-url:hover {
  background: rgba(255, 255, 255, 0.11);
  border-color: #35456b;
}

.share-url:focus-visible {
  outline: 2px solid #9db9ff;
  outline-offset: 2px;
}

.url-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.url-ext {
  flex: 0 0 auto;
  margin-left: auto;
  color: var(--on-ink-muted);
}

.copy-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  flex: 0 0 auto;
  min-height: 40px;
  padding: 0 16px;
  border: 1px solid var(--blue-300);
  border-radius: var(--radius-sm);
  background: var(--blue-600);
  color: #fff;
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  transition:
    background var(--dur-1) var(--ease-out),
    border-color var(--dur-1) var(--ease-out);
}

.copy-button:hover {
  background: var(--blue-700);
  border-color: #b9cdff;
}

.copy-button.is-copied {
  background: #146c43;
  border-color: #4fae82;
}

.copy-button:focus-visible {
  outline: 2px solid #9db9ff;
  outline-offset: 2px;
}

.copy-error {
  margin-top: var(--space-2);
  color: #ffb4ab;
  font-size: var(--text-xs);
}

@media (max-width: 640px) {
  .share-card {
    padding: var(--space-4);
  }

  .share-head {
    flex-direction: column;
    gap: var(--space-2);
  }

  .share-actions {
    flex-direction: column;
  }

  .copy-button {
    min-height: 44px;
  }
}
</style>
