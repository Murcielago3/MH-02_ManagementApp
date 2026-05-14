<template>
  <AppLayout>
    <div class="page-header">
      <div>
        <h1 class="page-title">Project Summary</h1>
        <p class="page-sub">Employee spend and partner remuneration by project</p>
      </div>
    </div>

    <div class="split-layout">
      <aside class="col-left">
        <ProjectSelector v-model:selectedProjectId="selectedProjectId" />
      </aside>
      <section class="col-right">
        <transition name="fade-panel" mode="out-in">
          <div v-if="!selectedProjectId" key="empty" class="empty-center">
            <span class="material-symbols-outlined empty-ic">summarize</span>
            <p>Select a project to view its summary</p>
          </div>

          <div v-else-if="summaryLoading" key="load" class="detail-skeleton">
            <div class="sk-h1" />
            <div class="sk-sub" />
            <div class="sk-table" />
          </div>

          <div v-else-if="summaryError" key="err" class="empty-center text-error">
            {{ summaryError }}
          </div>

          <div v-else key="content" class="detail-content">
            <div class="detail-toolbar">
              <div class="header-block">
                <h2 class="detail-title">{{ apiSummary.project_name }}</h2>
                <p class="detail-sub">
                  {{ summaryProjectMeta?.project_number }} · {{ summaryProjectMeta?.year || '—' }}
                </p>
                <div class="header-meta">
                  <span class="dot" :style="{ background: summaryProjectMeta?.color || '#287475' }" />
                  <span class="stage-badge" :class="stageClass(summaryProjectMeta?.current_stage)">
                    {{ summaryProjectMeta?.current_stage || 'N/A' }}
                  </span>
                </div>
              </div>
              <button type="button" class="btn-primary" @click="openAddModal">Add Employee to Project</button>
            </div>

            <div v-if="showTimesheetHint" class="info-banner">
              <span class="material-symbols-outlined">info</span>
              Hours come from approved weekly timesheets only. They will appear here once timesheets are approved.
            </div>

            <div v-if="timesheetHoursNote" class="info-banner subtle">
              <span class="material-symbols-outlined">schedule</span>
              {{ timesheetHoursNote }}
            </div>

            <div class="table-card">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Employee</th>
                    <th>Designation</th>
                    <th class="num">Base Pay/mo</th>
                    <th class="num">Rate/hr</th>
                    <th class="num">Hours Worked</th>
                    <th class="num">Total Spent</th>
                    <th class="actions-col">Pay</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="!shownRows.length">
                    <td colspan="7" class="empty-row">No approved timesheet hours on this project yet.</td>
                  </tr>
                  <tr v-for="row in shownRows" :key="row.employee_id">
                    <td>{{ row.name }}</td>
                    <td>{{ row.designation || '—' }}</td>
                    <td class="num tab">
                      <template v-if="row.assignment_id && drafts[row.assignment_id]">
                        <input
                          v-model.number="drafts[row.assignment_id].base_pay"
                          @input="onBasePayInput(row.assignment_id)"
                          type="number"
                          min="0"
                          step="100"
                          class="cell-input"
                        />
                      </template>
                      <template v-else>{{ formatInr(row.base_pay, 0) }}</template>
                    </td>
                    <td class="num tab">
                      <template v-if="row.assignment_id && drafts[row.assignment_id]">
                        <input
                          v-model.number="drafts[row.assignment_id].hourly_rate"
                          type="number"
                          min="0"
                          step="0.01"
                          class="cell-input narrow"
                        />
                      </template>
                      <template v-else>{{ formatInrPerHour(row.hourly_rate) }}</template>
                    </td>
                    <td class="num tab">{{ formatHours(row.hours_worked) }}</td>
                    <td class="num tab">{{ formatInr(row.display_spent, 0) }}</td>
                    <td class="actions-col">
                      <button
                        v-if="row.assignment_id"
                        type="button"
                        class="btn-row-save"
                        :disabled="savingAssignmentId === row.assignment_id"
                        @click="saveAssignmentRow(row)"
                      >
                        {{ savingAssignmentId === row.assignment_id ? '…' : 'Save' }}
                      </button>
                      <span v-else class="muted-xs">Assign in Projects to edit pay</span>
                    </td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr class="total-row">
                    <td colspan="2"><strong>TOTAL</strong></td>
                    <td class="num">—</td>
                    <td class="num">—</td>
                    <td class="num tab"><strong>{{ formatHours(displayTotals.total_hours) }}</strong></td>
                    <td class="num tab"><strong>{{ formatInr(displayTotals.total_spent, 0) }}</strong></td>
                    <td></td>
                  </tr>
                </tfoot>
              </table>
            </div>

            <div class="tag-row">
              <span class="tag-label expense">Total Employee Spend</span>
              <span class="type-tag expense">EXPENSE</span>
            </div>

            <div class="partner-card">
              <div class="partner-head">
                <span class="tag-label profit">Partner Remuneration</span>
                <span class="type-tag profit">PROFIT</span>
              </div>
              <div class="partner-grid">
                <div>
                  <span class="muted">Partner Rate</span>
                  <div class="val">{{ formatInrPerHour(displayPartnerHourly) }}</div>
                </div>
                <div>
                  <span class="muted">Total Hours (from table above)</span>
                  <div class="val">{{ formatHours(displayTotals.total_hours) }}</div>
                </div>
                <div>
                  <span class="muted">Partner Cost</span>
                  <div class="val">{{ formatInr(displayPartnerCost, 0) }}</div>
                </div>
              </div>

              <div v-if="!partnerRateSet" class="partner-warn">
                <span class="material-symbols-outlined">warning</span>
                Partner rate not set
                <template v-if="!editingPartnerRate">
                  <button type="button" class="btn-inline" @click="startEditPartnerRate">Set Rate</button>
                </template>
                <div v-else class="inline-rate">
                  <span class="rupee">₹</span>
                  <input v-model.number="partnerRateInput" type="number" min="0" step="1" class="rate-inp" />
                  <span class="per">/hr</span>
                  <button type="button" class="btn-primary sm" :disabled="savingPartnerRate" @click="savePartnerRate">
                    {{ savingPartnerRate ? '…' : 'Save' }}
                  </button>
                  <button type="button" class="btn-ghost sm" @click="editingPartnerRate = false">Cancel</button>
                </div>
              </div>
            </div>

            <div class="grand-total">
              <div class="grand-line" />
              <div class="grand-row">
                <span>Grand Total</span>
                <strong>{{ formatInr(displayGrandTotal, 0) }}</strong>
              </div>
              <p class="grand-note">Employee Spend + Partner Remuneration</p>
              <div class="grand-line" />
            </div>
          </div>
        </transition>
      </section>
    </div>

    <!-- Add employee modal -->
    <Teleport to="body">
      <div v-if="addModalOpen" class="modal-backdrop" @click.self="addModalOpen = false">
        <div class="modal">
          <div class="modal-header">
            <h3 class="modal-title">Add employee to project</h3>
            <button type="button" class="modal-close" @click="addModalOpen = false">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <form class="modal-body" @submit.prevent="submitAddEmployee">
            <div class="form-field">
              <label>Employee</label>
              <input v-model="empSearch" type="text" class="field-input" placeholder="Search name or designation…" />
              <div class="dropdown-list">
                <button
                  v-for="u in filteredUsersForAdd"
                  :key="u.id"
                  type="button"
                  class="dd-item"
                  :class="{ picked: addForm.user_id === u.id }"
                  @click="addForm.user_id = u.id"
                >
                  <span class="strong">{{ u.name }}</span>
                  <span class="sub">{{ u.designation || '—' }}</span>
                </button>
                <div v-if="filteredUsersForAdd.length === 0" class="dd-empty">No employees available</div>
              </div>
            </div>
            <div class="form-field">
              <label>Base Pay (₹/mo)</label>
              <input v-model.number="addForm.base_pay" type="number" min="0" step="100" class="field-input" required />
              <p v-if="addPreviewHourly != null" class="preview">Hourly Rate: {{ formatInrPerHour(addPreviewHourly) }}</p>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn-ghost" @click="addModalOpen = false">Cancel</button>
              <button type="submit" class="btn-primary" :disabled="addSubmitting || !addForm.user_id">
                {{ addSubmitting ? 'Saving…' : 'Assign' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <ToastNotification
      v-if="toastMsg"
      :message="toastMsg"
      :type="toastType"
      @done="toastMsg = ''"
    />
  </AppLayout>
</template>

<script setup>
import { ref, computed, watch, reactive } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import ProjectSelector from '../components/projects/ProjectSelector.vue'
import ToastNotification from '../components/ToastNotification.vue'
import { projectsAPI } from '../api/projects'
import { usersAPI } from '../api/users'
import { weeklyTimesheetsAPI } from '../api/weekly_timesheets'
import { formatInr, formatInrPerHour, previewHourlyFromBasePay } from '../utils/currency'

const selectedProjectId = ref(null)

const apiSummary = ref({
  project_id: null,
  project_name: '',
  employee_rows: [],
  totals: { total_hours: 0, total_spent: 0, type: 'expense' },
  partner: { hourly_rate: 0, total_hours: 0, partner_cost: 0, type: 'profit' },
  grand_total: 0,
})
const summaryProjectMeta = ref(null)
const projectDetail = ref(null)
const approvedTimesheets = ref([])
const summaryLoading = ref(false)
const summaryError = ref('')

const allUsers = ref([])
const addModalOpen = ref(false)
const empSearch = ref('')
const addForm = reactive({ user_id: null, base_pay: null })
const addSubmitting = ref(false)

const editingPartnerRate = ref(false)
const partnerRateInput = ref(0)
const savingPartnerRate = ref(false)

const drafts = reactive({})
const savingAssignmentId = ref(null)

const toastMsg = ref('')
const toastType = ref('success')

function toast(msg, type = 'success') {
  toastType.value = type
  toastMsg.value = msg
}

function apiErr(e) {
  const d = e.response?.data?.detail
  if (Array.isArray(d)) return d.map((x) => x.msg || JSON.stringify(x)).join(' ')
  if (typeof d === 'object' && d !== null) return JSON.stringify(d)
  return d || e.message || 'Request failed'
}

const partner = computed(() => apiSummary.value.partner || { hourly_rate: 0, partner_cost: 0 })

const displayPartnerHourly = computed(() => {
  const fromProject = Number(summaryProjectMeta.value?.partner_hourly_rate)
  if (!Number.isNaN(fromProject) && fromProject > 0) return fromProject
  const fromPartner = Number(partner.value.hourly_rate)
  if (!Number.isNaN(fromPartner) && fromPartner > 0) return fromPartner
  return 0
})

const partnerRateSet = computed(() => displayPartnerHourly.value > 0)

/** Approved weekly timesheets → hours per employee for selected project */
const hoursFromTimesheets = computed(() => {
  const pid = selectedProjectId.value
  const map = new Map()
  if (!pid) return map
  for (const ts of approvedTimesheets.value || []) {
    if (ts.status !== 'approved') continue
    const uid = ts.employee_id ?? ts.user_id
    if (!uid) continue
    const entries = ts.entries || []
    for (const e of entries) {
      if (Number(e.project_id) !== Number(pid)) continue
      const h = Number(e.hours) || 0
      if (h <= 0) continue
      map.set(uid, (map.get(uid) || 0) + h)
    }
  }
  return map
})

/**
 * Table rows: only employees with approved timesheet hours on this project.
 * Pay fields come from project assignments / summary when available.
 */
const employeeBaseRows = computed(() => {
  const pid = selectedProjectId.value
  const H = hoursFromTimesheets.value
  const apiRows = apiSummary.value.employee_rows || []
  const assignments = projectDetail.value?.assignments || []
  const users = allUsers.value || []

  const uids = [...H.keys()].filter((uid) => (H.get(uid) || 0) > 0)
  uids.sort((a, b) => {
    const na = users.find((u) => u.id === a)?.name || ''
    const nb = users.find((u) => u.id === b)?.name || ''
    return na.localeCompare(nb)
  })

  return uids.map((uid) => {
    const apiRow = apiRows.find((r) => r.employee_id === uid)
    const assign = assignments.find((a) => (a.user_id ?? a.user?.id) === uid)
    const u = users.find((x) => x.id === uid)
    const hours = H.get(uid) || 0
    const basePay = Number(apiRow?.base_pay ?? assign?.base_pay ?? 0) || 0
    let hourly = Number(apiRow?.hourly_rate ?? assign?.hourly_rate)
    if (Number.isNaN(hourly) || hourly <= 0) {
      hourly = previewHourlyFromBasePay(basePay) || 0
    }
    const totalSpent = hourly * hours
    return {
      employee_id: uid,
      assignment_id: assign?.id ?? apiRow?.assignment_id ?? null,
      name: apiRow?.name ?? u?.name ?? `Employee #${uid}`,
      designation: apiRow?.designation ?? u?.designation ?? assign?.user?.designation ?? '—',
      base_pay: basePay,
      hourly_rate: hourly,
      hours_worked: hours,
      total_spent: totalSpent,
    }
  })
})

watch(
  () => [selectedProjectId.value, employeeBaseRows.value.map((r) => r.employee_id).join(',')],
  () => {
    for (const k of Object.keys(drafts)) delete drafts[k]
    for (const r of employeeBaseRows.value) {
      if (r.assignment_id) {
        drafts[r.assignment_id] = {
          base_pay: r.base_pay,
          hourly_rate: r.hourly_rate,
        }
      }
    }
  },
  { flush: 'post' }
)

const shownRows = computed(() =>
  employeeBaseRows.value.map((r) => {
    const d = r.assignment_id ? drafts[r.assignment_id] : null
    const bp = Number(d?.base_pay ?? r.base_pay) || 0
    let hr = Number(d?.hourly_rate ?? r.hourly_rate)
    if (Number.isNaN(hr) || hr < 0) hr = 0
    if (hr === 0 && bp > 0) hr = previewHourlyFromBasePay(bp) || 0
    const hw = Number(r.hours_worked) || 0
    const display_spent = hr * hw
    return { ...r, display_spent }
  })
)

const displayTotals = computed(() => {
  const total_hours = shownRows.value.reduce((s, r) => s + (Number(r.hours_worked) || 0), 0)
  const total_spent = shownRows.value.reduce((s, r) => s + (Number(r.display_spent) || 0), 0)
  return { total_hours, total_spent, type: 'expense' }
})

const displayPartnerCost = computed(() => {
  const ph = displayPartnerHourly.value
  const th = displayTotals.value.total_hours
  return ph * th
})

const displayGrandTotal = computed(() => displayTotals.value.total_spent + displayPartnerCost.value)

const showTimesheetHint = computed(() => {
  if (!selectedProjectId.value) return false
  return shownRows.value.length === 0
})

const timesheetHoursNote = computed(() => {
  if (!selectedProjectId.value || !approvedTimesheets.value.length) return ''
  const H = hoursFromTimesheets.value
  if (H.size === 0 && approvedTimesheets.value.some((t) => t.status === 'approved')) {
    return 'Approved timesheets loaded; no hours logged against this project yet.'
  }
  return ''
})

const assignedUserIds = computed(() => {
  const ids = new Set()
  for (const a of projectDetail.value?.assignments || []) {
    const id = a.user_id ?? a.user?.id
    if (id != null) ids.add(id)
  }
  return ids
})

const filteredUsersForAdd = computed(() => {
  const q = empSearch.value.trim().toLowerCase()
  return allUsers.value.filter((u) => {
    if (assignedUserIds.value.has(u.id)) return false
    if (!q) return true
    return (
      (u.name || '').toLowerCase().includes(q) ||
      (u.designation || '').toLowerCase().includes(q)
    )
  })
})

const addPreviewHourly = computed(() => previewHourlyFromBasePay(addForm.base_pay))

async function ensureTimesheetEntries(timesheets) {
  const list = [...(timesheets || [])]
  const missing = list.filter((t) => !t.entries || t.entries.length === 0)
  const cap = 80
  const slice = missing.slice(0, cap)
  if (!slice.length) return list
  const detailed = await Promise.all(
    slice.map((t) =>
      weeklyTimesheetsAPI.getTimesheet(t.id).then((r) => r.data).catch(() => t)
    )
  )
  const byId = new Map(detailed.map((d) => [d.id, d]))
  return list.map((t) => byId.get(t.id) || t)
}

async function loadAllForProject(id) {
  summaryError.value = ''
  summaryProjectMeta.value = null
  projectDetail.value = null
  approvedTimesheets.value = []
  summaryLoading.value = true
  try {
    const [sumRes, projRes, tsRes, usersRes] = await Promise.all([
      projectsAPI.getProjectSummary(id),
      projectsAPI.getProject(id),
      weeklyTimesheetsAPI.getTimesheets({ status: 'approved' }).catch(() => ({ data: [] })),
      usersAPI.getUsers().catch(() => ({ data: [] })),
    ])
    apiSummary.value = sumRes.data
    summaryProjectMeta.value = projRes.data
    projectDetail.value = projRes.data
    allUsers.value = usersRes.data || []
    let tsList = tsRes.data || []
    tsList = await ensureTimesheetEntries(tsList)
    approvedTimesheets.value = tsList
  } catch (e) {
    summaryError.value = apiErr(e) || 'Could not load summary.'
    console.error(e)
  } finally {
    summaryLoading.value = false
  }
}

watch(selectedProjectId, (id) => {
  if (!id) {
    apiSummary.value = {
      project_id: null,
      project_name: '',
      employee_rows: [],
      totals: { total_hours: 0, total_spent: 0, type: 'expense' },
      partner: { hourly_rate: 0, total_hours: 0, partner_cost: 0, type: 'profit' },
      grand_total: 0,
    }
    summaryProjectMeta.value = null
    projectDetail.value = null
    approvedTimesheets.value = []
    return
  }
  loadAllForProject(id)
})

watch(addModalOpen, async (open) => {
  if (!open) return
  empSearch.value = ''
  addForm.user_id = null
  addForm.base_pay = null
  try {
    const res = await usersAPI.getUsers()
    allUsers.value = res.data || []
  } catch (e) {
    console.error(e)
  }
})

function formatHours(h) {
  const n = Number(h) || 0
  return `${n} hrs`
}

function stageClass(stage) {
  if (!stage) return 'stage-na'
  if (stage === 'Completed') return 'stage-done'
  if (stage === 'Incomplete Beyond Deadline' || stage === 'Halted') return 'stage-warn'
  return 'stage-active'
}

function openAddModal() {
  if (!selectedProjectId.value) return
  addModalOpen.value = true
}

async function submitAddEmployee() {
  if (!selectedProjectId.value || !addForm.user_id) return
  addSubmitting.value = true
  try {
    await projectsAPI.assignEmployee(selectedProjectId.value, {
      user_id: addForm.user_id,
      base_pay: Number(addForm.base_pay) || 0,
    })
    addModalOpen.value = false
    toast('Employee assigned.')
    await loadAllForProject(selectedProjectId.value)
  } catch (e) {
    toast(apiErr(e), 'error')
  } finally {
    addSubmitting.value = false
  }
}

async function saveAssignmentRow(row) {
  if (!selectedProjectId.value || !row.assignment_id) return
  const d = drafts[row.assignment_id]
  if (!d) return
  savingAssignmentId.value = row.assignment_id
  try {
    await projectsAPI.updateAssignment(selectedProjectId.value, row.assignment_id, {
      base_pay: Number(d.base_pay) || 0,
      hourly_rate: Number(d.hourly_rate) || 0,
    })
    toast('Assignment pay updated.')
    await loadAllForProject(selectedProjectId.value)
  } catch (e) {
    toast(apiErr(e), 'error')
  } finally {
    savingAssignmentId.value = null
  }
}

function onBasePayInput(aid) {
  const d = drafts[aid]
  if (d && d.base_pay) {
    const hr = previewHourlyFromBasePay(d.base_pay)
    if (hr != null) {
      d.hourly_rate = hr
    }
  }
}

function startEditPartnerRate() {
  partnerRateInput.value = displayPartnerHourly.value || 0
  editingPartnerRate.value = true
}

async function savePartnerRate() {
  if (!selectedProjectId.value) return
  savingPartnerRate.value = true
  try {
    const billRes = await projectsAPI.getProjectBilling(selectedProjectId.value)
    const billed = Number(billRes.data?.billed_amount) || 0
    await projectsAPI.patchProjectBilling(selectedProjectId.value, {
      billed_amount: billed,
      partner_hourly_rate: Number(partnerRateInput.value) || 0,
    })
    editingPartnerRate.value = false
    toast('Partner rate updated.')
    await loadAllForProject(selectedProjectId.value)
  } catch (e) {
    toast(apiErr(e), 'error')
  } finally {
    savingPartnerRate.value = false
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 24px;
}
.page-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--color-on-surface);
  margin: 0 0 4px;
  letter-spacing: -0.02em;
}
.page-sub {
  margin: 0;
  font-size: 14px;
  color: var(--color-on-surface-variant);
}

.split-layout {
  display: flex;
  gap: 24px;
  align-items: stretch;
  min-height: calc(100vh - 220px);
}

.col-left {
  flex: 0 0 30%;
  max-width: 360px;
  min-width: 240px;
}

.col-right {
  flex: 1;
  min-width: 0;
}

.empty-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  background: #fff;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  color: var(--color-on-surface-variant);
  font-size: 14px;
}
.empty-ic {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.35;
}

