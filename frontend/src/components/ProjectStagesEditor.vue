<template>
  <div class="pse">
    <!-- Running bucket: stages divide the full project cost (advance is not
         deducted). What's left to allocate is always visible. -->
    <div class="pse-bucket">
      <div class="bk-item bk-item--strong">
        <span class="bk-label">Total project cost</span>
        <span class="bk-value">{{ inr(data.bucket) }}</span>
      </div>
      <div class="bk-item">
        <span class="bk-label">Advance received</span>
        <span class="bk-value">{{ inr(data.advance_amount) }}</span>
      </div>
      <div class="bk-spacer"></div>
      <div class="bk-item bk-item--remaining" :class="{ full: remainingPct <= 0 }">
        <span class="bk-label">Unallocated</span>
        <span class="bk-value">
          {{ inr(data.remaining_amount) }}
          <small>· {{ fmtPct(remainingPct) }}% · {{ fmtHours(data.remaining_hours) }}h</small>
        </span>
      </div>
    </div>

    <!-- Allocation bar -->
    <div class="pse-bar" :title="`${fmtPct(allocatedPct)}% allocated`">
      <div
        v-for="s in data.stages"
        :key="'bar-' + s.id"
        class="bar-seg"
        :style="{ width: s.percentage + '%', background: segColor(s) }"
        :title="`${s.name} - ${fmtPct(s.percentage)}%`"
      ></div>
    </div>

    <!-- Stage rows -->
    <div v-if="data.stages.length" class="pse-rows">
      <div v-for="s in data.stages" :key="s.id" class="stage-row" :class="{ done: s.status === 'completed' }">
        <button class="row-toggle" @click="toggle(s.id)" :aria-expanded="isOpen(s.id)">
          <span class="material-symbols-outlined chev" :class="{ open: isOpen(s.id) }">chevron_right</span>
        </button>

        <div class="row-main" @click="toggle(s.id)">
          <div class="row-line1">
            <span class="stage-name">{{ s.name }}</span>
            <span v-if="s.created_by_role" class="role-chip">{{ roleLabel(s.created_by_role) }}</span>
            <span v-if="s.status === 'completed'" class="done-chip">
              <span class="material-symbols-outlined">check_circle</span> Complete
            </span>
          </div>
          <div class="row-line2">
            <span class="pct-pill">{{ fmtPct(s.percentage) }}%</span>
            <span class="mono">{{ inr(s.amount) }}</span>
            <span class="mono muted">{{ fmtHours(s.hours) }} h</span>
            <span class="sep">·</span>
            <span class="completion" :class="completionClass(s)">
              {{ s.completion_percent }}% complete
              <small v-if="s.subtask_total">({{ s.subtask_completed }}/{{ s.subtask_total }} subtasks)</small>
              <small v-else>(no subtasks)</small>
            </span>
          </div>
          <div class="mini-bar"><div class="mini-fill" :style="{ width: s.completion_percent + '%' }"></div></div>
        </div>

        <div class="row-actions" @click.stop>
          <button
            v-if="canEditStages"
            class="icon-btn"
            :title="s.status === 'completed' ? 'Reopen stage' : 'Mark stage complete'"
            @click="toggleStageComplete(s)"
          >
            <span class="material-symbols-outlined">{{ s.status === 'completed' ? 'undo' : 'task_alt' }}</span>
          </button>
          <button v-if="canEditStages" class="icon-btn" title="Edit stage" @click="startEdit(s)">
            <span class="material-symbols-outlined">edit</span>
          </button>
          <button v-if="canEditStages" class="icon-btn danger" title="Delete stage" @click="removeStage(s)">
            <span class="material-symbols-outlined">delete</span>
          </button>
        </div>

        <!-- Expanded: subtasks + who worked on them -->
        <div v-if="isOpen(s.id)" class="row-detail">
          <div v-if="editingId === s.id" class="edit-form">
            <input v-model="editName" class="inp" placeholder="Stage name" />
            <input v-model.number="editPct" type="number" min="0.01" step="0.01" class="inp inp-sm" placeholder="%" />
            <button class="btn-mini primary" @click="saveEdit(s)">Save</button>
            <button class="btn-mini" @click="editingId = null">Cancel</button>
          </div>

          <div class="sub-head">
            <span>Subtasks</span>
            <button v-if="canEditSubtasks" class="btn-mini" @click="startAddSub(s.id)">
              <span class="material-symbols-outlined">add</span> Add subtask
            </button>
          </div>

          <div v-if="addingFor === s.id" class="sub-add">
            <input v-model="newSub.title" class="inp" placeholder="Subtask title" @keyup.enter="submitSub(s.id)" />
            <input v-model="newSub.due_date" type="date" class="inp inp-date" />
            <button class="btn-mini primary" :disabled="!newSub.title" @click="submitSub(s.id)">Add</button>
            <button class="btn-mini" @click="addingFor = null">Cancel</button>
          </div>

          <ul v-if="s.subtasks.length" class="sub-list">
            <li v-for="t in s.subtasks" :key="t.id" class="sub-item" :class="{ done: t.status === 'completed' }">
              <button
                class="sub-check"
                :class="{ checked: t.status === 'completed' }"
                :disabled="!canEditSubtasks"
                :title="canEditSubtasks ? 'Toggle complete' : 'Only an admin or PM can complete this'"
                @click="toggleSub(t)"
              >
                <span v-if="t.status === 'completed'" class="material-symbols-outlined">check</span>
              </button>
              <!-- Inline edit: title + deadline -->
              <div v-if="editingSubId === t.id" class="sub-edit">
                <input v-model="editSubTitle" class="inp" placeholder="Subtask title"
                       @keyup.enter="saveSubEdit(t)" />
                <input v-model="editSubDue" type="date" class="inp inp-date" />
                <button class="btn-mini primary" :disabled="!editSubTitle.trim()" @click="saveSubEdit(t)">Save</button>
                <button class="btn-mini" @click="editingSubId = null">Cancel</button>
              </div>
              <div v-else class="sub-body">
                <div class="sub-title">{{ t.title }}</div>
                <div class="sub-meta">
                  <span v-if="t.due_date" :class="{ late: t.is_overdue }">
                    <span class="material-symbols-outlined">event</span>{{ fmtDate(t.due_date) }}
                    <template v-if="t.is_overdue">· {{ t.days_overdue }}d late</template>
                  </span>
                  <span v-if="t.created_by_role" class="role-chip sm">{{ roleLabel(t.created_by_role) }}</span>
                  <!-- Who logged hours against this subtask -->
                  <span v-if="t.workers && t.workers.length" class="workers">
                    <span class="material-symbols-outlined">group</span>
                    <button
                      v-for="w in t.workers"
                      :key="w.name"
                      class="worker-chip"
                      :title="`${w.hours}h logged - view timesheets`"
                      @click="$emit('view-worker', w)"
                    >{{ w.name }} · {{ w.hours }}h</button>
                  </span>
                </div>
              </div>
              <button v-if="canEditSubtasks && editingSubId !== t.id" class="icon-btn sm"
                      title="Edit subtask" @click="startEditSub(t)">
                <span class="material-symbols-outlined">edit</span>
              </button>
              <button v-if="canEditSubtasks" class="icon-btn danger sm" title="Delete" @click="removeSub(t)">
                <span class="material-symbols-outlined">close</span>
              </button>
            </li>
          </ul>
          <p v-else class="sub-empty">No subtasks yet.</p>
        </div>
      </div>
    </div>
    <p v-else class="pse-empty">No stages defined yet.</p>

    <!-- Add stage -->
    <div v-if="canEditStages" class="pse-add">
      <input v-model="newStage.name" class="inp" placeholder="Stage name (e.g. DD)" @keyup.enter="submitStage" />
      <div class="pct-wrap">
        <input v-model.number="newStage.percentage" type="number" min="0.01" :max="remainingPct"
               step="0.01" class="inp inp-sm" placeholder="%" @keyup.enter="submitStage" />
        <span class="pct-sign">%</span>
      </div>
      <div class="preview" v-if="previewValid">
        = <strong>{{ inr(previewAmount) }}</strong> · {{ fmtHours(previewHours) }} h
      </div>
      <button class="btn-mini primary" :disabled="!canSubmitStage" @click="submitStage">
        <span class="material-symbols-outlined">add</span> Add stage
      </button>
    </div>

    <!-- Overboard warning -->
    <div v-if="overboard" class="pse-warn">
      <span class="material-symbols-outlined">warning</span>
      That would allocate <strong>{{ fmtPct(allocatedPct + (Number(newStage.percentage) || 0)) }}%</strong>
      of the project - only <strong>{{ fmtPct(remainingPct) }}%</strong> ({{ inr(data.remaining_amount) }}) is left.
    </div>

    <p v-if="errorMsg" class="pse-error">{{ errorMsg }}</p>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { stagesAPI } from '../api/stages'

