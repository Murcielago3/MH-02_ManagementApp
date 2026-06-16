<template>
  <AppLayout>
    <!-- Page Header -->
    <div class="page-header">
      <div class="page-header__left">
        <button class="back-btn" @click="goBack">
          <span class="material-symbols-outlined">arrow_back</span>
        </button>
        <div>
          <h1 class="page-title">Project Summary</h1>
          <p class="page-sub">Employee spend and partner remuneration</p>
        </div>
      </div>
      <div class="page-header__actions" v-if="summaryProjectMeta">
        <button class="btn-outline" @click="editProject">
          <span class="material-symbols-outlined">edit</span>
          Edit Project
        </button>
      </div>
    </div>

    <!-- Loading skeleton -->
    <div v-if="summaryLoading" class="detail-skeleton">
      <div class="sk-h1" />
      <div class="sk-sub" />
      <div class="sk-table" />
    </div>

    <!-- Error -->
    <div v-else-if="summaryError" class="empty-center text-error">
      <span class="material-symbols-outlined" style="font-size:36px;margin-bottom:8px;opacity:0.5;">error_outline</span>
      {{ summaryError }}
    </div>

    <!-- Main content -->
    <div v-else-if="selectedProjectId" class="detail-content">

      <!-- Project identity header -->
      <div class="project-header">
        <div class="project-header__left">
          <div class="project-color-dot" :style="{ background: summaryProjectMeta?.color || 'var(--color-primary)' }" />
          <div>
            <h2 class="detail-title">{{ apiSummary.project_name }}</h2>
            <p class="detail-sub">
              {{ summaryProjectMeta?.project_number }}
              <template v-if="summaryProjectMeta?.year"> · {{ summaryProjectMeta.year }}</template>
            </p>
          </div>
        </div>
        <span class="stage-badge" :class="stageClass(summaryProjectMeta?.current_stage)">
          {{ summaryProjectMeta?.current_stage || 'N/A' }}
        </span>
      </div>

            <!-- Section: Project Financials -->
            <div class="section-block">
              <div class="section-header">
                <span class="material-symbols-outlined section-icon">payments</span>
                <span class="section-title">Project Financials</span>
                <span class="type-tag neutral">BUDGET</span>
              </div>

              <div class="partner-card">
                <div class="partner-grid">
                  <div class="partner-metric">
                    <span class="metric-label">Total Project Cost</span>
                    <div class="metric-value">{{ summaryProjectMeta?.project_remuneration ? formatInr(summaryProjectMeta.project_remuneration, 0) : '—' }}</div>
                  </div>
                  <div class="partner-metric">
                    <span class="metric-label">Employee Remuneration</span>
                    <div class="metric-value">{{ summaryProjectMeta?.employee_remuneration ? formatInr(summaryProjectMeta.employee_remuneration, 0) : '—' }}</div>
                  </div>
                  <div class="partner-metric">
                    <span class="metric-label">Partner Remuneration</span>
                    <div class="metric-value">{{ summaryProjectMeta?.partner_remuneration ? formatInr(summaryProjectMeta.partner_remuneration, 0) : '—' }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Section: Employee Spend -->
            <div class="section-block">
              <div class="section-header">
                <span class="material-symbols-outlined section-icon">people</span>
                <span class="section-title">Employee Spend</span>
                <span class="type-tag expense">EXPENSE</span>
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
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-if="!shownRows.length">
                      <td colspan="6" class="empty-row">
                        <span class="material-symbols-outlined" style="font-size:20px;opacity:0.3;vertical-align:middle;margin-right:6px;">schedule</span>
                        No approved timesheet hours on this project yet.
                      </td>
                    </tr>
                    <tr v-for="row in shownRows" :key="row.employee_id">
                      <td class="cell-name">{{ row.name }}</td>
                      <td class="cell-muted">{{ row.designation || '—' }}</td>
                      <td class="num tab">{{ formatInr(row.base_pay, 0) }}</td>
                      <td class="num tab">{{ formatInrPerHour(row.hourly_rate) }}</td>
                      <td class="num tab">{{ formatHours(row.hours_worked) }}</td>
                      <td class="num tab cell-amount">{{ formatInr(row.display_spent, 0) }}</td>
                    </tr>
                  </tbody>
                  <tfoot>
                    <tr class="total-row">
                      <td colspan="2"><strong>TOTAL</strong></td>
                      <td class="num">—</td>
                      <td class="num">—</td>
                      <td class="num tab"><strong>{{ formatHours(displayTotals.total_hours) }}</strong></td>
                      <td class="num tab cell-amount"><strong>{{ formatInr(displayTotals.total_spent, 0) }}</strong></td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>

            <!-- Section: Partner Remuneration -->
            <div class="section-block">
              <div class="section-header">
                <span class="material-symbols-outlined section-icon section-icon--profit">handshake</span>
                <span class="section-title">Partner Remuneration</span>
                <span class="type-tag profit">PROFIT</span>
              </div>

              <div class="partner-card">
                <div class="partner-grid">
                  <div class="partner-metric">
                    <span class="metric-label">Partner Rate</span>
                    <div v-if="!editingPartnerRate" class="metric-value rate-cell">
                      {{ partnerRateSet ? formatInrPerHour(displayPartnerHourly) : '—' }}
                      <button type="button" class="btn-edit-rate" @click="startEditPartnerRate" title="Edit partner rate">
                        <span class="material-symbols-outlined">edit</span>
                      </button>
                    </div>
                    <div v-else class="inline-rate compact">
                      <span class="rupee">₹</span>
                      <input v-model.number="partnerRateInput" type="number" min="0" step="1" class="rate-inp" />
                      <span class="per">/hr</span>
                      <button type="button" class="btn-primary sm" :disabled="savingPartnerRate" @click="savePartnerRate">
                        {{ savingPartnerRate ? '…' : 'Save' }}
                      </button>
                      <button type="button" class="btn-ghost sm" @click="editingPartnerRate = false">Cancel</button>
                    </div>
                  </div>
                  <div class="partner-metric">
                    <span class="metric-label">Total Hours</span>
                    <div class="metric-value">{{ formatHours(displayTotals.total_hours) }}</div>
                  </div>
                  <div class="partner-metric partner-metric--highlight">
                    <span class="metric-label">Partner Cost</span>
                    <div class="metric-value metric-value--large">{{ formatInr(displayPartnerCost, 0) }}</div>
                  </div>
                </div>

                <div v-if="!partnerRateSet && !editingPartnerRate" class="partner-warn">
                  <span class="material-symbols-outlined">warning</span>
                  Partner rate not set — click the edit icon above to configure it.
                </div>
              </div>
            </div>

            <!-- Grand Total -->
            <div class="grand-total-block">
              <div class="grand-total-inner">
                <div class="grand-total-label">
                  <span class="material-symbols-outlined" style="font-size:18px;">calculate</span>
                  Grand Total
                </div>
                <div class="grand-total-value">{{ formatInr(displayGrandTotal, 0) }}</div>
              </div>
              <p class="grand-note">Employee Spend + Partner Remuneration</p>
            </div>

            <!-- Section: Project Reserves -->
            <div v-if="showReserveSection" class="section-block">
              <div class="section-header">
                <span class="material-symbols-outlined section-icon" :class="reserveDepleted ? 'section-icon--error' : ''">account_balance_wallet</span>
                <span class="section-title">Project Reserves</span>
                <span v-if="reserveDepleted" class="reserve-badge-warn">
                  <span class="material-symbols-outlined">warning</span>
                  Reserve Depleted
                </span>
              </div>

              <div class="reserve-card" :class="{ 'reserve-card--depleted': reserveDepleted }">
                <div class="summary-rows">
                  <div class="summary-row">
                    <span class="summary-row__label">Total Invoiced</span>
                    <span class="summary-row__value">{{ formatInr(apiSummary.total_invoiced, 0) }}</span>
                  </div>
                  <div class="summary-row">
                    <span class="summary-row__label">
                      <span class="op-badge op-badge--minus">−</span>
                      Total Spend
                    </span>
                    <span class="summary-row__value">{{ formatInr(displayGrandTotal, 0) }}</span>
                  </div>
                  <div class="summary-divider" />
                  <div class="summary-row summary-row--total" :class="{ 'summary-row--negative': reserveDepleted }">
                    <span class="summary-row__label summary-row__label--bold">Reserve Balance</span>
                    <strong class="summary-row__value summary-row__value--xl">
                      {{ reserveDepleted ? '−' : '' }}{{ formatInr(Math.abs(reserveBalance), 0) }}
                    </strong>
                  </div>
                </div>
              </div>
            </div>

            <!-- Section: Projected Cost -->
            <div class="section-block">
              <div class="section-header">
                <span class="material-symbols-outlined section-icon">trending_up</span>
                <span class="section-title">Projected Cost</span>
                <span class="section-subtitle">Based on tasks scheduled in calendar</span>
              </div>

              <div v-if="projectedLoading" class="projected-loading">
                <span class="material-symbols-outlined spin">refresh</span>
                Loading projected data…
              </div>

              <div v-else-if="projectedData && projectedData.rows && projectedData.rows.length">
                <div class="table-card">
                  <table class="data-table">
                    <thead>
                      <tr>
                        <th>Employee</th>
                        <th>Designation</th>
                        <th class="num">Proj. Hours</th>
                        <th class="num">Rate/hr</th>
                        <th class="num">Projected Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="row in projectedData.rows" :key="row.employee_id">
                        <td class="cell-name">{{ row.name }}</td>
                        <td class="cell-muted">{{ row.designation }}</td>
                        <td class="num tab">{{ row.projected_hours }} hrs</td>
                        <td class="num tab">{{ formatInrPerHour(row.hourly_rate) }}</td>
                        <td class="num tab cell-amount">{{ formatInr(row.projected_cost, 0) }}</td>
                      </tr>
                    </tbody>
                    <tfoot>
                      <tr class="total-row">
                        <td colspan="2"><strong>Employee Total</strong></td>
                        <td class="num tab"><strong>{{ projectedData.total_projected_hours }} hrs</strong></td>
                        <td></td>
                        <td class="num tab cell-amount"><strong>{{ formatInr(projectedData.total_employee_projected, 0) }}</strong></td>
                      </tr>
                    </tfoot>
                  </table>
                </div>

                <div class="projected-summary-block">
                  <div class="summary-rows">
                    <div class="summary-row">
                      <span class="summary-row__label">Total Employee Projected</span>
                      <span class="summary-row__value">{{ formatInr(projectedData.total_employee_projected, 0) }}</span>
                    </div>
                    <div class="summary-row">
                      <span class="summary-row__label">Partner Projected</span>
                      <span class="summary-row__value">{{ formatInr(projectedData.partner_projected_cost, 0) }}</span>
                    </div>
                    <div class="summary-divider" />
                    <div class="summary-row summary-row--total">
                      <span class="summary-row__label summary-row__label--bold">Total Projected Cost</span>
                      <strong class="summary-row__value summary-row__value--xl">{{ formatInr(projectedData.grand_projected, 0) }}</strong>
                    </div>
                  </div>
                </div>
              </div>

              <div v-else class="projected-empty">
                <span class="material-symbols-outlined">calendar_today</span>
                <p>No tasks scheduled for this project yet.</p>
              </div>
            </div>

    </div>

    <ToastNotification
      v-if="toastMsg"
      :message="toastMsg"
      :type="toastType"
      @done="toastMsg = ''"
    />
  </AppLayout>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import ToastNotification from '../components/ToastNotification.vue'
import { projectsAPI } from '../api/projects'
import { usersAPI } from '../api/users'
import { weeklyTimesheetsAPI } from '../api/weekly_timesheets'
import { formatInr, formatInrPerHour, previewHourlyFromBasePay } from '../utils/currency'

const route = useRoute()
const router = useRouter()

function goBack() {
  router.push('/admin/projects')
}

function editProject() {
  if (!selectedProjectId.value) return
  router.push({ path: '/admin/projects', query: { edit: selectedProjectId.value } })
}

// ── Projected cost ───────────────────────────────────────────────────────────
const projectedData = ref(null)
const projectedLoading = ref(false)

async function loadProjectedCost(id) {
  projectedLoading.value = true
  projectedData.value = null
  try {
    const res = await projectsAPI.getProjectedCost(id)
    projectedData.value = res.data
  } catch (e) {
    console.error('Projected cost load failed', e)
  } finally {
    projectedLoading.value = false
  }
}

const selectedProjectId = ref(null)

const apiSummary = ref({
  project_id: null,
  project_name: '',
  employee_rows: [],
  totals: { total_hours: 0, total_spent: 0, type: 'expense' },
  partner: { hourly_rate: 0, total_hours: 0, partner_cost: 0, type: 'profit' },
  grand_total: 0,
  advance_amount: 0,
  total_invoiced: 0,
  reserve_balance: 0,
  reserve_depleted: false,
  has_reserve: false,
})
const summaryProjectMeta = ref(null)
const projectDetail = ref(null)
const approvedTimesheets = ref([])
const summaryLoading = ref(false)
const summaryError = ref('')

const allUsers = ref([])


const editingPartnerRate = ref(false)
const partnerRateInput = ref(0)
const savingPartnerRate = ref(false)

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
    const basePay = Number(apiRow?.base_pay ?? u?.salary_month ?? assign?.base_pay ?? 0) || 0
    const hourly = previewHourlyFromBasePay(basePay) || 0
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

const shownRows = computed(() =>
  employeeBaseRows.value.map((r) => {
    const hw = Number(r.hours_worked) || 0
    const hr = Number(r.hourly_rate) || 0
    return { ...r, display_spent: hr * hw }
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

// ── Reserve Balance computed ─────────────────────────────────────────────────
const reserveBalance = computed(() => {
  const inv = Number(apiSummary.value.total_invoiced) || 0
  return inv - displayGrandTotal.value
})
const reserveDepleted = computed(() => reserveBalance.value < 0)
const showReserveSection = computed(() => (Number(apiSummary.value.total_invoiced) || 0) > 0)



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
    // Load projected cost in parallel (non-blocking)
    loadProjectedCost(id)
  } catch (e) {
    summaryError.value = apiErr(e) || 'Could not load summary.'
    console.error(e)
  } finally {
    summaryLoading.value = false
  }
}

onMounted(() => {
  const id = route.params.id
  if (id) {
    selectedProjectId.value = Number(id)
  }
})

watch(selectedProjectId, (id) => {
  if (!id) {
    apiSummary.value = {
      project_id: null,
      project_name: '',
      employee_rows: [],
      totals: { total_hours: 0, total_spent: 0, type: 'expense' },
      partner: { hourly_rate: 0, total_hours: 0, partner_cost: 0, type: 'profit' },
      grand_total: 0,
      advance_amount: 0,
      total_invoiced: 0,
      reserve_balance: 0,
      reserve_depleted: false,
      has_reserve: false,
    }
    summaryProjectMeta.value = null
    projectDetail.value = null
    approvedTimesheets.value = []
    projectedData.value = null
    return
  }
  loadAllForProject(id)
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
/* ── Base ─────────────────────────────────────────────────────────────────── */
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

/* ── Back Button ─────────────────────────────────────────────────────────── */
.back-btn {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-outline);
  background: var(--color-surface);
  color: var(--color-on-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s, color 0.15s;
}
.back-btn:hover { background: var(--color-surface-dim); color: var(--color-on-surface); }
.back-btn .material-symbols-outlined { font-size: 20px; }

/* ── Page Header ──────────────────────────────────────────────────────────── */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}
.page-header__left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.page-header__actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.page-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 800;
  color: var(--color-on-surface);
  margin: 0 0 2px;
  letter-spacing: -0.01em;
}
.page-sub {
  margin: 0;
  font-size: 13px;
  color: var(--color-on-surface-variant);
}
.btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-surface);
  cursor: pointer;
  transition: background 0.15s;
}
.btn-outline:hover { background: var(--color-surface-dim); }
.btn-outline .material-symbols-outlined { font-size: 17px; }

