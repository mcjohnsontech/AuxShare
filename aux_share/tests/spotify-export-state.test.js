import assert from 'node:assert/strict'
import test from 'node:test'
import { beginSpotifyExport, pendingExportKey, takeSpotifyReturnPath } from '../src/lib/spotifyExportState.js'

function storage(values = {}) {
  const entries = new Map(Object.entries(values))
  return {
    getItem: key => entries.get(key) ?? null,
    setItem: (key, value) => entries.set(key, String(value)),
    removeItem: key => entries.delete(key),
  }
}

test('homepage exports resume on the persistent playlist after an OAuth reload', () => {
  const state = storage()
  beginSpotifyExport(state, 'playlist-123')
  assert.equal(state.getItem('auth_return_path'), '/join/playlist-123')
  assert.equal(takeSpotifyReturnPath(state), '/join/playlist-123')
  assert.equal(state.getItem(pendingExportKey), 'playlist-123')
  assert.equal(state.getItem('auth_return_path'), null)
})

test('repairs pending exports that an older build would return to the homepage', () => {
  const state = storage({ auth_return_path: '/', [pendingExportKey]: 'saved-session' })
  assert.equal(takeSpotifyReturnPath(state), '/join/saved-session')
})

test('pending session takes precedence over a stale return path', () => {
  const state = storage({ auth_return_path: '/join/old', [pendingExportKey]: 'new' })
  assert.equal(takeSpotifyReturnPath(state), '/join/new')
})

test('encodes session codes instead of treating them as paths', () => {
  const state = storage()
  beginSpotifyExport(state, 'a/b?c')
  assert.equal(takeSpotifyReturnPath(state), '/join/a%2Fb%3Fc')
})

test('can return to a saved playlist without a pending export', () => {
  assert.equal(takeSpotifyReturnPath(storage({ auth_return_path: '/join/saved' })), '/join/saved')
})

test('missing, external, or callback return paths fall back to home', () => {
  for (const path of [undefined, '/', '//example.com', 'https://example.com', '/callback']) {
    assert.equal(takeSpotifyReturnPath(storage(path ? { auth_return_path: path } : {})), '/')
  }
})