const props = defineProps({
  // Payload from GET /projects/:id/stages
  data: { type: Object, required: true },
  canEditStages: { type: Boolean, default: false },   // admin only
  canEditSubtasks: { type: Boolean, default: false }, // admin or PM
})
const emit = defineEmits(['changed', 'view-worker'])

const PALETTE = ['#287475', '#3b82f6', '#a855f7', '#f59e0b', '#059669', '#0ea5e9', '#dc2626', '#6366f1']

const open = ref({})
const editingId = ref(null)
const editName = ref('')
const editPct = ref(null)
const addingFor = ref(null)
const newSub = ref({ title: '', due_date: '' })
const newStage = ref({ name: '', percentage: null })
const editingSubId = ref(null)
const editSubTitle = ref('')
const editSubDue = ref('')
const errorMsg = ref('')

const allocatedPct = computed(() => Number(props.data.allocated_percent) || 0)
const remainingPct = computed(() => Number(props.data.remaining_percent) || 0)

const overboard = computed(() => {
  const p = Number(newStage.value.percentage) || 0
  return p > 0 && p > remainingPct.value + 1e-9
})
const previewValid = computed(() => (Number(newStage.value.percentage) || 0) > 0 && !overboard.value)
const previewAmount = computed(() =>
  (Number(props.data.bucket) || 0) * (Number(newStage.value.percentage) || 0) / 100)
