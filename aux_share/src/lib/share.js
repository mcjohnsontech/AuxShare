// Production shares always use the public frontend, even if an older API
// deployment returns a link using its previous host. Local dev stays local.
export function shareUrlFor(code, provided = '') {
  const siteUrl = import.meta.env.PROD ? import.meta.env.VITE_SITE_URL : ''
  const origin = siteUrl || (typeof window !== 'undefined' ? window.location.origin : '')
  if (origin && code) return `${origin.replace(/\/+$/, '')}/join/${encodeURIComponent(code)}`
  return provided
}
