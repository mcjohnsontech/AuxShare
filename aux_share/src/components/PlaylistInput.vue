<template>
  <section class="converter" aria-labelledby="converter-heading">
    <div class="converter-head">
      <p class="eyebrow">YOUR NEXT SHARED MIX</p>
      <h2 id="converter-heading">Start with a link.</h2>
      <p class="converter-intro">Their next favorite song might already be in your playlist.</p>
    </div>

    <form novalidate @submit.prevent="handleSubmit">
      <div class="step">
        <div class="step-head">
          <span class="step-number" aria-hidden="true">1</span>
          <div>
            <h3>Playlist link</h3>
            <p>Public Spotify or YouTube Music playlists.</p>
          </div>
        </div>

        <label class="field-label" for="playlist-url">Playlist URL</label>
        <div class="url-field" :class="{ 'is-invalid': validationError, 'is-valid': detected }">
          <Link2 :size="17" class="url-icon" aria-hidden="true" />
          <input
            id="playlist-url"
            ref="urlInput"
            v-model="playlistUrl"
            type="text"
            inputmode="url"
            autocomplete="url"
            autocapitalize="off"
            spellcheck="false"
            placeholder="https://open.spotify.com/playlist/…"
            :disabled="busy"
            aria-required="true"
            :aria-invalid="validationError ? 'true' : 'false'"
            :aria-describedby="describedBy"
            @input="onInput"
          />
          <button
            v-if="playlistUrl && !busy"
            type="button"
            class="clear-button"
            aria-label="Clear the playlist link"
            @click="clearUrl"
          >
            <X :size="15" aria-hidden="true" />
          </button>
        </div>

        <p v-if="detected" class="field-note is-detected" role="status" aria-live="polite">
          <PlatformMark :platform="detected" size="sm" />
          {{ detectedName }} playlist detected
        </p>
        <p v-else class="field-note">
          Share → Copy link to playlist. Make sure it is public.
        </p>

        <p v-if="validationError" id="url-error" class="field-error" role="alert">
          <AlertCircle :size="15" aria-hidden="true" />
          <span>{{ validationError }}</span>
        </p>

        <details class="link-help">
          <summary>Where do I find this?</summary>
          <ul>
            <li><strong>Spotify:</strong> open the playlist → ··· → Share → Copy link to playlist.</li>
            <li><strong>YouTube Music:</strong> open the playlist → Share → Copy link.</li>
          </ul>
        </details>
      </div>

      <div class="step">
        <div class="step-head">
          <span class="step-number" aria-hidden="true">2</span>
          <div>
            <h3>Destination</h3>
            <p>We find the closest match in that catalogue.</p>
          </div>
        </div>
        <PlatformSelector v-model="targetPlatform" />
      </div>

      <button type="submit" class="submit-button" :disabled="!canSubmit" :aria-busy="busy">
        <Loader2 v-if="busy" class="spin" :size="18" aria-hidden="true" />
        <span>{{ busy ? 'Converting playlist…' : 'Convert & share' }}</span>
        <ArrowRight v-if="!busy" :size="18" aria-hidden="true" />
      </button>

      <div v-if="busy" class="conversion-progress" role="status" aria-live="polite">
        <span class="eq-bars" aria-hidden="true"><span></span><span></span><span></span><span></span></span>
        <div>
          <p class="progress-title">{{ stageLabel }}</p>
          <p class="progress-note">Large playlists can take up to a minute. Keep this tab open.</p>
        </div>
      </div>

      <div v-if="submitError" class="submit-error" role="alert">
        <AlertCircle :size="17" aria-hidden="true" />
        <div>
          <p class="submit-error-title">That conversion did not finish</p>
          <p class="submit-error-text">{{ submitError }}</p>
        </div>
      </div>

      <p class="assurance">
        <ShieldCheck :size="14" aria-hidden="true" />
        Public links only. Your source playlist is never modified. No account needed.
      </p>
    </form>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import {
  AlertCircle,
  ArrowRight,
  Link2,
  Loader2,
  ShieldCheck,
  X,
} from 'lucide-vue-next'
import PlatformSelector from './PlatformSelector.vue'
import PlatformMark from './PlatformMark.vue'
import { usePlaylistStore } from '@/stores/playlist'
import { classifyPlaylistUrl, getPlatform } from '@/lib/platforms'

