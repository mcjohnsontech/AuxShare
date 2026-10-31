export const pendingExportKey = 'spotify_pending_export_session'
const returnPathKey = 'auth_return_path'

export function beginSpotifyExport(storage, sessionCode) {
  // The home results view lives only in memory. Resume on the durable session
  // page after a full-page OAuth redirect, regardless of where export began.
  storage.setItem(pendingExportKey, sessionCode)
  storage.setItem(returnPathKey, `/join/${encodeURIComponent(sessionCode)}`)
}

export function takeSpotifyReturnPath(storage) {
  const sessionCode = storage.getItem(pendingExportKey)
  const savedPath = storage.getItem(returnPathKey)
  storage.removeItem(returnPathKey)
  // Also repairs pending exports started by older builds that saved '/'.
  if (sessionCode) return `/join/${encodeURIComponent(sessionCode)}`
  if (savedPath && /^\/join\/[A-Za-z0-9_-]+$/.test(savedPath)) return savedPath
  return '/'
}