.detail-skeleton {
  background: #fff;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 24px;
}
.sk-h1 {
  height: 28px;
  width: 55%;
  background: #e2e8f0;
  border-radius: 4px;
  margin-bottom: 12px;
  animation: pulse 1.2s ease-in-out infinite;
}
.sk-sub {
  height: 16px;
  width: 30%;
  background: #f1f5f9;
  border-radius: 4px;
  margin-bottom: 24px;
  animation: pulse 1.2s ease-in-out infinite;
}
.sk-table {
  height: 200px;
  background: #f8fafc;
  border-radius: 8px;
  animation: pulse 1.2s ease-in-out infinite;
}
@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.55;
  }
}

.detail-content {
  background: #fff;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 24px;
}

.detail-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.detail-title {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 4px;
  color: var(--color-on-surface);
}
.detail-sub {
  margin: 0 0 8px;
  font-size: 13px;
  color: var(--color-on-surface-variant);
}
.header-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}
.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.stage-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 2px;
  font-size: 11px;
  font-weight: 600;
}
.stage-active {
  background: #d4edee;
  color: #113b3c;
}
.stage-done {
  background: #dcfce7;
  color: #166534;
}
.stage-warn {
  background: #fef3c7;
  color: #92400e;
}
.stage-na {
  background: #f1f5f9;
  color: #64748b;
}