const emit = defineEmits(['converted'])

const playlistStore = usePlaylistStore()

const playlistUrl = ref('')
const targetPlatform = ref('apple_music')
const urlInput = ref(null)
const validationError = ref('')
const submitError = ref('')
const detected = ref(null)
const stageIndex = ref(0)

let stageTimer = null

const busy = computed(() => playlistStore.loading)
const detectedName = computed(() => getPlatform(detected.value).name)

const canSubmit = computed(
  () => !busy.value && playlistUrl.value.trim().length > 0 && Boolean(targetPlatform.value),
)

const describedBy = computed(() => {
  const ids = []
  if (validationError.value) ids.push('url-error')
  return ids.length ? ids.join(' ') : undefined
})

const STAGES = computed(() => [
  'Fetching the playlist from your source service…',
  `Matching tracks on ${getPlatform(targetPlatform.value).name}…`,
  'Preparing your results…',
])

const stageLabel = computed(() => STAGES.value[Math.min(stageIndex.value, STAGES.value.length - 1)])

function onInput() {
  if (validationError.value) validationError.value = ''
  if (submitError.value) submitError.value = ''
  detected.value = classifyPlaylistUrl(playlistUrl.value).platform
}

function clearUrl() {
  playlistUrl.value = ''
  detected.value = null
  validationError.value = ''
  submitError.value = ''
  urlInput.value?.focus()
}

function startStages() {
  stageIndex.value = 0
  stopStages()
  stageTimer = setInterval(() => {
    if (stageIndex.value < STAGES.value.length - 1) stageIndex.value += 1
  }, 9000)
}

function stopStages() {
  if (stageTimer) {
    clearInterval(stageTimer)
    stageTimer = null
  }
}

function friendlyError(error) {
  const status = error?.response?.status
  const detail = error?.response?.data?.detail

  if (!error?.response) {
    if (error?.code === 'ECONNABORTED') {
      return 'The conversion took too long to finish. Try again — very large playlists can take over a minute.'
    }
    return 'We could not reach the AuxShare server. Check your connection and try again.'
  }

  if (status === 429) {
    return 'Too many conversions from this network. Wait a moment and try again.'
  }
  if (status === 503) {
    return 'Playlist storage is temporarily unavailable. Please try again in a moment.'
  }
  if (status && status < 500 && typeof detail === 'string' && detail.trim()) {
    return detail
  }
  return 'Something went wrong while converting that playlist. Try again, or try a different playlist.'
}

async function handleSubmit() {
  if (busy.value) return

  const result = classifyPlaylistUrl(playlistUrl.value)
  if (result.error) {
    validationError.value = result.error
    urlInput.value?.focus()
    return
  }

  validationError.value = ''
  submitError.value = ''
  playlistStore.error = null
  startStages()

  try {
    await playlistStore.convertPlaylist(result.url, targetPlatform.value)
    emit('converted')
  } catch (error) {
    submitError.value = friendlyError(error)
  } finally {
    stopStages()
  }
}

onBeforeUnmount(stopStages)

defineExpose({
  focusUrl: () => urlInput.value?.focus(),
})
</script>

<style scoped>
.converter {
  padding: 32px;
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  background: var(--surface);
  box-shadow: 0 4px 8px #49341a03, 0 24px 64px -28px #49341a26;
}

.converter-head {
  margin-bottom: 28px;
}

.eyebrow {
  margin-bottom: 4px;
  color: var(--blue-700);
  font-size: var(--text-2xs);
  font-weight: var(--weight-bold);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
}

.converter-head h2 {
  margin-top: 10px;
  font-size: 32px;
  font-weight: 800;
  letter-spacing: var(--tracking-tight);
}

.converter-intro { margin-top: 10px; color: var(--text-muted); font-size: 13px; line-height: 1.65; max-width: 34ch; }

.step + .step {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--divider);
}

.step-head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: var(--space-3);
}

.step-number {
  display: grid;
  place-items: center;
  flex: 0 0 25px;
  height: 25px;
  margin-top: 1px;
  border-radius: 50%;
  background: var(--blue-50);
  color: var(--blue-700);
  font-size: var(--text-2xs);
  font-weight: var(--weight-bold);
}

.step-head h3 {
  font-size: var(--text-base);
  letter-spacing: 0;
}

