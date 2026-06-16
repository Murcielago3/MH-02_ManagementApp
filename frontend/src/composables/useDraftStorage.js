import { ref, computed, watch, unref, isRef } from 'vue'
import { useAuthStore } from '../stores/auth'

/**
 * Reusable composable for localStorage draft persistence.
 * All keys are user-scoped: draft_{key}_{userId}
 *
 * @param {string | Ref<string>} key - Unique key for this draft (e.g. 'timesheet_2026-05-26', 'project_create')
 * @returns {{ draft: Ref, saveDraft: Function, clearDraft: Function, hasDraft: ComputedRef<boolean> }}
 */
export function useDraftStorage(key) {
  const authStore = useAuthStore()
  const userId = computed(() => authStore.user?.id ?? 'anon')
  const resolvedKey = computed(() => `draft_${unref(key)}_${userId.value}`)

  function readFromStorage() {
    try {
      const raw = localStorage.getItem(resolvedKey.value)
      if (raw) return JSON.parse(raw)
    } catch (e) {
      console.warn(`[useDraftStorage] Failed to parse draft for "${resolvedKey.value}"`, e)
    }
    return null
  }

  const draft = ref(readFromStorage())

  // Re-read if the storage key changes (userId change, or reactive key change)
  watch(resolvedKey, () => {
    draft.value = readFromStorage()
  })

  function saveDraft(data) {
    try {
      localStorage.setItem(resolvedKey.value, JSON.stringify(data))
      draft.value = data
    } catch (e) {
      console.warn(`[useDraftStorage] Failed to save draft for "${resolvedKey.value}"`, e)
    }
  }

  function clearDraft() {
    try {
      localStorage.removeItem(resolvedKey.value)
    } catch (e) {
      // ignore
    }
    draft.value = null
  }

  const hasDraft = computed(() => draft.value !== null)

  return { draft, saveDraft, clearDraft, hasDraft }
}
