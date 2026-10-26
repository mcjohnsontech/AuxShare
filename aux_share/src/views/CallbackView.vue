<template>
  <main id="main" class="callback">
    <div class="callback-card">
      <span class="callback-mark" aria-hidden="true">
        <span class="mark-bar" style="height: 8px"></span>
        <span class="mark-bar" style="height: 15px"></span>
        <span class="mark-bar" style="height: 11px"></span>
      </span>

      <p class="eyebrow">Spotify connection</p>
      <h1>{{ message }}</h1>
      <p class="callback-text" role="status" aria-live="polite">
        Please wait while we verify the connection and bring you back.
      </p>

      <div class="progress" aria-hidden="true">
        <Loader2 :size="18" class="spin" />
        <span>This usually takes a second</span>
      </div>

      <p class="fallback">
        Nothing happening?
        <RouterLink to="/">Return to AuxShare</RouterLink>
      </p>
    </div>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { Loader2 } from 'lucide-vue-next'
import { API_BASE_URL } from '@/services/api'

const router = useRouter()
const route = useRoute()
const message = ref('Connecting to Spotify…')

async function adoptSession(handoff) {
  const res = await fetch(`${API_BASE_URL}/api/auth/handoff`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ code: handoff }),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || 'Could not complete Spotify sign-in')
  }
}

function goBack() {
  const returnPath = localStorage.getItem('auth_return_path')
  if (returnPath) {
    localStorage.removeItem('auth_return_path')
    router.push(returnPath)
  } else {
    router.push('/')
  }
}

onMounted(async () => {
  // Clear any legacy plaintext token stored in localStorage for security.
  localStorage.removeItem('spotify_access_token')

  const { status, error, handoff } = route.query

  if (error) {
    console.error('Auth error:', error)
    localStorage.removeItem('spotify_pending_export_session')
    localStorage.removeItem('auth_return_path')
    router.push('/?auth_error=' + encodeURIComponent(error))
    return
  }

  if (status === 'success' || handoff) {
    try {
      if (handoff) {
        message.value = 'Finishing sign-in…'
        await adoptSession(handoff)
        message.value = 'Connected — returning…'
      }
      // Let the status be readable for a beat before navigating away.
      window.setTimeout(goBack, 350)
    } catch (e) {
      console.error(e)
      message.value = 'Spotify sign-in failed'
      localStorage.removeItem('spotify_pending_export_session')
      localStorage.removeItem('auth_return_path')
      router.push('/?auth_error=' + encodeURIComponent(e.message || 'handoff_failed'))
    }
  } else {
    router.push('/')
  }
})
</script>

<style scoped>
.callback {
  display: grid;
  place-items: center;
  min-height: 100vh;
  padding: var(--space-4);
  background:
    radial-gradient(700px 320px at 50% -120px, rgba(47, 107, 255, 0.12), transparent 70%),
    var(--bg);
}

.callback-card {
  width: min(430px, 100%);
  padding: var(--space-6);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow);
  text-align: center;
}

.callback-mark {
  display: inline-flex;
  align-items: flex-end;
  justify-content: center;
  gap: 2.5px;
  width: 42px;
  height: 42px;
  margin-bottom: var(--space-3);
  padding-bottom: 11px;
  border-radius: 12px;
  background: var(--brand);
  box-shadow: inset 0 -7px 14px rgba(11, 31, 77, 0.2);
}

.mark-bar {
  width: 4px;
  border-radius: 2px;
  background: #fff;
}

.eyebrow {
  color: var(--blue-700);
  font-size: var(--text-2xs);
  font-weight: var(--weight-bold);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
}

.callback-card h1 {
  margin-top: var(--space-2);
  font-size: var(--text-xl);
  letter-spacing: var(--tracking-tight);
}

.callback-text {
  margin-top: var(--space-2);
  color: var(--text-muted);
  font-size: var(--text-sm);
  line-height: 1.55;
}

.progress {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  margin-top: var(--space-4);
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  background: var(--surface-2);
  color: var(--text-faint);
  font-size: var(--text-xs);
}

.progress svg {
  color: var(--blue-600);
}

.fallback {
  margin-top: var(--space-4);
  color: var(--text-faint);
  font-size: var(--text-xs);
}

.fallback a {
  color: var(--blue-700);
  font-weight: var(--weight-semibold);
}

@media (max-width: 480px) {
  .callback-card {
    padding: var(--space-5) var(--space-4);
  }
}
</style>
