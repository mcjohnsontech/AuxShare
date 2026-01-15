// src/router/index.js

import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import JoinView from '@/views/JoinView.vue'
import CallbackView from '@/views/CallbackView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
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

export default router