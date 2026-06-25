<template>
  <AppLayout>
    <!-- Page Header -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">Timesheets</h1>
        <p class="page-subtitle">Review and approve weekly employee timesheets</p>
      </div>
      <button class="btn-primary" @click="fetchTimesheets">
        <span class="material-symbols-outlined">refresh</span>
        Refresh
      </button>
    </div>

    <!-- Filter Bar -->
    <div class="filter-bar">
      <div class="filter-bar-left">
        <select v-model="filterEmployee" class="filter-select">
          <option value="">All Employees</option>
          <option v-for="emp in employees" :key="emp.id" :value="emp.id">{{ emp.name }}</option>
        </select>
        <select v-model="filterStatus" class="filter-select">
          <option value="">All Statuses</option>
          <option value="submitted">Pending Review</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
        <input
          v-model="filterMonth"
          type="month"
          class="filter-select filter-month"
          title="Filter by month"
        />
        <select v-model="filterWeek" class="filter-select">
          <option value="">All Weeks</option>
          <option v-for="w in availableWeeks" :key="w.value" :value="w.value">{{ w.label }}</option>
        </select>
      </div>
      <button v-if="hasActiveFilters" class="btn-clear-filters" @click="clearFilters" title="Clear all filters">
        <span class="material-symbols-outlined">filter_alt_off</span>
        Clear
      </button>
    </div>

    <!-- Table Card -->
    <div class="table-card">
      <table class="data-table">
        <thead>
          <tr>
            <th>Employee</th>
            <th>Week</th>
            <th class="col-center">Hours</th>
            <th>Status</th>
            <th class="col-actions">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="5" class="empty-cell">
              <div class="empty-state">
                <span class="material-symbols-outlined empty-icon">hourglass_empty</span>
                <p>Loading timesheets…</p>
              </div>
            </td>
          </tr>
          <tr v-else-if="filtered.length === 0">
            <td colspan="5" class="empty-cell">
              <div class="empty-state">
                <span class="material-symbols-outlined empty-icon">schedule</span>
                <p>No timesheet records found.</p>
              </div>
            </td>
          </tr>
          <tr v-for="ts in filtered" :key="ts.id" class="data-row">
            <td>
              <span class="row-name row-link" @click="goToEmployeeProfile(ts.employee_id)">
                {{ getUserName(ts.employee_id) }}
              </span>
            </td>
            <td class="cell-mono cell-week">
              <span class="material-symbols-outlined week-icon">date_range</span>
              {{ formatDateShort(ts.week_start) }} – {{ formatDateShort(ts.week_end) }}
            </td>
            <td class="col-center">
              <span class="hours-badge">{{ ts.total_hours || 0 }}h</span>
            </td>
            <td>
              <span class="badge" :class="`badge-${ts.status}`">
                {{ formatTimesheetStatus(ts.status) }}
              </span>
            </td>
            <td>
              <div class="row-actions">
                <button class="btn-outline-sm" @click="viewDetail(ts)">
                  <span class="material-symbols-outlined">visibility</span>
                  Details
                </button>
                <template v-if="ts.status === 'submitted'">
                  <button class="icon-btn icon-btn-approve" title="Approve" @click="handleAction(ts.id, 'approved')" :disabled="actionLoading === ts.id">
                    <span class="material-symbols-outlined">check</span>
                  </button>
                  <button class="icon-btn icon-btn-reject" title="Reject" @click="openRejectModal(ts.id)" :disabled="actionLoading === ts.id">
                    <span class="material-symbols-outlined">close</span>
                  </button>
                </template>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="table-footer">
        <span class="page-info">
          {{ filtered.length }} {{ filtered.length === 1 ? 'timesheet' : 'timesheets' }}
        </span>
      </div>
    </div>

    <!-- Detail Modal -->
    <div v-if="showDetailModal" class="modal-backdrop">
      <div class="modal modal-wide">
        <div class="modal-header">
          <div class="modal-header-info">
            <h3 class="modal-title">Timesheet Breakdown</h3>
            <p class="modal-subtitle">
              {{ getUserName(selectedTimesheet.employee_id) }}
              &nbsp;·&nbsp;
              {{ formatDateShort(selectedTimesheet.week_start) }} – {{ formatDateShort(selectedTimesheet.week_end) }}
            </p>
          </div>
          <button class="modal-close" @click="closeDetailModal">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <div class="modal-body">
          <!-- Daily Hours Breakdown -->
          <div class="detail-section">
            <label class="section-label">Daily Hours Log</label>
            <TimesheetDailyGrid :timesheet="selectedTimesheet" :projects="projects" />
          </div>

          <!-- Weekly Overview -->
          <div v-if="selectedTimesheet.description" class="detail-section">
            <label class="section-label">Weekly Overview</label>
            <div class="overview-box">{{ selectedTimesheet.description }}</div>
          </div>
        </div>

        <div class="modal-footer" v-if="selectedTimesheet.status === 'submitted'">
          <button class="btn-cancel" @click="closeDetailModal">Close</button>
          <button class="btn-reject-action" @click="openRejectModal(selectedTimesheet.id)">
            <span class="material-symbols-outlined">close</span>
            Reject
          </button>
          <button class="btn-submit" @click="handleAction(selectedTimesheet.id, 'approved')">
            <span class="material-symbols-outlined">check</span>
            Approve Timesheet
          </button>
        </div>
        <div class="modal-footer" v-else>
          <button class="btn-cancel" @click="closeDetailModal">Close</button>
        </div>
      </div>
    </div>

    <!-- Reject Modal -->
    <div v-if="rejectModalOpen" class="modal-backdrop">
      <div class="modal modal-sm">
        <div class="modal-header">
          <div>
            <h3 class="modal-title">Reject Timesheet</h3>
            <p class="modal-subtitle">Provide a reason for the employee</p>
          </div>
          <button class="modal-close" @click="closeRejectModal">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-field">
            <label class="form-label">Rejection Reason *</label>
            <textarea
              v-model="rejectReason"
              rows="4"
              placeholder="Explain why this timesheet is being rejected..."
              class="form-input"
            ></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeRejectModal">Cancel</button>
          <button
            class="btn-danger"
            @click="confirmReject"
            :disabled="!rejectReason.trim() || actionLoading === rejectModalTarget"
          >
            {{ actionLoading === rejectModalTarget ? 'Rejecting…' : 'Reject Timesheet' }}
          </button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import TimesheetDailyGrid from '../components/timesheet/TimesheetDailyGrid.vue'
