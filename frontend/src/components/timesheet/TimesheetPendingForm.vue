<template>
  <div class="form-container">
    <div v-if="week.status === 'rejected'" class="rejected-alert">
      <div class="alert-header">
        <span class="material-symbols-outlined">error</span>
        <h4>This timesheet was rejected</h4>
      </div>
      <p class="rejection-reason">{{ week.rejection_reason || 'No reason provided by admin.' }}</p>
    </div>

    <!-- Draft restore banner -->
    <div v-if="showDraftBanner" class="draft-banner">
      <span class="material-symbols-outlined">history</span>
      <span>You have an unsaved draft for this week.</span>
      <button type="button" class="draft-restore-btn" @click="restoreTsDraft">Restore</button>
      <button type="button" class="draft-discard-btn" @click="discardTsDraft">Discard</button>
    </div>

    <form @submit.prevent="handleSubmit" class="timesheet-form">
      <div v-if="store.loading" class="loading-overlay">
        <span class="material-symbols-outlined rotating">sync</span>
        <p>Fetching assigned tasks...</p>
      </div>

      <div class="form-section">
        <div class="section-header">
          <div>
            <label>Daily Hours Log</label>
            <p class="section-desc">Log hours per project for each working day. Add more project rows as needed.</p>
          </div>
          <button type="button" class="btn-add-task" @click="addRow">
            <span class="material-symbols-outlined">add</span>
            Add Project
          </button>
        </div>

        <!-- One card per work item: project -> stage -> subtask, then the week -->
        <div class="entry-cards">
          <div v-for="(row, ri) in rows" :key="ri" class="entry-card" :class="{ filled: rowTotal(ri) > 0 }">
            <div class="ec-head">
              <div class="ec-selects">
                <select v-model="row.project_id" required class="ec-select ec-project"
                        @change="onProjectChange(row)">
                  <option :value="null" disabled>Select project…</option>
                  <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
                </select>

                <template v-if="row.project_id && stagesFor(row.project_id).length">
                  <span class="ec-arrow material-symbols-outlined">chevron_right</span>
                  <select v-model="row.stage_id" required class="ec-select ec-stage"
                          :class="{ missing: rowTotal(ri) > 0 && !row.stage_id }"
                          @change="row.subtask_id = null">
                    <option :value="null" disabled>Select stage…</option>
                    <option v-for="s in stagesFor(row.project_id)" :key="s.id" :value="s.id">
                      {{ s.name }} · {{ s.completion_percent }}%
                    </option>
                  </select>

                  <template v-if="row.stage_id">
                    <span class="ec-arrow material-symbols-outlined">chevron_right</span>
                    <select v-model="row.subtask_id" class="ec-select ec-sub">
                      <option :value="null">Subtask (optional)</option>
                      <option v-for="t in subtasksFor(row.project_id, row.stage_id)" :key="t.id" :value="t.id">
                        {{ t.status === 'completed' ? '✓ ' : '' }}{{ t.title }}
                      </option>
                    </select>
                  </template>
                </template>
              </div>

              <div class="ec-right">
                <span class="ec-total" :class="{ on: rowTotal(ri) > 0 }">{{ rowTotal(ri) }}h</span>
                <button type="button" class="ec-remove" @click="removeRow(ri)" :disabled="rows.length === 1"
                        title="Remove this row">
                  <span class="material-symbols-outlined">delete</span>
                </button>
              </div>
            </div>

            <div class="ec-days">
              <label v-for="(d, di) in weekDays" :key="di" class="ec-day" :class="{ weekend: di >= 5 }">
                <span class="ec-day-name">{{ d.short }}</span>
                <span class="ec-day-date">{{ d.dateLabel }}</span>
                <input v-model.number="row.daily[di]" type="number" step="0.5" min="0" max="24"
                       class="ec-day-input" placeholder="0" />
              </label>
            </div>

            <input v-model="row.description" type="text" class="ec-desc"
                   placeholder="What did you work on?" :required="rowTotal(ri) > 0" />
          </div>
        </div>

        <!-- Week totals -->
        <div class="week-totals">
          <span class="wt-label">Daily total</span>
          <div class="wt-days">
            <span v-for="(d, di) in weekDays" :key="di" class="wt-day"
                  :class="{ 'over-8': dayTotal(di) > 8, weekend: di >= 5, zero: dayTotal(di) === 0 }">
              <small>{{ d.short }}</small>{{ dayTotal(di) }}h
            </span>
          </div>
          <span class="wt-grand" :class="{ on: grandTotal > 0 }">{{ grandTotal }}h</span>
        </div>
      </div>

      <div class="form-section">
        <label>Weekly Overview <span class="required">*</span></label>
        <p class="section-desc">Summarize your overall progress and blockers for the week (Required).</p>
        <textarea
          v-model="description"
          rows="3"
          placeholder="Overall progress and highlights..."
          required
        ></textarea>
        <div class="char-count" v-if="description.length < 20">
          Min 20 characters ({{ description.length }}/20)
        </div>
      </div>

      <div class="form-actions">
        <div v-if="!isValid && missingItems.length" class="submit-hint">
          <span class="material-symbols-outlined">info</span>
          <div>
            <span class="submit-hint-title">Before you can submit:</span>
            <ul>
              <li v-for="(m, mi) in missingItems" :key="mi">{{ m }}</li>
            </ul>
          </div>
        </div>
        <button
          type="submit"
          class="btn-submit"
          :disabled="!isValid || submitting"
        >
          <span class="material-symbols-outlined" v-if="!submitting">send</span>
          <span class="material-symbols-outlined rotating" v-else>sync</span>
          {{ submitLabel }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useTimesheetStore } from '../../stores/timesheet'
