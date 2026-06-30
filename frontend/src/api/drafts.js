import client from './client'

/**
 * Generic per-account draft store.
 *
 * Drafts used to live in this browser's localStorage; they now live on the
 * server, scoped to the logged-in user (via the auth token). That means a
 * user's drafts follow their account across devices instead of being stranded
 * on one machine.
 *
 * A draft is addressed by (namespace, key):
 *   • namespace groups drafts by feature ('estimate', 'invoice',
 *     'client_create', 'timesheet_2026-05-26', …).
 *   • key distinguishes multiple drafts in a namespace. List-style features
 *     generate a unique key per draft; single-slot autosave forms use 'default'.
 */
export const draftsAPI = {
  // List every draft in a namespace (returns [] when there are none).
  list: (namespace) =>
    client.get(`/drafts/${encodeURIComponent(namespace)}`),

  // Fetch one draft. 404s when absent — pass skipGlobalErrorToast so a missing
  // draft never pops an error toast.
  get: (namespace, key) =>
    client.get(
      `/drafts/${encodeURIComponent(namespace)}/${encodeURIComponent(key)}`,
      { skipGlobalErrorToast: true }
    ),

  // Create or update (idempotent on namespace+key).
  upsert: (namespace, key, payload) =>
    client.put(
      `/drafts/${encodeURIComponent(namespace)}/${encodeURIComponent(key)}`,
      payload
    ),

  remove: (namespace, key) =>
    client.delete(
      `/drafts/${encodeURIComponent(namespace)}/${encodeURIComponent(key)}`
    ),
}