import { weeklyTimesheetsAPI } from '../api/weekly_timesheets'
import { usersAPI } from '../api/users'
import { projectsAPI } from '../api/projects'

const router = useRouter()

const timesheets = ref([])
const employees = ref([])
const loading = ref(true)
const filterEmployee = ref('')
const filterStatus = ref('')
const filterMonth = ref('')
const filterWeek = ref('')

const actionLoading = ref(null)
const rejectModalOpen = ref(false)
const rejectModalTarget = ref(null)
const rejectReason = ref('')

const showDetailModal = ref(false)
const selectedTimesheet = ref(null)
const projects = ref([])

async function fetchTimesheets() {
  loading.value = true
  try {
    const params = {}
    if (filterEmployee.value) params.employee_id = filterEmployee.value
    if (filterStatus.value) params.status = filterStatus.value

    const res = await weeklyTimesheetsAPI.getTimesheets(params)
    timesheets.value = res.data.sort((a, b) => new Date(b.week_start) - new Date(a.week_start))
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function fetchEmployees() {
  try {
    const res = await usersAPI.getUsers()
    employees.value = res.data
  } catch (e) {
    console.error(e)
  }
}

async function fetchProjects() {
  try {
    const res = await projectsAPI.getProjects()
    projects.value = res.data
  } catch (e) {
    console.error(e)
  }
}

onMounted(async () => {
  await Promise.all([fetchTimesheets(), fetchEmployees(), fetchProjects()])
})

watch([filterEmployee, filterStatus], () => {
  fetchTimesheets()
})

// Reset week filter when month changes (weeks are derived from month)
watch(filterMonth, () => {
  filterWeek.value = ''
})

const hasActiveFilters = computed(() => {
  return filterEmployee.value || filterStatus.value || filterMonth.value || filterWeek.value
})

function clearFilters() {
  filterEmployee.value = ''
  filterStatus.value = ''
  filterMonth.value = ''
  filterWeek.value = ''
  fetchTimesheets()
}

// Available weeks derived from current filter month or from all timesheets
const availableWeeks = computed(() => {
  let source = timesheets.value
  // If a month is selected, only show weeks overlapping that month
  if (filterMonth.value) {
    const [y, m] = filterMonth.value.split('-').map(Number)
    const monthStart = new Date(y, m - 1, 1)
    const monthEnd = new Date(y, m, 0) // last day of month
    source = source.filter(ts => {
      const ws = new Date(ts.week_start)
      const we = new Date(ts.week_end)
      return ws <= monthEnd && we >= monthStart
    })
  }
  const weekSet = new Map()
  for (const ts of source) {
    if (!weekSet.has(ts.week_start)) {
      weekSet.set(ts.week_start, {
        value: ts.week_start,
        label: `${formatDateShort(ts.week_start)} – ${formatDateShort(ts.week_end)}`
      })
    }
  }
  // Sort newest first
  return [...weekSet.values()].sort((a, b) => b.value.localeCompare(a.value))
})

const filtered = computed(() => {
  let list = timesheets.value

  // Month filter
  if (filterMonth.value) {
    const [y, m] = filterMonth.value.split('-').map(Number)
    const monthStart = new Date(y, m - 1, 1)
    const monthEnd = new Date(y, m, 0)
    list = list.filter(ts => {
      const ws = new Date(ts.week_start)
      const we = new Date(ts.week_end)
      return ws <= monthEnd && we >= monthStart
    })
  }

  // Week filter
  if (filterWeek.value) {
    list = list.filter(ts => ts.week_start === filterWeek.value)
  }

  return list
})


// Helpers
function getUserName(empId) {
  const emp = employees.value.find(e => e.id === empId)
  return emp ? emp.name : `Employee #${empId}`
}

function formatDateShort(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
}

function truncateDesc(desc) {
  if (!desc) return 'No description'
  return desc.length > 50 ? desc.slice(0, 50) + '...' : desc
}

function formatTimesheetStatus(s) {
  if (s === 'submitted') return 'Pending Review'
  return s.charAt(0).toUpperCase() + s.slice(1)
}

function goToEmployeeProfile(empId) {
  router.push(`/admin/employees/${empId}`)
}

async function handleAction(tsId, status, reason = null) {
  actionLoading.value = tsId
  try {
    await weeklyTimesheetsAPI.actionTimesheet(tsId, { status, rejection_reason: reason })
    const idx = timesheets.value.findIndex(t => t.id === tsId)
    if (idx !== -1) {
      timesheets.value[idx].status = status
      timesheets.value[idx].rejection_reason = reason
    }
  } catch (e) {
    console.error('Failed to update status', e)
  } finally {
    actionLoading.value = null
  }
}

function openRejectModal(tsId) {
  rejectModalTarget.value = tsId
  rejectReason.value = ''
  rejectModalOpen.value = true
}

function closeRejectModal() {
  rejectModalOpen.value = false
  rejectModalTarget.value = null
}

async function confirmReject() {
  if (rejectModalTarget.value) {
    await handleAction(rejectModalTarget.value, 'rejected', rejectReason.value)
    closeRejectModal()
    if (selectedTimesheet.value?.id === rejectModalTarget.value) {
      selectedTimesheet.value.status = 'rejected'
      selectedTimesheet.value.rejection_reason = rejectReason.value
    }
  }
}

function viewDetail(ts) {
  selectedTimesheet.value = ts
  showDetailModal.value = true
}

function closeDetailModal() {
  showDetailModal.value = false
  selectedTimesheet.value = null
}
</script>

<style scoped>
/* ── Page Header ── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}
.page-header-left { display: flex; flex-direction: column; gap: 2px; }
.page-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--color-on-surface);
  margin: 0;
}
.page-subtitle {
  font-size: 13px;
  color: var(--color-on-surface-variant);
  margin: 0;
}

/* ── Primary Button ── */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition);
}
.btn-primary:hover { background: #1f5c5d; }
.btn-primary .material-symbols-outlined { font-size: 18px; }

/* ── Filter Bar ── */
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl);
  padding: 12px 16px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-sm);
}
.filter-bar-left { display: flex; gap: 10px; align-items: center; }
.filter-select {
  padding: 8px 12px;
  background: var(--color-surface-dim);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  outline: none;
  transition: border var(--transition);
  cursor: pointer;
}
.filter-select:focus { border-color: var(--color-primary); background: var(--color-surface); }
.filter-month {
  min-width: 160px;
}
.btn-clear-filters {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 7px 14px;
  background: none;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  transition: all var(--transition);
}
.btn-clear-filters .material-symbols-outlined { font-size: 16px; }
.btn-clear-filters:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }

