import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api } from '../api'

const TOKEN_KEY = 'yunyun_token'
const USER_KEY = 'yunyun_user'

function readUser() {
  try {
    return JSON.parse(sessionStorage.getItem(USER_KEY) || 'null')
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)

  const token = ref(sessionStorage.getItem(TOKEN_KEY) || '')
  const user = ref(readUser())
  const unread = ref(0)

  const isLoggedIn = computed(() => Boolean(token.value && user.value))
  const isAdmin = computed(() => Boolean(user.value?.is_admin))

  function persist() {
    if (token.value) sessionStorage.setItem(TOKEN_KEY, token.value)
    else sessionStorage.removeItem(TOKEN_KEY)
    if (user.value) sessionStorage.setItem(USER_KEY, JSON.stringify(user.value))
    else sessionStorage.removeItem(USER_KEY)
  }

  async function login(account, password) {
    const data = await api.login({ account, password })
    token.value = data.access_token
    user.value = data.user
    persist()
    await refreshUnread()
  }

  async function register(payload) {
    const data = await api.register(payload)
    token.value = data.access_token
    user.value = data.user
    persist()
    unread.value = 0
  }

  function logout() {
    token.value = ''
    user.value = null
    unread.value = 0
    persist()
  }

  async function refreshMe() {
    if (!token.value) return
    try {
      user.value = await api.me(token.value)
      persist()
      await refreshUnread()
    } catch (e) {
      if (e.status === 401) logout()
    }
  }

  async function refreshUnread() {
    if (!token.value) {
      unread.value = 0
      return
    }
    try {
      const data = await api.unreadCount(token.value)
      unread.value = data.count || 0
    } catch {
      unread.value = 0
    }
  }

  return {
    token,
    user,
    unread,
    isLoggedIn,
    isAdmin,
    login,
    register,
    logout,
    refreshMe,
    refreshUnread,
    persist,
  }
})
