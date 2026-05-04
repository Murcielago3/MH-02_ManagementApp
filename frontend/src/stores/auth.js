import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('access_token') || null)
  const user = ref(null)
  const role = ref(localStorage.getItem('user_role') || null)
  const loading = ref(false)
  const error = ref(null)

  const isAuthenticated = computed(() => !!token.value)

  const setToken = (newToken, userRole) => {
    token.value = newToken
    role.value = userRole
    localStorage.setItem('access_token', newToken)
    localStorage.setItem('user_role', userRole)
  }

  const clearAuth = () => {
    token.value = null
    user.value = null
    role.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_role')
  }

  return {
    token,
    user,
    role,
    loading,
    error,
    isAuthenticated,
    setToken,
    clearAuth,
  }
})