.btn-primary {
  padding: 10px 18px;
  border: none;
  border-radius: var(--radius-lg);
  background: var(--color-primary);
  color: #fff;
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}
.btn-primary:hover {
  opacity: 0.92;
}
.btn-primary.sm {
  padding: 6px 12px;
  font-size: 13px;
}
.btn-ghost {
  padding: 8px 14px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  background: #fff;
  font-size: 14px;
  cursor: pointer;
}
.btn-ghost.sm {
  padding: 6px 10px;
  font-size: 13px;
}

.info-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  margin-bottom: 16px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: var(--radius-lg);
  font-size: 13px;
  color: #1e40af;
}

.info-banner.subtle {
  background: #f8fafc;
  border-color: #e2e8f0;
  color: var(--color-on-surface-variant);
}

.cell-input {
  width: 100%;
  max-width: 140px;
  height: 36px;
  padding: 0 8px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.cell-input.narrow {
  max-width: 100px;
}

.cell-input:focus {
  border-color: var(--color-primary);
  outline: none;
  box-shadow: 0 0 0 1px var(--color-primary);
}

.actions-col {
  width: 140px;
  text-align: right;
  vertical-align: middle;
}

.btn-row-save {
  padding: 6px 12px;
  border: none;
  border-radius: var(--radius-lg);
  background: var(--color-primary);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.btn-row-save:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.empty-row {
  text-align: center;
  color: var(--color-on-surface-variant);
  padding: 24px !important;
}

.muted-xs {
  font-size: 11px;
  color: var(--color-on-surface-variant);
}

.table-card {
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  overflow: auto;
  margin-bottom: 12px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.data-table th {
  text-align: left;
  padding: 10px 12px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
  background: #f8fafc;
  border-bottom: 1px solid var(--color-outline-variant);
}
.data-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #e2e8f0;
}
.data-table tbody tr:nth-child(even) {
  background: #fafafa;
}
.data-table .num {
  text-align: right;
}
.tab {
  font-variant-numeric: tabular-nums;
}
.total-row td {
  background: #f1f5f9;
  font-size: 14px;
}

.tag-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}
.tag-label {
  font-size: 13px;
  font-weight: 600;
}
.tag-label.expense {
  color: #b91c1c;
}
.type-tag {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 2px 8px;
  border-radius: 2px;
}
.type-tag.expense {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}
.type-tag.profit {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}
.tag-label.profit {
  color: #15803d;
}

.partner-card {
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 20px;
  margin-bottom: 24px;
  background: #fafafa;
}
.partner-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.partner-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.muted {
  display: block;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-on-surface-variant);
  margin-bottom: 4px;
}
.val {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: var(--color-on-surface);
}

