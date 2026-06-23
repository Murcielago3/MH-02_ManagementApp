import { ref, computed } from 'vue'
import { draftsAPI } from '../api/drafts'

const NAMESPACE = 'estimate'

// Map a server draft row onto the shape the UI has always used.
function mapDraft(row) {
  return { id: row.key, label: row.label, data: row.data, updatedAt: row.updated_at }
}

/** Stable per-draft key. Generated up front so callers (autosave) can own the
 *  id synchronously while the actual save happens asynchronously. */
export function newEstimateDraftId() {
  return 'est_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 7)
}

/**
 * Composable for managing multiple estimate drafts.
 * Drafts now live on the server, scoped to the logged-in user, so they sync
 * across devices. Each draft is { id, label, data, updatedAt }.
 */
export function useEstimateDrafts() {
  const drafts = ref([])

  async function refresh() {
    try {
      const res = await draftsAPI.list(NAMESPACE)
      drafts.value = res.data.map(mapDraft)
    } catch (e) {
      console.warn('[useEstimateDrafts] Failed to load drafts', e)
      drafts.value = []
    }
  }

  /**
   * Save or update a draft.
   * @param {string|null} draftId - Existing draft id, or null to create a new one.
   * @param {object} snapshot - The estimate snapshot to save.
   * @returns {Promise<string>} The draft id.
   */
  async function saveDraft(draftId, snapshot) {
    const id = draftId || newEstimateDraftId()
    const label = snapshot.projectName || 'Untitled Estimate'
    try {
      const res = await draftsAPI.upsert(NAMESPACE, id, { label, data: snapshot })
      const mapped = mapDraft(res.data)
      const idx = drafts.value.findIndex(d => d.id === id)
      if (idx !== -1) drafts.value[idx] = mapped
      else drafts.value.unshift(mapped)
    } catch (e) {
      console.warn('[useEstimateDrafts] Failed to save draft', e)
    }
    return id
  }

  async function deleteDraft(draftId) {
    try {
      await draftsAPI.remove(NAMESPACE, draftId)
    } catch (e) {
      console.warn('[useEstimateDrafts] Failed to delete draft', e)
    }
    drafts.value = drafts.value.filter(d => d.id !== draftId)
  }

  async function getDraft(draftId) {
    try {
      const res = await draftsAPI.get(NAMESPACE, draftId)
      return mapDraft(res.data)
    } catch (e) {
      return null
    }
  }

  const hasDrafts = computed(() => drafts.value.length > 0)

  return { drafts, hasDrafts, saveDraft, deleteDraft, getDraft, refresh }
}
