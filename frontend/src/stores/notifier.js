// Global notification store — a tiny reactive queue so any code (an axios
// interceptor, a router guard, a component) can surface a toast without each
// view having to wire up its own <ToastNotification>. The single
// <GlobalNotifier> mounted in App.vue subscribes to this list.
import { reactive } from 'vue'

const state = reactive({
  toasts: [], // { id, message, type, duration, title? }
})

let nextId = 1

/**
 * Push a notification.
 * Accepts either a string (defaults to type 'info') or an options object:
 *   notify('Saved')
 *   notify({ message: 'Failed', type: 'error', duration: 6000, title: 'Save failed' })
 * Returns the toast id (so callers can dismiss programmatically).
 */
export function notify(opts) {
  const t = typeof opts === 'string' ? { message: opts } : opts || {}
  const toast = {
    id: nextId++,
    message: t.message || '',
    type: t.type || 'info', // info | success | error | warning
    duration: t.duration ?? (t.type === 'error' ? 6000 : 3500),
    title: t.title || null,
  }
  state.toasts.push(toast)
  if (toast.duration > 0) {
    setTimeout(() => dismiss(toast.id), toast.duration)
  }
  return toast.id
}

// Convenience helpers — easier to read at the call site.
export const notifySuccess = (message, opts = {}) => notify({ ...opts, message, type: 'success' })
export const notifyError = (message, opts = {}) => notify({ ...opts, message, type: 'error' })
export const notifyWarning = (message, opts = {}) => notify({ ...opts, message, type: 'warning' })
export const notifyInfo = (message, opts = {}) => notify({ ...opts, message, type: 'info' })

export function dismiss(id) {
  const idx = state.toasts.findIndex((x) => x.id === id)
  if (idx >= 0) state.toasts.splice(idx, 1)
}

export function clearAll() {
  state.toasts.splice(0)
}

// Composable form for use in <script setup>
export function useNotifier() {
  return {
    notify,
    notifySuccess,
    notifyError,
    notifyWarning,
    notifyInfo,
    dismiss,
    clearAll,
    toasts: state.toasts,
  }
}

// Friendly HTTP-status → message translator. Used by the axios interceptor.
export function describeApiError(err) {
  // Network failure / browser-blocked / server down
  if (err && !err.response) {
    if (err.code === 'ERR_NETWORK' || err.message?.includes('Network Error')) {
      return {
        title: 'Cannot reach the server',
        message: 'Check your internet connection or contact an admin if the issue continues.',
      }
    }
    if (err.code === 'ECONNABORTED') {
      return { title: 'Request timed out', message: 'The server took too long to respond. Please try again.' }
    }
    return { title: 'Connection error', message: err.message || 'Something went wrong reaching the server.' }
  }

  const status = err.response.status
  const data = err.response.data
  // Prefer the server's `detail` (FastAPI convention), then `message`, then a string body.
  let detail = ''
  if (data) {
    if (typeof data === 'string') detail = data
    else if (typeof data.detail === 'string') detail = data.detail
    else if (Array.isArray(data.detail)) {
      // Pydantic validation errors come back as a list of {loc, msg, type}
      detail = data.detail
        .map((d) => `${(d.loc || []).slice(-1)[0] || 'field'}: ${d.msg}`)
        .join(' · ')
    } else if (typeof data.message === 'string') detail = data.message
  }

  if (status === 400) return { title: 'Invalid request', message: detail || 'Please check the form and try again.' }
  if (status === 401) return { title: 'Session expired', message: 'Please log in again to continue.' }
  if (status === 403) return { title: 'Not allowed', message: detail || "You don't have permission for this action." }
  if (status === 404) return { title: 'Not found', message: detail || "We couldn't find what you were looking for." }
  if (status === 409) return { title: 'Conflict', message: detail || 'That conflicts with existing data.' }
  if (status === 413) return { title: 'File too large', message: detail || 'Try a smaller file.' }
  if (status === 422) return { title: 'Validation failed', message: detail || 'Some fields look invalid.' }
  if (status === 429) return { title: 'Too many requests', message: 'Slow down a moment and try again.' }
  if (status >= 500) return { title: 'Server error', message: detail || 'Something went wrong on our side. Please try again.' }
  return { title: `Error ${status}`, message: detail || 'Something went wrong.' }
}
