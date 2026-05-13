<template>
  <AppLayout>
    <!-- Page Actions -->
    <div class="page-actions">
      <div class="actions-left">
        <select v-model="filterEmployee" class="emp-select">
          <option value="">All Employees</option>
          <option v-for="emp in employees" :key="emp.id" :value="emp.id">{{ emp.name }}</option>
        </select>
        <select v-model="filterStatus" class="emp-select">
          <option value="">All Statuses</option>
          <option value="submitted">Pending Review</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>
      <div class="actions-right">
        <button class="today-btn" @click="fetchTimesheets">
          <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">refresh</span> Refresh
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="table-card">
      <table class="proj-table">
        <thead>
          <tr>
            <th>Employee</th>
            <th>Week</th>
            <th class="text-center">Hours</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="5" class="empty-cell"><div class="loading-text">Loading timesheets…</div></td>
          </tr>
          <tr v-else-if="filtered.length === 0">
            <td colspan="5" class="empty-cell">No timesheet records found.</td>
          </tr>
          <tr v-for="ts in paginated" :key="ts.id" class="proj-row">
            <td>
              <span class="proj-name" style="cursor: pointer;" @click="goToEmployeeProfile(ts.employee_id)">
                {{ getUserName(ts.employee_id) }}
              </span>
            </td>
            <td class="mono">{{ formatDateShort(ts.week_start) }} – {{ formatDateShort(ts.week_end) }}</td>
            <td class="text-center">
              <span class="hours-badge">{{ ts.total_hours || 0 }}h</span>
            </td>
            <td>
              <span class="status-badge" :class="`status-${ts.status}`">
                {{ formatTimesheetStatus(ts.status) }}
              </span>
            </td>
            <td class="action-cell">
              <div class="ts-actions">
                <button class="btn-outline" @click="viewDetail(ts)">
                  <span class="material-symbols-outlined">visibility</span>
                  Details
                </button>
                <template v-if="ts.status === 'submitted'">
                  <button class="btn-approve" @click="handleAction(ts.id, 'approved')" :disabled="actionLoading === ts.id">
                    <span class="material-symbols-outlined">check</span>
                  </button>
                  <button class="btn-reject" @click="openRejectModal(ts.id)" :disabled="actionLoading === ts.id">
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
          Showing {{ filtered.length === 0 ? 0 : startIdx + 1 }} to {{ endIdx }} of {{ filtered.length }} entries
        </span>
        <div class="page-btns">
          <button class="page-btn" :disabled="currentPage === 1" @click="currentPage--">Prev</button>
          <button class="page-btn" :disabled="currentPage >= totalPages" @click="currentPage++">Next</button>
        </div>
      </div>
    </div>

    <!-- Detail Modal -->
    <div v-if="showDetailModal" class="modal-backdrop" @click.self="closeDetailModal">
      <div class="modal-content detail-modal">
        <div class="modal-header">
          <div class="header-info">
            <h3>Timesheet Breakdown</h3>
            <p>{{ getUserName(selectedTimesheet.employee_id) }} · {{ formatDateShort(selectedTimesheet.week_start) }} - {{ formatDateShort(selectedTimesheet.week_end) }}</p>
          </div>
          <button class="btn-close" @click="closeDetailModal">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <div class="modal-body">
          <div class="detail-section">
            <div class="detail-table-wrapper">
              <table class="detail-table">
                <thead>
                  <tr>
                    <th>Project</th>
                    <th>Task Description</th>
                    <th class="text-right">Hours</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="entry in selectedTimesheet.entries" :key="entry.id">
                    <td class="col-proj">
                      <span class="project-tag">{{ getProjectName(entry.project_id) }}</span>
                    </td>
                    <td class="col-desc">{{ entry.description }}</td>
                    <td class="text-right mono">{{ entry.hours }}h</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr>
                    <td colspan="2" class="text-right font-bold">Total Time</td>
                    <td class="text-right font-bold total-val">{{ selectedTimesheet.total_hours }}h</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          <div v-if="selectedTimesheet.description" class="detail-section">
            <label>Weekly Overview</label>
            <div class="overview-box">{{ selectedTimesheet.description }}</div>
          </div>
        </div>

        <div class="modal-footer" v-if="selectedTimesheet.status === 'submitted'">
          <div class="footer-actions">
            <button class="btn-reject-large" @click="openRejectModal(selectedTimesheet.id)">Reject</button>
            <button class="btn-approve-large" @click="handleAction(selectedTimesheet.id, 'approved')">Approve Timesheet</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Reject Modal -->
    <div v-if="rejectModalOpen" class="modal-backdrop" @click.self="closeRejectModal">
      <div class="modal-content">
        <h3>Reject Timesheet</h3>
        <p>Please provide a reason for rejecting this timesheet.</p>
        <textarea v-model="rejectReason" rows="3" placeholder="Reason..."></textarea>
        <div class="modal-actions">
          <button class="btn-cancel" @click="closeRejectModal">Cancel</button>
          <button class="btn-reject-confirm" @click="confirmReject" :disabled="!rejectReason.trim() || actionLoading === rejectModalTarget">
            Reject Timesheet
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
import { weeklyTimesheetsAPI } from '../api/weekly_timesheets'
import { usersAPI } from '../api/users'
import { projectsAPI } from '../api/projects'

