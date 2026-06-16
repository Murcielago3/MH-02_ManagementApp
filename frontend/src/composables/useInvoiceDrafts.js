import { ref, computed } from 'vue'
import { useAuthStore } from '../stores/auth'

const STORAGE_KEY_PREFIX = 'invoice_drafts_'

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
    console.warn('[useInvoiceDrafts] Failed to parse drafts', e)
  }
  return []
}

function writeDrafts(drafts) {
  try {
    localStorage.setItem(getStorageKey(), JSON.stringify(drafts))
  } catch (e) {
    console.warn('[useInvoiceDrafts] Failed to save drafts', e)
  }
}

/**
 * Composable for managing multiple invoice drafts in localStorage.
 * Each draft has: { id, label, data, updatedAt }
 */
export function useInvoiceDrafts() {
  const drafts = ref(readDrafts())

  function refresh() {
    drafts.value = readDrafts()
  }

  /**
   * Save or update a draft.
   * @param {string|null} draftId - Existing draft ID to update, or null to create new
   * @param {object} formData - The invoice form data to save
   * @returns {string} The draft ID
   */
  function saveDraft(draftId, formData) {
    const list = readDrafts()
    const label = buildLabel(formData)
    const now = new Date().toISOString()

    if (draftId) {
      const idx = list.findIndex(d => d.id === draftId)
      if (idx !== -1) {
        list[idx].data = { ...formData }
        list[idx].label = label
        list[idx].updatedAt = now
      } else {
        list.unshift({ id: draftId, label, data: { ...formData }, updatedAt: now })
      }
    } else {
      draftId = generateId()
      list.unshift({ id: draftId, label, data: { ...formData }, updatedAt: now })
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
  return 'inv_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 7)
}

function buildLabel(formData) {
  const parts = []
  if (formData.bill_to_name) parts.push(formData.bill_to_name)
  if (formData.subject) parts.push(formData.subject)
  if (parts.length) return parts.join(' — ')
  if (formData.invoice_number) return formData.invoice_number
  return 'Untitled Draft'
}
