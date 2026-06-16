import { ref, computed } from 'vue'
import { useAuthStore } from '../stores/auth'

const STORAGE_KEY_PREFIX = 'estimate_drafts_'

function getStorageKey() {
  const authStore = useAuthStore()
  const userId = authStore.user?.id ?? 'anon'
  return `${STORAGE_KEY_PREFIX}${userId}`
}

function readDrafts() {
  try {
    const raw = localStorage.getItem(getStorageKey())
    if (raw) return JSON.parse(raw)
  } catch (e) {
    console.warn('[useEstimateDrafts] Failed to parse drafts', e)
  }
  return []
}

function writeDrafts(drafts) {
  try {
    localStorage.setItem(getStorageKey(), JSON.stringify(drafts))
  } catch (e) {
    console.warn('[useEstimateDrafts] Failed to save drafts', e)
  }
}

/**
 * Composable for managing multiple estimate drafts in localStorage.
 * Each draft has: { id, label, data, updatedAt }
 */
export function useEstimateDrafts() {
  const drafts = ref(readDrafts())

  function refresh() {
    drafts.value = readDrafts()
  }

  /**
   * Save or update a draft.
   * @param {string|null} draftId - Existing draft ID to update, or null to create new
   * @param {object} snapshot - The estimate snapshot to save
   * @returns {string} The draft ID
   */
  function saveDraft(draftId, snapshot) {
    const list = readDrafts()
    const label = snapshot.projectName || 'Untitled Estimate'
    const now = new Date().toISOString()

    if (draftId) {
      const idx = list.findIndex(d => d.id === draftId)
      if (idx !== -1) {
        list[idx].data = { ...snapshot }
        list[idx].label = label
        list[idx].updatedAt = now
      } else {
        list.unshift({ id: draftId, label, data: { ...snapshot }, updatedAt: now })
      }
    } else {
      draftId = generateId()
      list.unshift({ id: draftId, label, data: { ...snapshot }, updatedAt: now })
    }

    writeDrafts(list)
    drafts.value = list
    return draftId
  }

  function deleteDraft(draftId) {
    const list = readDrafts().filter(d => d.id !== draftId)
    writeDrafts(list)
    drafts.value = list
  }

  function getDraft(draftId) {
    const list = readDrafts()
    return list.find(d => d.id === draftId) || null
  }

  const hasDrafts = computed(() => drafts.value.length > 0)

  return { drafts, hasDrafts, saveDraft, deleteDraft, getDraft, refresh }
}

function generateId() {
  return 'est_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 7)
}