import { useDraftStorage } from '../../composables/useDraftStorage'
import { stagesAPI } from '../../api/stages'

const props = defineProps({
  week: { type: Object, required: true },
  projects: { type: Array, required: true }
})

const emit = defineEmits(['submit'])
const store = useTimesheetStore()

const description = ref('')
const rows = ref([])
const submitting = ref(false)
const showDraftBanner = ref(false)

// Compute weekday labels from the week range
const weekDays = computed(() => {
  const start = new Date(props.week.week_start + 'T00:00:00')
  const days = []
  const shortNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  for (let i = 0; i < 7; i++) {
    const d = new Date(start)
    d.setDate(start.getDate() + i)
    days.push({
      short: shortNames[i],
      dateLabel: d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }),
      date: d
    })
  }
  return days
})

function makeEmptyRow() {
  return { project_id: null, stage_id: null, subtask_id: null, daily: [0, 0, 0, 0, 0, 0, 0], description: '' }
}

// ── Stage / subtask options, fetched lazily per project ──
// Cached so switching rows between projects doesn't refetch. Projects without
// stages simply return [], and the selects stay hidden.
const stagesByProject = ref({})
const subtasksByProject = ref({})

function stagesFor(projectId) { return stagesByProject.value[projectId] || [] }
function subtasksFor(projectId, stageId) {
  return (subtasksByProject.value[projectId] || []).filter(t => t.stage_id === stageId)
}

async function ensureStages(projectId) {
  if (!projectId || stagesByProject.value[projectId]) return
  try {
    const { data } = await stagesAPI.list(projectId)
    stagesByProject.value = { ...stagesByProject.value, [projectId]: data.stages || [] }
    subtasksByProject.value = {
      ...subtasksByProject.value,
      [projectId]: (data.stages || []).flatMap(s => s.subtasks || []),
    }
  } catch (e) {
    stagesByProject.value = { ...stagesByProject.value, [projectId]: [] }
  }
}

function onProjectChange(row) {
  row.stage_id = null
  row.subtask_id = null
  ensureStages(row.project_id)
}

// Draft storage keyed by week start (reactive key). Server-backed per account,
// so a half-filled week follows the user across devices.
const draftKey = computed(() => `timesheet_${props.week.week_start}`)
const { draft: tsDraft, saveDraft: saveTsDraft, clearDraft: clearTsDraft, hasDraft: hasTsDraft, load: loadTsDraft } = useDraftStorage(draftKey)
// Snapshot of the draft as loaded from the server, captured before autosave can
// overwrite it - so "Restore" always brings back what was actually saved.
const restorableDraft = ref(null)
// True while we populate the form from the store/server. Auto-save is suppressed
// during this window so the programmatic (often empty) population never saves a
// blank draft over the user's real one.
const hydrating = ref(true)

function rowHasContent(r) {
  return !!(r && (r.project_id || (r.description && r.description.trim()) ||
    (Array.isArray(r.daily) && r.daily.some(h => Number(h) > 0))))
}
// Does the live form hold anything worth saving?
function formHasContent() {
  return !!description.value.trim() || rows.value.some(rowHasContent)
}
// Does a loaded draft hold anything worth restoring? (avoids a banner for blank drafts)
function draftHasContent(d) {
  if (!d) return false
  if (d.description && d.description.trim()) return true
  return Array.isArray(d.rows) && d.rows.some(rowHasContent)
}

