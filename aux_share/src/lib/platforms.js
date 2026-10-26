/**
 * Platform metadata shared by every view.
 *
 * Source sessions store display names ("Spotify"), target sessions store slugs
 * ("spotify"). `getPlatform()` accepts either.
 */
export const PLATFORMS = {
  spotify: {
    key: 'spotify',
    name: 'Spotify',
    monogram: 'S',
    urlHost: 'open.spotify.com',
    canPlayInApp: false,
    targetNote: 'Creates a real playlist in your Spotify account',
    sourceNote: 'Public Spotify playlists',
    playbackNote: 'Spotify does not allow in-app playback here — tracks open in Spotify.',
  },
  apple_music: {
    key: 'apple_music',
    name: 'Apple Music',
    monogram: 'A',
    urlHost: 'music.apple.com',
    canPlayInApp: true,
    targetNote: 'Match the catalogue · previews when available',
    sourceNote: 'Public Apple Music playlists',
    playbackNote: 'Apple Music playback uses 30-second previews supplied by Apple.',
  },
  youtube_music: {
    key: 'youtube_music',
    name: 'YouTube Music',
    monogram: 'Y',
    urlHost: 'music.youtube.com',
    canPlayInApp: true,
    targetNote: 'Play matched videos when embedding is allowed',
    sourceNote: 'Public YouTube Music playlists',
    playbackNote: 'Playback uses the YouTube player. Some tracks may be region-restricted.',
  },
}

const ALIASES = {
  spotify: 'spotify',
  apple: 'apple_music',
  apple_music: 'apple_music',
  'apple music': 'apple_music',
  youtube: 'youtube_music',
  ytmusic: 'youtube_music',
  youtube_music: 'youtube_music',
  'youtube music': 'youtube_music',
}

const UNKNOWN_PLATFORM = {
  key: 'unknown',
  name: 'Unknown service',
  monogram: '?',
  urlHost: '',
  canPlayInApp: false,
  targetNote: '',
  sourceNote: '',
  playbackNote: '',
}

/** Resolve a slug or display name to platform metadata. */
export function getPlatform(value) {
  if (!value) return UNKNOWN_PLATFORM
  const key = ALIASES[String(value).trim().toLowerCase()]
  return PLATFORMS[key] || UNKNOWN_PLATFORM
}

/** Target id key, e.g. youtube_music_id. */
export function trackTargetId(track, platformValue) {
  const { key } = getPlatform(platformValue)
  if (!track || key === 'unknown') return null
  return track[`${key}_id`] || null
}

/**
 * The only URL a track may link to: the one supplied by the backend.
 * Never synthesise a URL from an id.
 */
export function trackUrl(track, platformValue) {
  const { key } = getPlatform(platformValue)
  if (!track || key === 'unknown') return null
  const url = track[`${key}_url`]
  return typeof url === 'string' && /^https?:\/\//i.test(url) ? url : null
}

export function trackConfidence(track, platformValue) {
  const { key } = getPlatform(platformValue)
  if (!track || key === 'unknown') return null
  const value = track[`${key}_confidence`]
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

export function trackMatchMethod(track, platformValue) {
  const { key } = getPlatform(platformValue)
  if (!track || key === 'unknown') return null
  return track[`${key}_match_method`] || null
}

export function isTrackMatched(track, platformValue) {
  return Boolean(trackTargetId(track, platformValue))
}

/** Stable identity for active-row highlighting and queue syncing. */
export function trackKey(track, platformValue) {
  if (!track) return ''
  const id = trackTargetId(track, platformValue)
  if (id) return `${getPlatform(platformValue).key}:${id}`
  return `${track.title || ''}|${track.artist || ''}`
}

/** True when the embedded queue player can actually play this track. */
export function canPlayTrack(track, platformValue) {
  const { key } = getPlatform(platformValue)
  if (!track) return false
  if (key === 'youtube_music') return Boolean(track.youtube_music_id)
  if (key === 'apple_music') return Boolean(track.preview_url)
  return false
}

export function platformColor(platformValue) {
  const { key } = getPlatform(platformValue)
  if (key === 'unknown') return 'var(--platform-unknown)'
  return `var(--platform-${key === 'apple_music' ? 'apple' : key === 'youtube_music' ? 'youtube' : 'spotify'})`
}

export function platformSoftColor(platformValue) {
  const { key } = getPlatform(platformValue)
  if (key === 'unknown') return 'var(--platform-unknown-soft)'
  return `var(--platform-${key === 'apple_music' ? 'apple' : key === 'youtube_music' ? 'youtube' : 'spotify'}-soft)`
}

const SPOTIFY_PLAYLIST = /^https?:\/\/open\.spotify\.com\/(?:intl-[a-z-]+\/)?playlist\/([A-Za-z0-9]+)/i
const SPOTIFY_OTHER = /^https?:\/\/open\.spotify\.com\/(?:intl-[a-z-]+\/)?(track|album|artist|episode|show)\b/i
const YOUTUBE_PLAYLIST = /^https?:\/\/(?:www\.|music\.)?youtube\.com\/playlist\?(?:[^#]*&)?list=([A-Za-z0-9_-]+)/i
const YOUTUBE_VIDEO = /^https?:\/\/(?:www\.|music\.)?youtube\.com\/watch\b/i

/**
 * Classify a pasted URL for inline validation. Returns:
 * { url, platform, error } — error is human-readable and safe to display.
 */
export function classifyPlaylistUrl(rawValue) {
  const raw = String(rawValue || '').trim()
  if (!raw) return { url: '', platform: null, error: 'Paste a playlist link to continue.' }

  let parsed
  try {
    parsed = new URL(raw)
  } catch {
    return { url: raw, platform: null, error: 'That does not look like a link. Paste the full playlist URL, including https://.' }
  }

  if (!/^https?:$/.test(parsed.protocol)) {
    return { url: raw, platform: null, error: 'Use an http:// or https:// link.' }
  }

  if (SPOTIFY_PLAYLIST.test(raw)) {
    return { url: raw, platform: 'spotify', error: null }
  }
  if (SPOTIFY_OTHER.test(raw) || /open\.spotify\.com\/intl-[a-z-]+\/(track|album|artist|episode|show)\b/i.test(raw)) {
    return { url: raw, platform: null, error: 'That is a single item, not a playlist. Open the playlist and copy its link instead.' }
  }
  if (YOUTUBE_PLAYLIST.test(raw)) {
    return { url: raw, platform: 'youtube_music', error: null }
  }
  if (YOUTUBE_VIDEO.test(raw)) {
    return { url: raw, platform: null, error: 'That is a video link, not a playlist. Open the playlist and copy its link instead.' }
  }

  return {
    url: raw,
    platform: null,
    error: 'AuxShare converts public Spotify and YouTube Music playlists. Paste one of those playlist links.',
  }
}