const router = useRouter()

const timesheets = ref([])
const employees = ref([])
const loading = ref(true)
const filterEmployee = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const perPage = 10

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
  currentPage.value = 1
  fetchTimesheets()
})

const filtered = computed(() => timesheets.value)

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage)))
const startIdx = computed(() => (currentPage.value - 1) * perPage)
const endIdx = computed(() => Math.min(startIdx.value + perPage, filtered.value.length))
const paginated = computed(() => filtered.value.slice(startIdx.value, endIdx.value))

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

function getProjectName(id) {
  const p = projects.value.find(proj => proj.id === id)
  return p ? p.name : 'Unknown Project'
}
</script>

<style scoped>
.page-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.actions-left { display: flex; gap: 8px; align-items: center; }
.actions-right { display: flex; gap: 8px; align-items: center; }

.emp-select {
  padding: 8px 12px; background: #fff; border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg); font-family: var(--font-display); font-size: 13px;
  color: var(--color-on-surface); outline: none; transition: border 0.15s;
}
.emp-select:focus { border-color: var(--color-primary); }

.today-btn {
  display: flex; align-items: center;
  padding: 8px 16px; background: var(--color-primary); color: #fff; border: none;
  border-radius: var(--radius-lg); font-family: var(--font-display); font-size: 13px;
  font-weight: 500; cursor: pointer; transition: background 0.15s;
}
.today-btn:hover { background: #0f766e; }

.table-card {
  background: #fff; border: 1px solid var(--color-surface-container-high); border-radius: var(--radius-lg);
  overflow: hidden;
}
.proj-table {
  width: 100%; border-collapse: collapse;
}
.proj-table th {
  padding: 12px 16px; text-align: left; font-family: var(--font-display);
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--color-on-surface-variant); border-bottom: 1px solid var(--color-surface-container-high);
  background: var(--color-background);
}
.proj-table td {
  padding: 12px 16px; border-bottom: 1px solid var(--color-surface-container);
  font-family: var(--font-display); font-size: 13px; color: var(--color-on-surface);
}
.proj-row:hover { background: var(--color-background); }
.proj-name { font-weight: 500; color: var(--color-primary); }
.proj-name:hover { text-decoration: underline; }