.partner-warn {
  margin-top: 16px;
  padding: 12px;
  background: #fefce8;
  border: 1px solid #fde047;
  border-radius: var(--radius-lg);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #854d0e;
}
.btn-inline {
  margin-left: auto;
  padding: 6px 12px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-lg);
  font-weight: 600;
  cursor: pointer;
}
.inline-rate {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  width: 100%;
  margin-top: 8px;
}
.rate-inp {
  width: 120px;
  height: 36px;
  padding: 0 8px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
}
.rupee,
.per {
  font-size: 13px;
  font-weight: 600;
}

.grand-total {
  max-width: 480px;
}
.grand-line {
  height: 1px;
  background: var(--color-outline-variant);
  margin: 8px 0;
}
.grand-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  padding: 4px 0;
}
.grand-note {
  margin: 4px 0 8px;
  font-size: 12px;
  color: var(--color-on-surface-variant);
}

.fade-panel-enter-active,
.fade-panel-leave-active {
  transition: opacity 0.2s ease;
}
.fade-panel-enter-from,
.fade-panel-leave-to {
  opacity: 0;
}

.text-error {
  color: var(--color-error);
}

/* Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.modal {
  width: 440px;
  max-width: 94vw;
  background: #fff;
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--color-outline-variant);
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-outline-variant);
}
.modal-title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 18px;
}
.modal-close {
  border: none;
  background: none;
  cursor: pointer;
  color: var(--color-on-surface-variant);
}
.modal-body {
  padding: 20px;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 20px;
}
.form-field {
  margin-bottom: 16px;
}
.form-field label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--color-on-surface-variant);
}
.field-input {
  width: 100%;
  height: 40px;
  padding: 0 12px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  font-size: 14px;
}
.dropdown-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  margin-top: 8px;
}
.dd-item {
  width: 100%;
  text-align: left;
  padding: 10px 12px;
  border: none;
  background: #fff;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 2px;
  border-bottom: 1px solid #f1f5f9;
}
.dd-item:hover {
  background: #f8fafc;
}
.dd-item.picked {
  background: rgba(40, 116, 117, 0.12);
}
.strong {
  font-weight: 600;
  font-size: 14px;
}
.sub {
  font-size: 12px;
  color: var(--color-on-surface-variant);
}
.dd-empty {
  padding: 16px;
  text-align: center;
  font-size: 13px;
  color: var(--color-on-surface-variant);
}
.preview {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--color-on-surface-variant);
}

.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

@media (max-width: 960px) {
  .split-layout {
    flex-direction: column;
  }
  .col-left {
    flex: none;
    max-width: none;
    width: 100%;
  }
  .partner-grid {
    grid-template-columns: 1fr;
  }
}
</style>