.step-head p {
  margin-top: 1px;
  color: var(--text-muted);
  font-size: var(--text-xs);
}

.field-label {
  display: block;
  margin-bottom: 5px;
  color: var(--text);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
}

.url-field {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 8px 0 12px;
  border: 1px solid var(--border-strong);
  border-radius: 12px;
  background: var(--bg);
  transition:
    border-color var(--dur-1) var(--ease-out),
    box-shadow var(--dur-1) var(--ease-out);
}

.url-field:focus-within {
  border-color: var(--blue-500);
  box-shadow: 0 0 0 3px var(--blue-100);
}

.url-field.is-invalid {
  border-color: var(--danger);
  box-shadow: 0 0 0 3px var(--danger-bg);
}

.url-icon {
  flex: 0 0 auto;
  color: var(--text-faint);
}

.url-field input {
  flex: 1 1 auto;
  width: 100%;
  min-width: 0;
  height: 42px;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--text);
  font-size: var(--text-sm);
}

.url-field input:focus {
  outline: none;
}

.url-field input::placeholder {
  color: var(--text-faint);
}

.url-field input:disabled {
  color: var(--text-muted);
}

.clear-button {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: var(--radius-xs);
  background: transparent;
  color: var(--text-faint);
}

.clear-button:hover {
  background: var(--surface-2);
  color: var(--text);
}

.clear-button:focus-visible {
  outline: 2px solid var(--focus-color);
  outline-offset: 1px;
}

.field-note {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
  color: var(--text-faint);
  font-size: var(--text-xs);
}

.field-note.is-detected {
  color: var(--text-muted);
  font-weight: var(--weight-medium);
}

.field-error {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 7px;
  color: var(--danger-strong);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
}

.field-error svg {
  flex: 0 0 auto;
  margin-top: 1px;
}

.link-help {
  margin-top: var(--space-2);
  color: var(--text-muted);
  font-size: var(--text-xs);
}

.link-help summary {
  display: inline-flex;
  align-items: center;
  padding: 2px 0;
  border-radius: 3px;
  color: var(--blue-700);
  font-weight: var(--weight-semibold);
  cursor: pointer;
}

.link-help ul {
  margin: var(--space-2) 0 0;
  padding-left: 18px;
  display: grid;
  gap: 3px;
  color: var(--text-muted);
}

.submit-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  min-height: var(--control-lg);
  margin-top: var(--space-4);
  padding: 0 18px;
  border: 1px solid var(--brand);
  border-radius: 12px;
  background: var(--brand);
  color: #fff;
  font-size: var(--text-base);
  font-weight: var(--weight-semibold);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.12) inset;
  transition: transform var(--dur-1) var(--ease-out);
}

.submit-button:hover:not(:disabled) {
  background: var(--blue-700);
}

.submit-button:active:not(:disabled) {
  transform: translateY(1px);
}

.submit-button:disabled {
  background: #e7e9f2;
  border-color: #e7e9f2;
  color: #626777;
  box-shadow: none;
}

.conversion-progress {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-top: var(--space-3);
  padding: 10px 12px;
  border: 1px solid var(--info-border);
  border-radius: var(--radius-sm);
  background: var(--info-bg);
  color: var(--blue-800);
}

.conversion-progress .eq-bars {
  flex: 0 0 auto;
  margin-top: 2px;
}

.progress-title {
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
}

.progress-note {
  margin-top: 1px;
  color: var(--text-muted);
  font-size: var(--text-2xs);
}

.submit-error {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: var(--space-3);
  padding: 10px 12px;
  border: 1px solid var(--danger-border);
  border-radius: var(--radius-sm);
  background: var(--danger-bg);
  color: var(--danger-strong);
}

.submit-error svg {
  flex: 0 0 auto;
  margin-top: 1px;
}

.submit-error-title {
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
}

.submit-error-text {
  margin-top: 1px;
  font-size: var(--text-xs);
  font-weight: var(--weight-regular);
}

.assurance {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: var(--space-3);
  color: var(--text-faint);
  font-size: var(--text-2xs);
  line-height: 1.45;
}

.assurance svg {
  flex: 0 0 auto;
  margin-top: 1px;
}

@media (max-width: 560px) {
  .converter {
    padding: 24px 20px;
  }

  .converter-head h2 {
    font-size: 28px;
  }
}
</style>