const previewHours = computed(() =>
  (Number(props.data.total_hours) || 0) * (Number(newStage.value.percentage) || 0) / 100)
const canSubmitStage = computed(() =>
  !!newStage.value.name.trim() && (Number(newStage.value.percentage) || 0) > 0 && !overboard.value)

// Someone who can manage subtasks but not stages (a PM) is here for the
// subtasks - open every stage so they're actionable without extra clicks.
const subtaskFocused = computed(() => props.canEditSubtasks && !props.canEditStages)
watch(
  () => props.data?.stages?.map(s => s.id).join(','),
  () => {
    if (!subtaskFocused.value) return
    const next = { ...open.value }
    for (const s of props.data?.stages || []) {
      if (next[s.id] === undefined) next[s.id] = true
    }
    open.value = next
  },
  { immediate: true },
)

function segColor(s) {
  const i = props.data.stages.findIndex(x => x.id === s.id)
  return s.status === 'completed' ? '#059669' : PALETTE[i % PALETTE.length]
}
function isOpen(id) { return !!open.value[id] }
function toggle(id) { open.value = { ...open.value, [id]: !open.value[id] } }
function roleLabel(r) {
  return r === 'project_manager' ? 'PM' : r === 'admin' ? 'Admin' : 'Employee'
}
function completionClass(s) {
  if (s.completion_percent >= 100) return 'good'
  if (s.completion_percent > 0) return 'mid'
  return ''
}
const inrFmt = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
function inr(v) { return inrFmt.format(Number(v) || 0) }
function fmtPct(v) { const n = Number(v) || 0; return Number.isInteger(n) ? n : n.toFixed(2).replace(/\.?0+$/, '') }
function fmtHours(v) { const n = Number(v) || 0; return Number.isInteger(n) ? n : n.toFixed(1) }
function fmtDate(d) {
  return d ? new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) : ''
}

function fail(e, fallback) {
  errorMsg.value = e?.response?.data?.detail || fallback
  setTimeout(() => { errorMsg.value = '' }, 6000)
}

async function submitStage() {
  if (!canSubmitStage.value) return
  try {
    await stagesAPI.create(props.data.project_id, {
      name: newStage.value.name.trim(),
      percentage: Number(newStage.value.percentage),
    })
    newStage.value = { name: '', percentage: null }
    emit('changed')
  } catch (e) { fail(e, 'Could not add the stage.') }
}

function startEdit(s) {
  editingId.value = s.id
  editName.value = s.name
  editPct.value = s.percentage
  open.value = { ...open.value, [s.id]: true }
}
async function saveEdit(s) {
  try {
    await stagesAPI.update(s.id, { name: editName.value.trim(), percentage: Number(editPct.value) })
    editingId.value = null
    emit('changed')
  } catch (e) { fail(e, 'Could not save the stage.') }
}
async function removeStage(s) {
  if (!confirm(`Delete stage "${s.name}"? Its ${s.subtask_total} subtask(s) will be deleted too.`)) return
  try {
    await stagesAPI.remove(s.id)
    emit('changed')
  } catch (e) { fail(e, 'Could not delete the stage.') }
}
async function toggleStageComplete(s) {
  try {
    await stagesAPI.update(s.id, { status: s.status === 'completed' ? 'active' : 'completed' })
    emit('changed')
  } catch (e) { fail(e, 'Could not update the stage.') }
}