// Sync from store - convert flat entries to grid rows
watch(() => props.week, async () => {
  hydrating.value = true
  description.value = store.form.description || ''

  const storeEntries = store.form.entries || []
  if (storeEntries.length > 0) {
    rows.value = storeEntries.map(e => ({
      project_id: e.project_id,
      stage_id: e.stage_id ?? null,
      subtask_id: e.subtask_id ?? null,
      daily: e.daily ? padDaily(e.daily) : distributeHours(e.hours || 0),
      description: e.description || ''
    }))
    // Load stage options for every project already on the sheet.
    for (const id of new Set(rows.value.map(r => r.project_id).filter(Boolean))) ensureStages(id)
  } else {
    rows.value = [makeEmptyRow()]
  }

  // This week's draft loads asynchronously from the server. Reset the banner,
  // then show it only if the saved draft actually has content for this week.
  showDraftBanner.value = false
  restorableDraft.value = await loadTsDraft()
  if (draftHasContent(restorableDraft.value)) {
    showDraftBanner.value = true
  }
  // Population (and the watchers it triggers) has flushed - re-enable auto-save.
  await nextTick()
  hydrating.value = false
}, { immediate: true })

// Distribute total hours evenly across Mon–Fri, leave Sat/Sun at 0
function distributeHours(total) {
  if (!total || total <= 0) return [0, 0, 0, 0, 0, 0, 0]
  const perDay = Math.round((total / 5) * 10) / 10
  const days = [perDay, perDay, perDay, perDay, perDay, 0, 0]
  // Adjust rounding on Friday
  const sum = days.reduce((a, b) => a + b, 0)
  days[4] = Math.round((days[4] + (total - sum)) * 10) / 10
  return days
}

// Sync rows back to store as flat entries (for submission)
watch([description, rows], () => {
  store.form.description = description.value
  store.form.entries = rows.value.map(r => ({
    project_id: r.project_id,
    stage_id: r.stage_id ?? null,
    subtask_id: r.subtask_id ?? null,
    hours: rowTotalForRow(r),
    description: r.description,
    daily: [...r.daily]
  }))
}, { deep: true })

// Auto-save draft on changes - but never during hydration, and never an empty
// form (which would clobber a real saved draft). To clear a draft, use Discard.
watch([description, rows], () => {
  if (hydrating.value) return
  if (!formHasContent()) return
  saveTsDraft({
    description: description.value,
    rows: JSON.parse(JSON.stringify(rows.value))
  })
}, { deep: true })

function padDaily(arr) {
  // Handle legacy 5-day drafts: pad to 7 with zeros
  if (!arr) return [0, 0, 0, 0, 0, 0, 0]
  const a = [...arr]
  while (a.length < 7) a.push(0)
  return a.slice(0, 7)
}

function restoreTsDraft() {
  const d = restorableDraft.value || tsDraft.value
  if (!d) return
  description.value = d.description || ''
  if (d.rows) {
    rows.value = d.rows.map(r => ({
      project_id: r.project_id,
      stage_id: r.stage_id ?? null,
      subtask_id: r.subtask_id ?? null,
      daily: padDaily(r.daily),
      description: r.description || ''
    }))
    for (const id of new Set(rows.value.map(r => r.project_id).filter(Boolean))) ensureStages(id)
  }
  showDraftBanner.value = false
}

function discardTsDraft() {
  clearTsDraft()
  restorableDraft.value = null
  showDraftBanner.value = false
}

// Totals
function rowTotalForRow(row) {
  return Math.round(row.daily.reduce((s, v) => s + (Number(v) || 0), 0) * 10) / 10
}

function rowTotal(ri) {
  return rowTotalForRow(rows.value[ri])
}

function dayTotal(di) {
  return Math.round(rows.value.reduce((s, r) => s + (Number(r.daily[di]) || 0), 0) * 10) / 10
}

const grandTotal = computed(() => {
  return Math.round(rows.value.reduce((s, r) => s + rowTotalForRow(r), 0) * 10) / 10
})

