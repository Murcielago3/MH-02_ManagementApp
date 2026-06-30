import axios from 'axios'
import { notify, describeApiError } from '../stores/notifier'

const getApiBaseUrl = () => {
  const envUrl = import.meta.env.VITE_API_URL
  if (envUrl && !envUrl.includes('localhost') && !envUrl.includes('127.0.0.1')) {
    return envUrl
  }
  if (typeof window !== 'undefined' && window.location) {
    return `${window.location.protocol}//${window.location.hostname}:8000`
  }
  return 'http://localhost:8000'
}

const API_BASE_URL = getApiBaseUrl()

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const config = error.config || {}

    // 401: kick to login. Don't toast — the page change is the signal.
    if (status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_role')
      if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
        window.location.assign('/login')
      }
      return Promise.reject(error)
    }

    // Opt-out: callers that need to handle errors themselves (e.g. show an
    // inline form error) can pass `{ skipGlobalErrorToast: true }` in the
    // axios request config. Login-attempt 401s, optional-data probes, and any
    // request marked with this flag bypass the global toast.
    if (config.skipGlobalErrorToast) {
      return Promise.reject(error)
    }

    // Skip toast for the login endpoint — its 401 already shows an inline form error.
    const url = (config.url || '').toString()
    if (/\/auth\/login\b/.test(url)) {
      return Promise.reject(error)
    }

    const { title, message } = describeApiError(error)
    notify({ type: 'error', title, message })

    return Promise.reject(error)
  }
)

export default client