.muted { color: var(--color-on-surface-variant); }
.mono { font-variant-numeric: tabular-nums; }
.desc-cell { max-width: 250px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.empty-cell {
  text-align: center; padding: 48px 16px; color: var(--color-on-surface-variant);
  font-family: var(--font-display); font-size: 13px;
}
.loading-text { color: var(--color-on-surface-variant); }

.table-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; background: var(--color-background); border-top: 1px solid var(--color-surface-container-high);
}
.page-info {
  font-family: var(--font-display); font-size: 13px; color: var(--color-on-surface-variant);
}
.page-btns { display: flex; gap: 4px; }
.page-btn {
  padding: 6px 12px; background: #fff; border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius); font-family: var(--font-display); font-size: 13px;
  color: var(--color-on-surface-variant); cursor: pointer; transition: all 0.15s;
}
.page-btn:hover:not(:disabled) { background: var(--color-surface-container); }
.page-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.status-badge {
  padding: 4px 8px; border-radius: var(--radius-lg); font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.05em;
}
.status-badge.status-pending { background: #fef3c7; color: #92400e; }
.status-badge.status-submitted { background: #fef3c7; color: #92400e; }
.status-badge.status-approved { background: #dcfce7; color: #166534; }
.status-badge.status-rejected { background: #fee2e2; color: #991b1b; }

.ts-actions {
  display: flex; gap: 8px;
}
.btn-approve, .btn-reject, .btn-outline {
  display: flex; align-items: center; gap: 4px; padding: 4px 8px;
  border-radius: 4px; font-size: 11px; font-weight: 700; cursor: pointer;
  border: 1px solid transparent; transition: all 0.2s;
}
.btn-approve { background: var(--color-primary); color: #fff; }
.btn-approve:hover:not(:disabled) { background: #1a4e4f; }
.btn-reject { background: transparent; border-color: #ef4444; color: #ef4444; }
.btn-reject:hover:not(:disabled) { background: #fef2f2; }
.btn-outline { background: transparent; border-color: var(--color-outline); color: var(--color-on-surface); }
.btn-outline:hover { background: var(--color-surface-container); }
.btn-approve:disabled, .btn-reject:disabled { opacity: 0.5; cursor: not-allowed; }

/* Modal Base */
.modal-backdrop {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.5); display: flex; align-items: center;
  justify-content: center; z-index: 1000;
}
.modal-content {
  background: #fff; padding: 24px; border-radius: var(--radius-lg);
  width: 100%; max-width: 400px;
  display: flex; flex-direction: column; gap: 16px;
}
.modal-content h3 { margin: 0; font-family: var(--font-display); }
.modal-content p { margin: 0; font-size: 14px; color: var(--color-on-surface-variant); }
.modal-content textarea {
  padding: 8px; border: 1px solid var(--color-outline-variant); border-radius: 4px;
  font-family: var(--font-body); resize: vertical;
}
.modal-actions {
  display: flex; justify-content: flex-end; gap: 8px;
}
.btn-cancel {
  padding: 8px 16px; background: transparent; border: 1px solid var(--color-outline-variant);
  border-radius: 4px; cursor: pointer;
}
.btn-reject-confirm {
  padding: 8px 16px; background: #ef4444; color: #fff; border: none;
  border-radius: 4px; cursor: pointer;
}
.btn-reject-confirm:disabled { opacity: 0.5; }

.text-center { text-align: center; }
.text-right { text-align: right; }
.font-bold { font-weight: 700; }

.hours-badge {
  padding: 4px 10px;
  background: var(--color-surface-container);
  border-radius: 99px;
  font-size: 13px;
  font-weight: 700;
  color: var(--color-primary);
}

/* Detail Modal Styles */
.detail-modal {
  max-width: 800px;
  width: 90%;
  padding: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 24px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-outline-variant);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-info h3 {
  margin: 0 0 4px 0;
  font-family: var(--font-display);
  font-size: 20px;
}

.header-info p {
  margin: 0;
  font-size: 14px;
  color: var(--color-on-surface-variant);
}

.btn-close {
  background: none;
  border: none;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  padding: 4px;
}

.modal-body {
  padding: 24px;
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-section label {
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-on-surface-variant);
}

.detail-table-wrapper {
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.detail-table {
  width: 100%;
  border-collapse: collapse;
}

.detail-table th {
  background: var(--color-surface-container-low);
  padding: 12px;
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
  border-bottom: 1px solid var(--color-outline-variant);
}

.detail-table td {
  padding: 12px;
  border-bottom: 1px solid var(--color-surface-container-high);
  font-size: 14px;
}

.col-proj { width: 180px; }
.col-desc { line-height: 1.5; }

.project-tag {
  display: inline-block;
  padding: 4px 8px;
  background: var(--color-surface-container);
  border: 1px solid var(--color-outline-variant);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-primary);
}

.total-val {
  font-size: 16px;
  color: var(--color-primary);
}

.overview-box {
  padding: 16px;
  background: var(--color-surface-container-low);
  border-radius: var(--radius-md);
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.modal-footer {
  padding: 20px 24px;
  background: var(--color-surface-container-low);
  border-top: 1px solid var(--color-outline-variant);
}

.footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-approve-large {
  padding: 10px 20px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-weight: 700;
  cursor: pointer;
}

.btn-reject-large {
  padding: 10px 20px;
  background: #fff;
  color: #dc2626;
  border: 1px solid #dc2626;
  border-radius: var(--radius-md);
  font-weight: 700;
  cursor: pointer;
}

.btn-approve-large:hover { background: #1a4e4f; }
.btn-reject-large:hover { background: #fef2f2; }
</style>

