// src/router/index.js

import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import JoinView from '@/views/JoinView.vue'
import CallbackView from '@/views/CallbackView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior() {
    return { top: 0 }
  },
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/join/:code',
      name: 'join',
      component: JoinView
    },
    {
      path: '/callback',
      name: 'callback',
      component: CallbackView
    }
  ]
})

router.afterEach((to) => {
  const siteName = 'AuxShare'
  if (to.name === 'join') {
    document.title = `Shared playlist — ${siteName}`
  } else if (to.name === 'callback') {
    document.title = `Connecting Spotify — ${siteName}`
  } else {
    document.title = 'AuxShare — Convert playlists between Spotify, Apple Music & YouTube Music'
  }
})

export default router