/* ── Table Card ── */
.table-card {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
}
.data-table thead {
  background: #f8fafc;
}
.data-table th {
  padding: 12px 16px;
  text-align: left;
  font-family: var(--font-body);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-on-surface-variant);
  border-bottom: 1px solid var(--color-outline);
}
.data-table td {
  padding: 12px 16px;
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}
.data-row:last-child td { border-bottom: none; }
.data-row:hover { background: #fafbfc; }
.col-center { text-align: center; }
.col-actions { width: 200px; }

.row-name { font-weight: 600; }
.row-link { color: var(--color-primary); cursor: pointer; }
.row-link:hover { text-decoration: underline; }
.cell-muted { color: var(--color-on-surface-variant); }
.cell-mono { font-variant-numeric: tabular-nums; }
.cell-week {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-on-surface-variant);
}
.week-icon { font-size: 16px; }

/* ── Hours Badge ── */
.hours-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  background: var(--color-primary-light);
  border-radius: var(--radius-full);
  font-size: 13px;
  font-weight: 700;
  color: var(--color-primary);
}

/* ── Status Badges ── */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.badge-submitted { background: #fef3c7; color: #92400e; }
.badge-pending   { background: #fef3c7; color: #92400e; }
.badge-approved  { background: #dcfce7; color: #166534; }
.badge-rejected  { background: #fee2e2; color: #991b1b; }

/* ── Row Actions ── */
.row-actions { display: flex; gap: 6px; align-items: center; }
.btn-outline-sm {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  background: transparent;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-on-surface);
  cursor: pointer;
  transition: all var(--transition);
}
.btn-outline-sm .material-symbols-outlined { font-size: 15px; }
.btn-outline-sm:hover { background: var(--color-outline-variant); border-color: var(--color-on-surface-variant); }

.icon-btn {
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition);
}
.icon-btn .material-symbols-outlined { font-size: 16px; }
.icon-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.icon-btn-approve .material-symbols-outlined { color: var(--color-success); }
.icon-btn-approve:hover:not(:disabled) { background: #dcfce7; border-color: #86efac; }
.icon-btn-reject .material-symbols-outlined { color: var(--color-error); }
.icon-btn-reject:hover:not(:disabled) { background: #fef2f2; border-color: #fca5a5; }

/* ── Empty State ── */
.empty-cell { text-align: center; padding: 0; }
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 48px 16px;
  color: var(--color-on-surface-variant);
}
.empty-icon { font-size: 36px; opacity: 0.4; }
.empty-state p { margin: 0; font-size: 13px; }

/* ── Table Footer ── */
.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8fafc;
  border-top: 1px solid var(--color-outline);
}
.page-info {
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface-variant);
}
.page-btns { display: flex; gap: 6px; }
.page-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  transition: all var(--transition);
}
.page-btn .material-symbols-outlined { font-size: 16px; }
.page-btn:hover:not(:disabled) { background: var(--color-outline-variant); color: var(--color-on-surface); }
.page-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* ── Modals ── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.14);
  max-width: 520px;
  width: 92%;
  max-height: 90vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.modal-wide { max-width: 800px; }