/* ── State panels ─────────────────────────────────────────────────────────── */
.empty-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-xl);
  color: var(--color-on-surface-variant);
  font-size: 14px;
  box-shadow: var(--shadow-sm);
}
.text-error { color: var(--color-error); }

/* Skeleton */
.detail-skeleton {
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-xl);
  padding: 28px;
  box-shadow: var(--shadow-sm);
}
.sk-h1   { height: 28px; width: 55%; background: #e2e8f0; border-radius: 4px; margin-bottom: 12px; animation: pulse 1.2s ease-in-out infinite; }
.sk-sub  { height: 16px; width: 30%; background: #f1f5f9; border-radius: 4px; margin-bottom: 24px; animation: pulse 1.2s ease-in-out infinite; }
.sk-table{ height: 200px; background: var(--color-surface-dim); border-radius: var(--radius-md); animation: pulse 1.2s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

/* ── Detail content wrapper ───────────────────────────────────────────────── */
.detail-content {
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

/* ── Project header strip ─────────────────────────────────────────────────── */
.project-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-outline-variant);
  background: var(--color-surface-dim);
  flex-wrap: wrap;
}
.project-header__left {
  display: flex;
  align-items: center;
  gap: 14px;
}
.project-color-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
}
.detail-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 2px;
  color: var(--color-on-surface);
}
.detail-sub {
  margin: 0;
  font-size: 13px;
  color: var(--color-on-surface-variant);
}

