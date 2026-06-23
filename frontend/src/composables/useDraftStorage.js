import { ref, computed, watch, unref } from 'vue'
import { draftsAPI } from '../api/drafts'

/**
 * Account-synced single-slot draft persistence (one draft per namespace).
 *
 * Previously backed by localStorage; now backed by the server so the draft
 * follows the logged-in user across devices. The namespace doubles as the
 * feature key — e.g. 'client_create', 'project_create', 'timesheet_2026-05-26'.
 *
 * Saves are debounced so an autosave watcher firing on every keystroke results
 * in at most one network write per quiet period.
 *
 * @param {string | import('vue').Ref<string>} key - namespace for this draft.
 * @returns {{ draft: Ref, saveDraft: Function, clearDraft: Function,
 *            hasDraft: ComputedRef<boolean>, loaded: Ref<boolean>, load: Function }}
 */
const SLOT_KEY = 'default'
const SAVE_DEBOUNCE_MS = 600

export function useDraftStorage(key) {
  const namespace = computed(() => unref(key))
  const draft = ref(null)
  const loaded = ref(false)

  let saveTimer = null
  let pending = null   // latest { ns, data } not yet sent
  let inflight = null  // promise of the PUT currently in flight

  async function load() {
    const ns = namespace.value
    loaded.value = false
    try {
      const res = await draftsAPI.list(ns)
      // Drop a stale response if the (reactive) key changed mid-flight.
      if (ns !== namespace.value) return
      draft.value = res.data.length ? res.data[0].data : null
    } catch (e) {
      if (ns === namespace.value) draft.value = null
    } finally {
      if (ns === namespace.value) loaded.value = true
    }
  }

  // Initial load, and reload whenever the key changes (e.g. switching weeks).
  watch(namespace, () => { load() }, { immediate: true })

  function flush() {
    if (!pending) return inflight || Promise.resolve()
    const { ns, data } = pending
    pending = null
    inflight = draftsAPI
      .upsert(ns, SLOT_KEY, { label: null, data })
      .catch(() => {})
      .finally(() => { inflight = null })
    return inflight
  }

  function saveDraft(data) {
    draft.value = data
    pending = { ns: namespace.value, data }
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(() => { saveTimer = null; flush() }, SAVE_DEBOUNCE_MS)
  }

  async function clearDraft() {
    if (saveTimer) { clearTimeout(saveTimer); saveTimer = null }
    pending = null
    const ns = namespace.value
    draft.value = null
    try {
      if (inflight) await inflight  // don't let a late save resurrect the draft
      await draftsAPI.remove(ns, SLOT_KEY)
    } catch (e) {
      // ignore — clearing a draft is best-effort
    }
  }

  const hasDraft = computed(() => draft.value !== null)

  return { draft, saveDraft, clearDraft, hasDraft, loaded, load }
}