.modal-sm { max-width: 460px; }

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px 24px 20px;
  border-bottom: 1px solid var(--color-outline);
}
.modal-header-info { display: flex; flex-direction: column; gap: 2px; }
.modal-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--color-on-surface);
  margin: 0;
}
.modal-subtitle {
  font-size: 13px;
  color: var(--color-on-surface-variant);
  margin: 0;
}
.modal-close {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition);
  flex-shrink: 0;
}
.modal-close:hover { background: var(--color-outline-variant); }
.modal-close .material-symbols-outlined { font-size: 18px; color: var(--color-on-surface-variant); }

.modal-body {
  padding: 24px;
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 24px;
  border-top: 1px solid var(--color-outline);
  background: #f8fafc;
  border-radius: 0 0 var(--radius-xl) var(--radius-xl);
}

/* ── Detail Modal ── */
.detail-section { display: flex; flex-direction: column; gap: 10px; }
.section-label {
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-on-surface-variant);
}
.detail-table-wrapper {
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.detail-table {
  width: 100%;
  border-collapse: collapse;
}
.detail-table th {
  background: #f8fafc;
  padding: 10px 14px;
  text-align: left;
  font-family: var(--font-body);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-on-surface-variant);
  border-bottom: 1px solid var(--color-outline);
}
.detail-table td {
  padding: 10px 14px;
  font-size: 13px;
  border-bottom: 1px solid #f1f5f9;
  color: var(--color-on-surface);
}
.detail-table tbody tr:last-child td { border-bottom: none; }
.col-proj { width: 180px; }
.col-desc { line-height: 1.5; }
.col-right { text-align: right; }
.cell-mono { font-variant-numeric: tabular-nums; }
.total-row td { background: #f8fafc; border-top: 2px solid var(--color-outline); }
.total-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-on-surface-variant);
}
.total-val {
  font-size: 15px;
  font-weight: 800;
  color: var(--color-primary);
}

