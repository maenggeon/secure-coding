import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const token = ref(localStorage.getItem('access_token') || '')
  const csrfToken = ref(localStorage.getItem('csrf_token') || '')

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'ADMIN')
  const isBlocked = computed(() => ['SUSPENDED', 'BLOCKED'].includes(user.value?.status))

  async function login(username, password) {
    const { data } = await api.post('/auth/login', { username, password })
    if (data.success) {
      token.value = data.data.access_token
      csrfToken.value = data.data.csrf_token
      user.value = data.data.user
      localStorage.setItem('access_token', token.value)
      localStorage.setItem('csrf_token', csrfToken.value)
      localStorage.setItem('user', JSON.stringify(user.value))
    }
    return data
  }

  async function logout() {
    try {
      await api.post('/auth/logout')
    } catch {
      /* ignore */
    }
    token.value = ''
    csrfToken.value = ''
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('csrf_token')
    localStorage.removeItem('user')
  }

  async function refreshProfile() {
    const { data } = await api.get('/users/me')
    if (data.success) {
      user.value = data.data
      localStorage.setItem('user', JSON.stringify(user.value))
    }
  }

  return {
    user,
    token,
    csrfToken,
    isLoggedIn,
    isAdmin,
    isBlocked,
    login,
    logout,
    refreshProfile,
  }
})