function startAddSub(stageId) {
  addingFor.value = stageId
  newSub.value = { title: '', due_date: '' }
  open.value = { ...open.value, [stageId]: true }
}
async function submitSub(stageId) {
  if (!newSub.value.title) return
  try {
    await stagesAPI.createSubtask(stageId, {
      title: newSub.value.title.trim(),
      due_date: newSub.value.due_date || null,
    })
    newSub.value = { title: '', due_date: '' }
    addingFor.value = null
    emit('changed')
  } catch (e) { fail(e, 'Could not add the subtask.') }
}
function startEditSub(t) {
  editingSubId.value = t.id
  editSubTitle.value = t.title
  editSubDue.value = t.due_date || ''
}

async function saveSubEdit(t) {
  const title = editSubTitle.value.trim()
  if (!title) return
  try {
    await stagesAPI.updateSubtask(t.id, { title, due_date: editSubDue.value || null })
    editingSubId.value = null
    emit('changed')
  } catch (e) { fail(e, 'Could not save the subtask.') }
}

async function toggleSub(t) {
  try {
    await stagesAPI.updateSubtask(t.id, { status: t.status === 'completed' ? 'pending' : 'completed' })
    emit('changed')
  } catch (e) { fail(e, 'Could not update the subtask.') }
}
async function removeSub(t) {
  try {
    await stagesAPI.removeSubtask(t.id)
    emit('changed')
  } catch (e) { fail(e, 'Could not delete the subtask.') }
}
</script>

<style scoped>
.pse { display: flex; flex-direction: column; gap: 14px; }