.project-tag {
  display: inline-flex;
  padding: 3px 8px;
  background: var(--color-primary-light);
  border: 1px solid rgba(40, 116, 117, 0.2);
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-primary);
}

.overview-box {
  padding: 14px 16px;
  background: var(--color-surface-dim);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  color: var(--color-on-surface);
}

/* ── Form ── */
.form-field { display: flex; flex-direction: column; gap: 6px; }
.form-label {
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-on-surface-variant);
}
.form-input {
  width: 100%;
  padding: 9px 12px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  outline: none;
  transition: border var(--transition);
  box-sizing: border-box;
}
.form-input:focus { border-color: var(--color-primary); }
textarea.form-input { resize: vertical; }

/* ── Action Buttons ── */
.btn-cancel {
  padding: 8px 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  transition: all var(--transition);
}
.btn-cancel:hover { background: var(--color-outline-variant); }
.btn-submit {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition);
}
.btn-submit .material-symbols-outlined { font-size: 16px; }
.btn-submit:hover:not(:disabled) { background: #1f5c5d; }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-reject-action {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  background: var(--color-surface);
  color: var(--color-error);
  border: 1px solid #fca5a5;
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition);
}
.btn-reject-action .material-symbols-outlined { font-size: 16px; }
.btn-reject-action:hover { background: var(--color-error); color: #fff; border-color: var(--color-error); }
.btn-danger {
  padding: 9px 18px;
  background: var(--color-error);
  color: #fff;
  border: none;
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition);
}
.btn-danger:hover:not(:disabled) { background: #b91c1c; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }

@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: 10px; }
  .filter-bar { flex-direction: column; align-items: stretch; gap: 8px; }
  .filter-bar-left { flex-wrap: wrap; }
  .table-card { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .data-table { min-width: 580px; }
}
</style>
