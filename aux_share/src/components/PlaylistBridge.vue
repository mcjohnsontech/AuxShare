<template>
  <figure class="playlist-bridge" aria-label="Example: the same playlist shared from Spotify to Apple Music">
    <div class="bridge-cards">
      <div v-for="service in services" :key="service.key" class="demo-playlist" :class="service.key">
        <div class="demo-service"><PlatformMark :platform="service.key" size="sm" /><span>{{ service.name }}</span></div>
        <div class="demo-heading">
          <div class="demo-art" aria-hidden="true"><Music2 :size="26" /></div>
          <div><span class="demo-label">A playlist for you</span><h2>Good company.</h2><span class="demo-count">3 songs · all the same feelings</span></div>
        </div>
        <ol class="demo-tracks">
          <li v-for="(track, index) in tracks" :key="track"><span class="demo-number">{{ index + 1 }}</span><span class="demo-mini-art" :class="`art-${index}`" aria-hidden="true"><Music2 :size="12" /></span><span>{{ track }}</span><span class="demo-duration">{{ durations[index] }}</span></li>
        </ol>
      </div>
      <span class="bridge-link" aria-hidden="true"><Link2 :size="21" /><ArrowRight :size="16" /></span>
    </div>
    <figcaption><span class="bridge-dot"></span> Same songs. A different app. <span class="demo-caption">An example of the idea.</span></figcaption>
  </figure>
</template>

<script setup>
import { ArrowRight, Link2, Music2 } from 'lucide-vue-next'
import PlatformMark from './PlatformMark.vue'

const services = [{ key: 'spotify', name: 'Spotify' }, { key: 'apple_music', name: 'Apple Music' }]
const tracks = ['Golden Hour', 'Late Night Drive', 'Stay a Little']
const durations = ['3:24', '4:08', '2:56']
</script>

<style scoped>
.playlist-bridge { margin: 36px 0 0; }
.bridge-cards { position: relative; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: start; }
.demo-playlist { min-width: 0; padding: 19px 16px 12px; border-radius: 20px; box-shadow: 0 14px 26px -16px #40312255; }
.spotify { background: #191919; color: #fff; transform: rotate(-3deg); }
.apple_music { background: #fff; color: var(--text); border: 1px solid #eee9e3; transform: rotate(3deg) translateY(18px); }
.demo-service { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 750; }
.demo-service :deep(.platform-mark) { background: transparent; width: 24px; height: 24px; }
.spotify .demo-service :deep(.platform-mark) { color: #1ed760; }
.apple_music .demo-service :deep(.platform-mark) { color: #fa243c; }
.demo-heading { display: flex; align-items: center; gap: 10px; margin-top: 17px; }
.demo-art { display: grid; place-items: center; flex: 0 0 50px; height: 58px; border-radius: 9px; color: white; background: radial-gradient(ellipse at 95% 0%, #ffd7a1, #f7a16a 27%, transparent 55%), linear-gradient(140deg, #91b8ff, #2452ff 62%, #ffa869); }
.demo-label { display: block; font-size: 8px; opacity: .7; }
.demo-heading h2 { margin: 4px 0; color: inherit; font-size: clamp(13px, 1.5vw, 18px); font-weight: 800; letter-spacing: -.05em; }
.demo-count { display: block; font-size: 7px; opacity: .65; }
.demo-tracks { margin: 15px 0 0; padding: 0; list-style: none; }
.demo-tracks li { display: flex; align-items: center; gap: 7px; min-height: 36px; border-top: 1px solid #88888824; font-size: 9px; font-weight: 500; }
.demo-number { width: 5px; opacity: .5; font-size: 8px; }
.demo-mini-art { display: grid; place-items: center; flex: 0 0 22px; height: 22px; border-radius: 5px; background: #2460ff; color: white; }
.art-1 { background: #f6a563; }.art-2 { background: #d7e5ff; color: #2452ff; }
.demo-duration { margin-left: auto; font-size: 8px; opacity: .55; }
.bridge-link { position: absolute; top: 44%; left: 50%; display: flex; align-items: center; gap: 3px; padding: 10px; border: 4px solid var(--bg); border-radius: 30px; background: var(--brand); color: white; transform: translate(-50%, -50%); box-shadow: 0 4px 14px #2452ff33; }
figcaption { display: flex; align-items: center; gap: 7px; margin-top: 39px; color: var(--text-muted); font-size: 11px; font-weight: 550; }
.bridge-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--brand); }
.demo-caption { margin-left: auto; color: var(--text-faint); font-size: 9px; font-weight: 400; }
@media (max-width: 400px) { .bridge-cards { gap: 12px; }.demo-playlist { padding: 13px 10px 8px; }.demo-art { flex-basis: 34px; height: 42px; }.demo-heading { gap: 6px; }.demo-count { display: none; }.demo-service { font-size: 11px; }.demo-tracks li { gap: 4px; }.demo-duration { display: none; }.demo-caption { display: none; } }
</style>