/* Stage badge */
.stage-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  white-space: nowrap;
}
.stage-active { background: #d4edee; color: #113b3c; }
.stage-done   { background: #dcfce7; color: #166534; }
.stage-warn   { background: #fef3c7; color: #92400e; }
.stage-na     { background: #f1f5f9; color: #64748b; }

/* ── Section blocks ───────────────────────────────────────────────────────── */
.section-block {
  padding: 20px 24px 0;
}
.section-block + .section-block {
  margin-top: 8px;
}
.section-block:last-child {
  padding-bottom: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}
.section-icon {
  font-size: 18px;
  color: var(--color-primary);
}
.section-icon--profit { color: var(--color-success); }
.section-icon--error  { color: var(--color-error); }

.section-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-on-surface);
  letter-spacing: 0.03em;
  text-transform: uppercase;
}
.section-subtitle {
  font-size: 12px;
  color: var(--color-on-surface-variant);
  margin-left: 2px;
}

/* Type tags */
.type-tag {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.07em;
  padding: 2px 8px;
  border-radius: var(--radius-full);
}
.type-tag.expense { background: rgba(220, 38, 38, 0.1); color: var(--color-error); }
.type-tag.profit  { background: rgba(22, 163, 74, 0.12); color: var(--color-success); }
.type-tag.neutral { background: rgba(100, 116, 139, 0.1); color: #475569; }

/* ── Table ────────────────────────────────────────────────────────────────── */
.table-card {
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  overflow: auto;
  margin-bottom: 8px;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.data-table th {
  text-align: left;
  padding: 10px 14px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
  background: var(--color-surface-dim);
  border-bottom: 1px solid var(--color-outline-variant);
  white-space: nowrap;
}
.data-table td {
  padding: 10px 14px;
  border-bottom: 1px solid var(--color-outline-variant);
  color: var(--color-on-surface);
}
.data-table tbody tr:last-child td { border-bottom: none; }
.data-table tbody tr:hover { background: var(--color-surface-dim); }
.data-table .num { text-align: right; }
.tab  { font-variant-numeric: tabular-nums; }
.cell-name   { font-weight: 500; }
.cell-muted  { color: var(--color-on-surface-variant); }
.cell-amount { font-weight: 600; color: var(--color-on-surface); }
.total-row td {
  background: var(--color-outline-variant);
  font-size: 13px;
  font-weight: 600;
  border-bottom: none;
}
.empty-row {
  text-align: center;
  color: var(--color-on-surface-variant);
  padding: 28px 14px !important;
  font-size: 13px;
}

/* ── Partner card ─────────────────────────────────────────────────────────── */
.partner-card {
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 20px;
  background: var(--color-surface-dim);
}
.partner-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.partner-metric {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.partner-metric--highlight {
  background: var(--color-primary-light);
  border-radius: var(--radius-md);
  padding: 10px 14px;
  margin: -10px -14px -10px -14px;
}
.metric-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
}
.metric-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-on-surface);
  display: flex;
  align-items: center;
  gap: 8px;
  font-variant-numeric: tabular-nums;
}
.metric-value--large {
  font-family: var(--font-display);
  font-size: 20px;
  color: var(--color-primary);
}
.rate-cell { display: inline-flex; align-items: center; gap: 8px; }

.btn-edit-rate {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: 1px solid var(--color-outline-variant);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-on-surface-variant);
  transition: background 0.15s, color 0.15s;
}
.btn-edit-rate:hover { background: var(--color-primary-light); color: var(--color-primary); }
.btn-edit-rate .material-symbols-outlined { font-size: 15px; }

.inline-rate {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.inline-rate.compact { margin-top: 0; }
.rate-inp {
  width: 110px;
  height: 34px;
  padding: 0 8px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-size: 14px;
}
.rupee, .per { font-size: 13px; font-weight: 600; color: var(--color-on-surface-variant); }

.partner-warn {
  margin-top: 16px;
  padding: 12px 14px;
  background: #fefce8;
  border: 1px solid #fde047;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #854d0e;
}

/* ── Buttons ──────────────────────────────────────────────────────────────── */
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
.btn-primary:hover  { opacity: 0.9; }
.btn-primary.sm     { padding: 6px 12px; font-size: 13px; }
.btn-ghost {
  padding: 8px 14px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  font-size: 14px;
  cursor: pointer;
  color: var(--color-on-surface);
}
.btn-ghost.sm { padding: 6px 10px; font-size: 13px; }

/* ── Grand Total block ────────────────────────────────────────────────────── */
.grand-total-block {
  margin: 0 24px;
  padding: 16px 20px;
  background: linear-gradient(135deg, var(--color-primary-light) 0%, #f0fafa 100%);
  border: 1px solid rgba(40,116,117,0.2);
  border-radius: var(--radius-lg);
  margin-bottom: 4px;
}
.grand-total-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.grand-total-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 700;
  color: var(--color-primary);
}
.grand-total-value {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--color-primary);
  font-variant-numeric: tabular-nums;
}
.grand-note {
  margin: 4px 0 0;
  font-size: 11px;
  color: var(--color-on-surface-variant);
}

/* ── Summary rows (reserves / projected) ─────────────────────────────────── */
.reserve-card {
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: border-color 0.2s;
}
.reserve-card--depleted { border-color: #fca5a5; }

.reserve-badge-warn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  background: #fee2e2;
  border: 1px solid #fca5a5;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 700;
  color: #b91c1c;
  letter-spacing: 0.04em;
  margin-left: auto;
}
.reserve-badge-warn .material-symbols-outlined { font-size: 13px; }

.summary-rows { padding: 4px 0; }
.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  font-size: 13px;
  color: var(--color-on-surface-variant);
  transition: background 0.1s;
}
.summary-row:nth-child(even) { background: var(--color-surface-dim); }
.summary-row__label {
  display: flex;
  align-items: center;
  gap: 6px;
}
.summary-row__value {
  font-variant-numeric: tabular-nums;
  font-weight: 500;
  color: var(--color-on-surface);
}
.summary-divider {
  height: 1px;
  background: var(--color-outline-variant);
  margin: 4px 16px;
}
.summary-row--total {
  padding: 12px 16px;
  background: var(--color-surface-dim) !important;
  font-weight: 600;
  font-size: 14px;
  color: var(--color-on-surface);
}
.summary-row--negative .summary-row__label--bold,
.summary-row--negative .summary-row__value--xl { color: var(--color-error); }
.summary-row__label--bold { font-weight: 700; font-size: 13px; }
.summary-row__value--xl {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.op-badge--minus {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(220,38,38,0.1);
  color: var(--color-error);
  font-size: 14px;
  font-weight: 700;
  line-height: 1;
}

/* ── Projected summary ────────────────────────────────────────────────────── */
.projected-summary-block {
  margin-top: 12px;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  overflow: hidden;
  max-width: 480px;
}
.projected-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-on-surface-variant);
  padding: 16px 0;
}
.projected-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 36px;
  color: var(--color-on-surface-variant);
  font-size: 13px;
  gap: 8px;
  background: var(--color-surface-dim);
  border-radius: var(--radius-lg);
}
.projected-empty .material-symbols-outlined { font-size: 32px; opacity: 0.3; }

@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 1s linear infinite; }

/* ── Transitions ──────────────────────────────────────────────────────────── */
.fade-panel-enter-active,
.fade-panel-leave-active { transition: opacity 0.2s ease; }
.fade-panel-enter-from,
.fade-panel-leave-to     { opacity: 0; }

/* ── Responsive ───────────────────────────────────────────────────────────── */
@media (max-width: 960px) {
  .partner-grid  { grid-template-columns: 1fr; }
}
</style>
