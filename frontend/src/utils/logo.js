/** Document logo (invoices, salary slips, and the on-screen invoice preview).
 *  Served from the backend so it matches the server-rendered PDFs. */
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

/** Brand logo for the website chrome (sidebar, login). Static frontend asset. */
export function getBrandLogoUrl() {
  return '/MH02-Tech-Logo.png'
}
