/**
 * Lazy loader for the official YouTube IFrame Player API.
 *
 * A plain <iframe> cannot report playback state, so the queue could never
 * advance on YouTube. The IFrame API is the supported way to observe ENDED on
 * the same embedded player — no extra playback provider is introduced.
 */
let apiPromise = null

export function loadYouTubeIframeApi() {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('YouTube playback is only available in the browser.'))
  }
  if (window.YT && typeof window.YT.Player === 'function') {
    return Promise.resolve(window.YT)
  }
  if (apiPromise) return apiPromise

  apiPromise = new Promise((resolve, reject) => {
    const previousReady = window.onYouTubeIframeAPIReady
    let settled = false

    const fail = (message) => {
      if (settled) return
      settled = true
      clearTimeout(watchdog)
      apiPromise = null
      reject(new Error(message))
    }

    const watchdog = setTimeout(() => {
      fail('The YouTube player took too long to load. Check your connection or open the track on YouTube Music.')
    }, 15000)

    window.onYouTubeIframeAPIReady = () => {
      if (typeof previousReady === 'function') previousReady()
      settled = true
      clearTimeout(watchdog)
      resolve(window.YT)
    }

    const existing = document.querySelector('script[data-aux-youtube-api]')
    if (existing) return

    const script = document.createElement('script')
    script.src = 'https://www.youtube.com/iframe_api'
    script.async = true
    script.dataset.auxYoutubeApi = 'true'
    script.addEventListener('error', () => {
      script.remove()
      fail('The YouTube player could not be loaded. Check your connection or open the track on YouTube Music.')
    })
    document.head.appendChild(script)
  })

  return apiPromise
}
