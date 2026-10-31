/** Format a millisecond duration as m:ss (or h:mm:ss). */
export function formatDuration(ms) {
  if (typeof ms !== 'number' || !Number.isFinite(ms) || ms <= 0) return ''
  return formatSeconds(Math.round(ms / 1000))
}

/** Format seconds as m:ss (or h:mm:ss when needed). */
export function formatSeconds(totalSeconds) {
  if (typeof totalSeconds !== 'number' || !Number.isFinite(totalSeconds) || totalSeconds < 0) {
    return '0:00'
  }
  const seconds = Math.floor(totalSeconds)
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const rest = seconds % 60
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(rest).padStart(2, '0')}`
  }
  return `${minutes}:${String(rest).padStart(2, '0')}`
}

/** 1 → "1 track", 4 → "4 tracks". */
export function pluralize(count, singular, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`
}

/** Round a 0–1 ratio to a whole percentage, or null when unavailable. */
export function toPercent(ratio) {
  if (typeof ratio !== 'number' || !Number.isFinite(ratio)) return null
  return Math.round(ratio * 100)
}
