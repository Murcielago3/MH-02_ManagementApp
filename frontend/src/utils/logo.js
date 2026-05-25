/** Resolve the shared invoice logo asset from the backend. */
export function getAppLogoUrl() {
  const envUrl = import.meta.env.VITE_API_URL
  if (envUrl && !envUrl.includes('localhost') && !envUrl.includes('127.0.0.1')) {
    return `${envUrl.replace(/\/$/, '')}/static/logo.jpg`
  }

  if (typeof window !== 'undefined' && window.location) {
    return `${window.location.protocol}//${window.location.hostname}:8000/static/logo.jpg`
  }

  return 'http://localhost:8000/static/logo.jpg'
}
