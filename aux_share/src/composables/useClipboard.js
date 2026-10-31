import { onBeforeUnmount, ref } from 'vue'

/**
 * Clipboard helper with a legacy fallback and explicit failure state.
 * `state` is 'idle' | 'copied' | 'error'; callers should render a live message.
 */
export function useClipboard({ resetAfter = 2400 } = {}) {
  const state = ref('idle')
  let timer = null

  function scheduleReset() {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      state.value = 'idle'
    }, resetAfter)
  }

  async function copy(text) {
    const value = String(text || '')
    if (!value) {
      state.value = 'error'
      scheduleReset()
      return false
    }

    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(value)
      } else {
        legacyCopy(value)
      }
      state.value = 'copied'
      scheduleReset()
      return true
    } catch {
      try {
        legacyCopy(value)
        state.value = 'copied'
        scheduleReset()
        return true
      } catch {
        state.value = 'error'
        scheduleReset()
        return false
      }
    }
  }

  onBeforeUnmount(() => {
    if (timer) clearTimeout(timer)
  })

  return { state, copy }
}

function legacyCopy(value) {
  const field = document.createElement('textarea')
  field.value = value
  field.setAttribute('readonly', '')
  field.style.position = 'fixed'
  field.style.top = '-1000px'
  field.style.opacity = '0'
  document.body.appendChild(field)
  field.select()
  field.setSelectionRange(0, value.length)
  const ok = document.execCommand('copy')
  document.body.removeChild(field)
  if (!ok) throw new Error('Copy command was rejected')
}