/* Bucket strip */
.pse-bucket {
  display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
  padding: 14px 16px; background: var(--color-surface-container-lowest, #f8fafc);
  border: 1px solid var(--color-outline); border-radius: var(--radius-lg);
}
.bk-item { display: flex; flex-direction: column; gap: 2px; }
.bk-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; color: var(--color-on-surface-variant); }
.bk-value { font-size: 15px; font-weight: 700; font-variant-numeric: tabular-nums; color: var(--color-on-surface); }
.bk-value small { font-size: 11px; font-weight: 600; color: var(--color-on-surface-variant); }
.bk-item--strong .bk-value { color: var(--color-primary); }
.bk-op { font-size: 16px; color: var(--color-on-surface-variant); font-weight: 700; }
.bk-spacer { flex: 1; }
.bk-item--remaining { text-align: right; }
.bk-item--remaining .bk-value { color: #b45309; }
.bk-item--remaining.full .bk-value { color: #059669; }

/* Allocation bar */
.pse-bar { display: flex; height: 8px; border-radius: 999px; overflow: hidden; background: var(--color-outline-variant); }
.bar-seg { height: 100%; }

/* Stage rows */
.pse-rows { display: flex; flex-direction: column; gap: 8px; }
.stage-row {
  display: grid; grid-template-columns: 28px 1fr auto; align-items: start;
  border: 1px solid var(--color-outline); border-radius: var(--radius-lg);
  padding: 10px 12px; background: var(--color-surface);
}
.stage-row.done { background: #f0fdf4; border-color: #bbf7d0; }
.row-toggle { background: none; border: none; cursor: pointer; padding: 2px; color: var(--color-on-surface-variant); }
.chev { transition: transform .15s; font-size: 20px; }
.chev.open { transform: rotate(90deg); }
.row-main { cursor: pointer; min-width: 0; }
.row-line1 { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.stage-name { font-weight: 700; font-size: 14px; color: var(--color-on-surface); }
.role-chip {
  font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em;
  background: var(--color-surface-container); color: var(--color-on-surface-variant);
  padding: 2px 6px; border-radius: 999px;
}
.role-chip.sm { font-size: 8px; }
.done-chip { display: inline-flex; align-items: center; gap: 3px; font-size: 11px; font-weight: 700; color: #059669; }
.done-chip .material-symbols-outlined { font-size: 14px; }
.row-line2 { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-top: 3px; font-size: 12px; }
.pct-pill { background: var(--color-primary-light, #e6f0f0); color: var(--color-primary); font-weight: 700; padding: 1px 8px; border-radius: 999px; }
.mono { font-variant-numeric: tabular-nums; font-weight: 600; color: var(--color-on-surface); }
.mono.muted { color: var(--color-on-surface-variant); font-weight: 500; }
.sep { color: var(--color-outline); }
.completion { font-weight: 600; color: var(--color-on-surface-variant); }
.completion.good { color: #059669; }
.completion.mid { color: #b45309; }
.completion small { font-weight: 500; opacity: .8; }
.mini-bar { height: 4px; border-radius: 999px; background: var(--color-outline-variant); margin-top: 6px; overflow: hidden; }
.mini-fill { height: 100%; background: #059669; transition: width .2s; }

.row-actions { display: flex; gap: 2px; }
.icon-btn {
  width: 28px; height: 28px; display: inline-flex; align-items: center; justify-content: center;
  border: 1px solid transparent; border-radius: var(--radius-md); background: none; cursor: pointer;
  color: var(--color-on-surface-variant);
}
.icon-btn:hover { background: var(--color-surface-container); }
.icon-btn.danger:hover { background: #fee2e2; color: #dc2626; }
.icon-btn .material-symbols-outlined { font-size: 16px; }
.icon-btn.sm { width: 22px; height: 22px; }
.icon-btn.sm .material-symbols-outlined { font-size: 14px; }

/* Expanded detail */
.row-detail { grid-column: 1 / -1; margin-top: 10px; padding-top: 10px; border-top: 1px dashed var(--color-outline-variant); }
.sub-head { display: flex; justify-content: space-between; align-items: center; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; color: var(--color-on-surface-variant); margin-bottom: 8px; }
.sub-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 4px; }
.sub-item { display: flex; align-items: flex-start; gap: 8px; padding: 6px 4px; border-radius: var(--radius-md); }
.sub-item:hover { background: var(--color-surface-container-lowest, #f8fafc); }
.sub-item.done .sub-title { text-decoration: line-through; color: var(--color-on-surface-variant); }
.sub-check {
  width: 17px; height: 17px; flex-shrink: 0; margin-top: 2px;
  border: 2px solid var(--color-outline); border-radius: 4px; background: var(--color-surface);
  cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 0;
}
.sub-check.checked { background: var(--color-primary); border-color: var(--color-primary); }
.sub-check:disabled { cursor: not-allowed; opacity: .6; }
.sub-check .material-symbols-outlined { font-size: 11px; color: #fff; }
.sub-body { flex: 1; min-width: 0; }
.sub-edit { flex: 1; display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.sub-title { font-size: 13px; font-weight: 600; color: var(--color-on-surface); }
.sub-meta { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 2px; font-size: 11px; color: var(--color-on-surface-variant); }
.sub-meta .material-symbols-outlined { font-size: 12px; vertical-align: -2px; }
.sub-meta .late { color: #dc2626; font-weight: 700; }
.workers { display: inline-flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.worker-chip {
  background: var(--color-primary-light, #e6f0f0); color: var(--color-primary);
  border: none; border-radius: 999px; padding: 1px 8px; font-size: 10px; font-weight: 700; cursor: pointer;
}
.worker-chip:hover { text-decoration: underline; }
.sub-empty, .pse-empty { font-size: 12px; font-style: italic; color: var(--color-on-surface-variant); margin: 4px 0; }

/* Add / edit forms */
.pse-add, .sub-add, .edit-form { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.sub-add, .edit-form { margin-bottom: 10px; }
.inp {
  padding: 7px 10px; border: 1px solid var(--color-outline); border-radius: var(--radius-md);
  font-size: 13px; background: var(--color-surface); color: var(--color-on-surface); outline: none; min-width: 0; flex: 1;
}
.inp:focus { border-color: var(--color-primary); }
.inp-sm { flex: 0 0 90px; }
.inp-date { flex: 0 0 150px; }
.pct-wrap { display: flex; align-items: center; gap: 4px; }
.pct-sign { font-size: 13px; font-weight: 700; color: var(--color-on-surface-variant); }
.preview { font-size: 12px; color: var(--color-primary); font-weight: 600; }
.btn-mini {
  display: inline-flex; align-items: center; gap: 4px; padding: 7px 12px;
  border: 1px solid var(--color-outline); border-radius: var(--radius-md);
  background: var(--color-surface); font-size: 12px; font-weight: 700; cursor: pointer;
  color: var(--color-on-surface-variant); white-space: nowrap;
}
.btn-mini.primary { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }
.btn-mini:disabled { opacity: .5; cursor: not-allowed; }
.btn-mini .material-symbols-outlined { font-size: 15px; }

.pse-warn {
  display: flex; align-items: center; gap: 8px; padding: 10px 14px;
  background: #fef2f2; border: 1px solid #fecaca; border-radius: var(--radius-md);
  font-size: 12px; color: #991b1b;
}
.pse-warn .material-symbols-outlined { font-size: 17px; }
.pse-error { font-size: 12px; color: var(--color-error, #dc2626); margin: 0; }

@media (max-width: 768px) {
  .stage-row { grid-template-columns: 24px 1fr auto; }
  .pse-bucket { gap: 10px; }
  .bk-op { display: none; }
}
</style>