// A row only "counts" once it has a project AND some hours. A project row left
// at 0h means the employee didn't work on it this week - it's ignored, not an
// error (and gets dropped from the payload on submit).
function rowIsActive(r) {
  return !!(r.project_id && rowTotalForRow(r) > 0)
}

// Spell out exactly what's blocking submission, so an employee who has "filled
// everything" can see what's still holding the button disabled. This is also the
// single source of truth for validity (isValid = nothing missing).
const missingItems = computed(() => {
  const out = []
  const active = rows.value.filter(rowIsActive)
  // Hours logged against a row with no project selected would be silently lost.
  if (rows.value.some(r => !r.project_id && rowTotalForRow(r) > 0)) {
    out.push('Select a project for every row that has hours logged.')
  }
  // A stage is required once the project defines any - hours must be
  // attributable to a stage so stage progress and spend stay meaningful.
  if (rows.value.some(r =>
    r.project_id && rowTotalForRow(r) > 0 &&
    stagesFor(r.project_id).length > 0 && !r.stage_id
  )) {
    out.push('Select a stage for every row logged against a project that uses stages.')
  }
  if (active.length === 0) {
    out.push('Log hours for at least one project.')
  }
  if (active.some(r => (r.description || '').trim().length <= 3)) {
    out.push('Add a task description (4+ characters) for each project you logged hours on.')
  }
  if (description.value.trim().length < 20) {
    const n = description.value.trim().length
    out.push(`Write a weekly overview of at least 20 characters (${n}/20).`)
  }
  return out
})

const isValid = computed(() => missingItems.value.length === 0)

const submitLabel = computed(() => {
  if (submitting.value) return 'Submitting...'
  return props.week.status === 'rejected' ? 'Resubmit Timesheet' : 'Submit Timesheet'
})

function getProjectName(pid) {
  if (!pid) return 'Unselected'
  const p = props.projects.find(x => x.id === pid)
  return p ? p.name : `Project #${pid}`
}

function addRow() {
  rows.value.push(makeEmptyRow())
}

function removeRow(index) {
  if (rows.value.length > 1) {
    rows.value.splice(index, 1)
  }
}

