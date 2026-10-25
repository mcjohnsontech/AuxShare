<template>
  <section class="playlist-input">
    <div class="eyebrow"><Sparkles :size="15" /> No login needed to preview your matches</div>
    <div class="hero-copy">
      <div class="brand-mark"><Music2 :size="24" /></div>
      <p class="brand-name">AuxParty</p>
      <h1 class="title">Move any playlist.<br><span>Keep the right songs.</span></h1>
      <p class="subtitle">Convert a playlist between your favorite music services, review the matches, and share the result in seconds.</p>
    </div>

    <div class="flow-card">
      <div class="step-heading">
        <span class="step-number">1</span>
        <div>
          <h2>Where should we find your playlist?</h2>
          <p>Paste a public Spotify or YouTube Music playlist link.</p>
        </div>
      </div>

      <form @submit.prevent="handleSubmit" class="input-form">
        <label class="input-label" for="playlist-url">Playlist link</label>
        <div class="input-row">
          <div class="input-wrapper">
            <Link2 :size="18" class="input-icon" />
            <input
              id="playlist-url"
              v-model="playlistUrl"
              type="url"
              placeholder="https://open.spotify.com/playlist/..."
              :disabled="loading"
              class="url-input"
              autocomplete="url"
            />
          </div>
          <button
            type="submit"
            :disabled="loading || !playlistUrl"
            class="convert-button"
          >
            <Loader2 v-if="loading" class="spin-icon" />
            <span v-else>Continue <ArrowRight :size="18" /></span>
          </button>
        </div>
        <p class="input-hint"><ShieldCheck :size="15" /> Public links only. Your playlist is never modified.</p>
      </form>

      <div v-if="error" class="error-message" role="alert">
        <AlertCircle class="error-icon" :size="18" />
        <span>{{ error }}</span>
      </div>
    </div>

    <div class="destination-section">
      <div class="step-heading">
        <span class="step-number">2</span>
        <div>
          <h2>Choose a destination</h2>
          <p>We'll find the closest matches in that catalog.</p>
        </div>
      </div>
      <PlatformSelector v-model="targetPlatform" />
    </div>

    <div class="info-box">
      <div class="info-header">
        <Lightbulb :size="18" class="info-icon" />
        <div>
          <h4>For the best results</h4>
          <p>Spotify playlists are currently the most reliable source. YouTube Music works best with public playlists.</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import { usePlaylistStore } from '@/stores/playlist'
import PlatformSelector from './PlatformSelector.vue'
import { Music2, Sparkles, Lightbulb, Loader2, AlertCircle, Link2, ArrowRight, ShieldCheck } from 'lucide-vue-next'

const playlistStore = usePlaylistStore()

const playlistUrl = ref('')
const targetPlatform = ref('apple_music')  // Default to Apple Music

const emit = defineEmits(['converted'])

const loading = computed(() => playlistStore.loading)
const error = computed(() => playlistStore.error)

async function handleSubmit() {
  if (!playlistUrl.value) return

  try {
    await playlistStore.convertPlaylist(playlistUrl.value, targetPlatform.value)
    emit('converted')
  } catch (err) {}
}
</script>

<style scoped>
.playlist-input {
  max-width: 760px;
  margin: 0 auto;
  padding: 24px 0 48px;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  margin-bottom: 28px;
  border: 1px solid var(--blue-100);
  border-radius: var(--radius-pill);
  background: var(--blue-50);
  color: var(--blue-700);
  font-size: 13px;
  font-weight: 600;
}

.hero-copy { text-align: center; }
.brand-mark {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  margin: 0 auto 12px;
  border-radius: 14px;
  background: var(--blue-500);
  color: #fff;
  box-shadow: 0 8px 20px rgba(47, 107, 255, .2);
}
.brand-name {
  margin: 0 0 18px;
  color: var(--blue-700);
  font-size: 14px;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
}
.title {
  margin: 0;
  color: var(--blue-900);
  font-size: clamp(2.15rem, 6vw, 3.4rem);
  font-weight: 700;
  letter-spacing: -.045em;
  line-height: 1.08;
}
.title span { color: var(--blue-500);
}
.subtitle {
  max-width: 540px;
  margin: 18px auto 34px;
  color: var(--text-muted);
  font-size: 16px;
}
.flow-card, .destination-section {
  padding: 24px;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow);
}
.flow-card { margin-bottom: 16px; }
.destination-section { margin-bottom: 16px; }
.step-heading { display: flex; gap: 12px; align-items: flex-start; }
.step-number {
  display: grid;
  place-items: center;
  flex: 0 0 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--blue-100);
  color: var(--blue-700);
  font-size: 14px;
  font-weight: 700;
}
.step-heading h2 { margin: 2px 0 3px; font-size: 17px; }
.step-heading p { margin: 0; color: var(--text-muted); font-size: 14px; }
.input-form { margin-top: 24px; }
.input-label { display: block; margin-bottom: 8px; color: var(--text); font-size: 13px; font-weight: 600; }
.input-row { display: flex; gap: 10px; }
.input-wrapper { position: relative; flex: 1; }
.input-icon { position: absolute; top: 50%; left: 14px; color: var(--text-faint); transform: translateY(-50%); }
.url-input {
  width: 100%;
  min-height: 50px;
  padding: 0 16px 0 42px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font: inherit;
  transition: border-color 150ms ease-out, box-shadow 150ms ease-out;
}
.url-input:focus { outline: none; border-color: var(--blue-500); box-shadow: 0 0 0 3px var(--blue-100); }
.url-input::placeholder { color: var(--text-faint); }
.url-input:disabled { background: var(--bg-subtle); cursor: not-allowed; }
.convert-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 126px;
  min-height: 50px;
  padding: 0 18px;
  border: 0;
  border-radius: var(--radius-sm);
  background: var(--blue-500);
  color: #fff;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  transition: background 150ms ease-out, transform 150ms ease-out;
}
.convert-button span { display: inline-flex; align-items: center; gap: 8px; }
.convert-button:hover:not(:disabled) { background: var(--blue-600); transform: translateY(-1px); }
.convert-button:disabled { opacity: .5; cursor: not-allowed; }
.input-hint { display: flex; align-items: center; gap: 6px; margin: 10px 0 0; color: var(--text-faint); font-size: 12px; }
.error-message {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin-top: 16px;
  padding: 12px;
  border: 1px solid #f3b8b3;
  border-radius: var(--radius-sm);
  background: var(--danger-bg);
  color: var(--danger);
  font-size: 14px;
}
.spin-icon {
  animation: spin 1s linear infinite;
  width: 20px;
  height: 20px;
}
.info-box {
  padding: 16px;
  border: 1px solid #f2dfac;
  border-radius: var(--radius-md);
  background: var(--warning-bg);
}
.info-header { display: flex; gap: 10px; align-items: flex-start; }
.info-icon { flex: 0 0 auto; color: var(--warning); }
.info-box h4 { margin: 0 0 2px; color: var(--text); font-size: 14px; }
.info-box p { margin: 0; color: var(--text-muted); font-size: 13px; }

@media (max-width: 640px) {
  .playlist-input { padding-top: 8px; }
  .flow-card, .destination-section { padding: 18px; }
  .input-row { flex-direction: column; }
  .convert-button { width: 100%; }
}
</style>