async function handleSubmit() {
  if (!isValid.value) return
  submitting.value = true
  try {
    await store.submitTimesheet()
    clearTsDraft()
    emit('submit')
  } catch (err) {
    // Error handled in store
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.form-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.rejected-alert {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: var(--radius-md);
  padding: 16px;
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #dc2626;
  margin-bottom: 8px;
}

.alert-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}

.rejection-reason {
  margin: 0;
  font-size: 14px;
  color: #b91c1c;
  font-style: italic;
}

.timesheet-form {
  display: flex;
  flex-direction: column;
  gap: 32px;
  position: relative;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

label {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: var(--color-on-surface);
}

.section-desc {
  font-size: 13px;
  color: var(--color-on-surface-variant);
  margin: 4px 0 0 0;
}

.btn-add-task {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: var(--color-surface-container);
  color: var(--color-primary);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-add-task:hover {
  background: var(--color-surface-container-high);
  border-color: var(--color-primary);
}

/* ─── Day-by-day Grid Table ─── */
.grid-table-wrapper {
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-md);
  overflow-x: auto;
}

.grid-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.grid-table th {
  background: var(--color-surface-container-low);
  padding: 8px 4px;
  text-align: center;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
  border-bottom: 1px solid var(--color-outline-variant);
}

.grid-table th.col-project {
  text-align: left;
  padding-left: 8px;
  width: 28%;
}

.grid-table th.col-day {
  /* 7 day columns share remaining space equally */
}

.grid-table th.col-day.is-weekend {
  background: #f8f5f0;
}

.grid-table td.day-cell.is-weekend {
  background: #faf8f5;
}

.grid-table th.col-total {
  width: 52px;
  font-weight: 800;
  color: var(--color-on-surface);
}

.grid-table th.col-action {
  width: 36px;
}

.day-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.day-name {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.day-date {
  font-size: 9px;
  font-weight: 500;
  color: var(--color-on-surface-variant);
  text-transform: none;
  letter-spacing: 0;
}

.grid-table td {
  padding: 4px 3px;
  border-bottom: 1px solid var(--color-surface-container-high);
  vertical-align: middle;
}

.grid-table td:first-child {
  padding-left: 8px;
}

/* ── Entry cards (replaces the wide grid table) ── */
.entry-cards { display: flex; flex-direction: column; gap: 12px; }
.entry-card {
  border: 1px solid var(--color-outline); border-radius: var(--radius-xl);
  padding: 14px; background: var(--color-surface); transition: border-color .15s, box-shadow .15s;
}
.entry-card.filled { border-color: var(--color-primary); box-shadow: 0 0 0 3px rgba(40,116,117,.06); }

.ec-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; flex-wrap: wrap; }
.ec-selects { display: flex; align-items: center; gap: 4px; flex: 1; flex-wrap: wrap; min-width: 0; }
.ec-select {
  padding: 8px 10px; border: 1px solid var(--color-outline); border-radius: var(--radius-md);
  font-size: 13px; background: var(--color-surface); color: var(--color-on-surface);
  outline: none; max-width: 100%;
}
.ec-select:focus { border-color: var(--color-primary); }
.ec-project { font-weight: 700; min-width: 160px; }
.ec-stage, .ec-sub { font-size: 12px; background: var(--color-surface-container-lowest, #f8fafc); }
/* A staged project with hours but no stage picked - flag it before submit. */
.ec-select.missing { border-color: #dc2626; background: #fef2f2; }
.ec-arrow { font-size: 16px; color: var(--color-outline); flex-shrink: 0; }

.ec-right { display: flex; align-items: center; gap: 8px; margin-left: auto; }
.ec-total {
  font-variant-numeric: tabular-nums; font-weight: 800; font-size: 15px;
  color: var(--color-on-surface-variant); min-width: 46px; text-align: right;
}
.ec-total.on { color: var(--color-primary); }
.ec-remove {
  width: 30px; height: 30px; display: inline-flex; align-items: center; justify-content: center;
  border: 1px solid transparent; border-radius: var(--radius-md); background: none; cursor: pointer;
  color: var(--color-on-surface-variant);
}
.ec-remove:hover:not(:disabled) { background: #fee2e2; color: #dc2626; }
.ec-remove:disabled { opacity: .3; cursor: not-allowed; }
.ec-remove .material-symbols-outlined { font-size: 17px; }

.ec-days { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; }
.ec-day {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 7px 4px; border-radius: var(--radius-md);
  background: var(--color-surface-container-lowest, #f8fafc); cursor: text;
}
.ec-day.weekend { background: #fef9f3; }
.ec-day-name { font-size: 10px; font-weight: 800; text-transform: uppercase; color: var(--color-on-surface-variant); }
.ec-day-date { font-size: 9px; color: var(--color-on-surface-variant); opacity: .75; }
.ec-day-input {
  width: 100%; margin-top: 3px; padding: 5px 2px; text-align: center;
  border: 1px solid var(--color-outline); border-radius: 5px;
  font-size: 13px; font-weight: 700; font-variant-numeric: tabular-nums;
  background: var(--color-surface); color: var(--color-on-surface); outline: none;
  -moz-appearance: textfield;
}
.ec-day-input::-webkit-outer-spin-button,
.ec-day-input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
.ec-day-input:focus { border-color: var(--color-primary); }

.ec-desc {
  width: 100%; margin-top: 10px; padding: 8px 10px;
  border: 1px solid var(--color-outline); border-radius: var(--radius-md);
  font-size: 13px; background: var(--color-surface); color: var(--color-on-surface); outline: none;
}
.ec-desc:focus { border-color: var(--color-primary); }

/* Week totals strip */
.week-totals {
  display: flex; align-items: center; gap: 12px; margin-top: 12px;
  padding: 10px 14px; border-radius: var(--radius-lg);
  background: var(--color-surface-container-lowest, #f8fafc); border: 1px solid var(--color-outline);
}
.wt-label { font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: .05em; color: var(--color-on-surface-variant); }
.wt-days { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; flex: 1; }
.wt-day {
  display: flex; flex-direction: column; align-items: center;
  font-size: 12px; font-weight: 700; font-variant-numeric: tabular-nums; color: var(--color-on-surface);
}
.wt-day small { font-size: 9px; font-weight: 700; text-transform: uppercase; color: var(--color-on-surface-variant); }
.wt-day.zero { color: var(--color-on-surface-variant); font-weight: 500; }
.wt-day.over-8 { color: #b45309; }
.wt-day.weekend small { color: #c2820a; }
.wt-grand { font-size: 17px; font-weight: 800; font-variant-numeric: tabular-nums; color: var(--color-on-surface-variant); }
.wt-grand.on { color: var(--color-primary); }

@media (max-width: 720px) {
  .ec-days { grid-template-columns: repeat(4, 1fr); }
  .wt-days { grid-template-columns: repeat(4, 1fr); }
  .ec-project { min-width: 100%; }
}

.form-select {
  width: 100%;
  padding: 5px 4px;
  border: 1px solid var(--color-outline-variant);
  border-radius: 4px;
  font-size: 12px;
  color: var(--color-on-surface);
  background: var(--color-surface);
}

.form-select:focus {
  border-color: var(--color-primary);
  outline: none;
}

.day-cell {
  text-align: center;
}

.day-input {
  width: 100%;
  max-width: 48px;
  padding: 5px 2px;
  border: 1px solid var(--color-outline-variant);
  border-radius: 4px;
  font-size: 13px;
  font-weight: 600;
  text-align: center;
  color: var(--color-on-surface);
  background: var(--color-surface);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.day-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-primary-light);
  outline: none;
}

.day-input::placeholder {
  color: var(--color-outline);
  font-weight: 400;
}

/* Hide spinner arrows on number inputs */
.day-input::-webkit-inner-spin-button,
.day-input::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
.day-input[type="number"] {
  -moz-appearance: textfield;
}

.row-total {
  text-align: center;
  font-weight: 700;
  font-size: 12px;
  color: var(--color-on-surface-variant);
  background: var(--color-surface-container-lowest);
}

.row-total.has-hours {
  color: var(--color-primary);
}

.btn-remove {
  padding: 4px;
  background: none;
  border: none;
  color: var(--color-on-surface-variant);
  cursor: pointer;
}

.btn-remove:hover:not(:disabled) {
  color: #dc2626;
}

.btn-remove:disabled {
  opacity: 0.3;
}

/* Footer totals */
.grid-table tfoot td {
  background: var(--color-surface-container-low);
  border-top: 2px solid var(--color-outline-variant);
  border-bottom: none;
}

.total-label {
  text-align: right;
  font-weight: 700;
  font-size: 12px;
  padding-right: 12px !important;
  color: var(--color-on-surface-variant);
}

.day-total {
  text-align: center;
  font-weight: 700;
  font-size: 13px;
  color: var(--color-on-surface);
}

.day-total.over-8 {
  color: #dc2626;
}

.grand-total {
  text-align: center;
  font-weight: 800;
  font-size: 15px;
  color: var(--color-primary);
}

.grand-total.text-success {
  color: var(--color-primary);
}

/* ─── Description rows ─── */
.desc-rows {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.desc-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.desc-project-name {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-on-surface);
  min-width: 140px;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.form-input {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid var(--color-outline-variant);
  border-radius: 4px;
  font-size: 13px;
  color: var(--color-on-surface);
  background: var(--color-surface);
}

.form-input:focus {
  border-color: var(--color-primary);
  outline: none;
}

/* ─── Rest of form ─── */
textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-on-surface);
  background: var(--color-surface);
  resize: vertical;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  padding-top: 16px;
  border-top: 1px dashed var(--color-outline-variant);
}

.submit-hint {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-right: auto;
  padding: 10px 14px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: var(--radius-md);
  color: #1e40af;
  font-size: 12.5px;
}
.submit-hint .material-symbols-outlined { font-size: 18px; flex-shrink: 0; margin-top: 1px; }
.submit-hint-title { font-weight: 700; }
.submit-hint ul { margin: 4px 0 0; padding-left: 16px; }
.submit-hint li { margin: 2px 0; }

.btn-submit {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-submit:hover:not(:disabled) {
  background: #1a4e4f;
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(255,255,255,0.8);
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--color-primary);
  font-weight: 600;
}

.required {
  color: #dc2626;
}

.char-count {
  font-size: 11px;
  color: #dc2626;
  margin-top: 4px;
  text-align: right;
}

.rotating {
  animation: spin 1.5s linear infinite;
}

@keyframes spin { 100% { transform: rotate(360deg); } }

/* Draft banner */
.draft-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  margin-bottom: 4px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 13px;
  color: #92400e;
}
.draft-banner .material-symbols-outlined { font-size: 18px; flex-shrink: 0; }
.draft-restore-btn {
  margin-left: auto;
  padding: 5px 12px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}
.draft-restore-btn:hover { opacity: 0.88; }
.draft-discard-btn {
  padding: 5px 12px;
  background: none;
  border: 1px solid #d97706;
  color: #d97706;
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}
.draft-discard-btn:hover { background: #fef3c7; }
</style>
