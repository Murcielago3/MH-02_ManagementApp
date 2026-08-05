<template>
  <AppLayout>
    <!-- Page Header -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">Leave Requests</h1>
        <p class="page-subtitle">Review and manage employee leave applications</p>
      </div>
      <button class="btn-primary" @click="openAbsent">
        <span class="material-symbols-outlined">person_off</span>
        Mark Absent
      </button>
    </div>

    <!-- Mark Absent modal -->
    <Teleport to="body">
      <div v-if="absentOpen" class="modal-backdrop">
        <div class="modal modal-sm">
          <div class="modal-header">
            <div>
              <h3 class="modal-title">Mark Absent</h3>
              <p class="modal-subtitle">Record an absence for an employee who didn't apply</p>
            </div>
            <button class="modal-close" @click="absentOpen = false">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <div class="modal-body absent-body">
            <label class="af">
              <span>Employee *</span>
              <select v-model.number="absent.employee_id">
                <option :value="null" disabled>Select employee</option>
                <option v-for="e in absentEmployees" :key="e.id" :value="e.id">{{ e.name }}</option>
              </select>
            </label>
            <div class="af-row">
              <label class="af">
                <span>From *</span>
                <input v-model="absent.start_date" type="date" />
              </label>
              <label class="af">
                <span>To (optional)</span>
                <input v-model="absent.end_date" type="date" :min="absent.start_date" />
              </label>
            </div>
            <label class="af">
              <span>Reason</span>
              <input v-model="absent.reason" type="text" placeholder="e.g. Unreported absence" />
            </label>
            <label class="af-check">
              <input v-model="absent.unpaid" type="checkbox" />
              <span>Loss of pay — count every working day as unpaid (don't touch leave balance)</span>
            </label>
            <p class="af-note">
              <template v-if="absent.unpaid">All working days will be deducted from salary.</template>
              <template v-else>Days draw from comp-off then paid balance; any overflow is unpaid, exactly like an approved leave.</template>
            </p>
            <p v-if="absentError" class="af-error">{{ absentError }}</p>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="absentOpen = false">Cancel</button>
            <button class="btn-submit" :disabled="!absent.employee_id || !absent.start_date || absentSaving" @click="submitAbsent">
              {{ absentSaving ? 'Saving…' : 'Mark Absent' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Filter Bar -->
    <div class="filter-bar">
      <div class="filter-bar-left">
        <div class="search-box">
          <span class="material-symbols-outlined search-icon">search</span>
          <input v-model="searchQuery" type="text" placeholder="Search by employee or reason..." class="search-input" />
        </div>
        <select v-model="filterStatus" class="filter-select">
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>
    </div>

    <!-- Table Card -->
    <div class="table-card">
      <table class="data-table">
        <thead>
          <tr>
            <th>Employee</th>
            <th>Start Date</th>
            <th>End Date</th>
            <th>Days</th>
            <th>Reason</th>
            <th>Status</th>
            <th class="col-actions">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="7" class="empty-cell">
              <div class="empty-state">
                <span class="material-symbols-outlined empty-icon">hourglass_empty</span>
                <p>Loading leave requests…</p>
              </div>
            </td>
          </tr>
          <tr v-else-if="filtered.length === 0">
            <td colspan="7" class="empty-cell">
              <div class="empty-state">
                <span class="material-symbols-outlined empty-icon">event_busy</span>
                <p>No leave requests found.</p>
              </div>
            </td>
          </tr>
          <tr v-for="l in filtered" :key="l.id" class="data-row">
            <td><span class="row-name">{{ l.employee?.name }}</span></td>
            <td class="cell-mono">{{ formatDate(l.start_date) }}</td>
            <td class="cell-mono">{{ formatDate(l.end_date) }}</td>
            <td>
              <span class="days-pill">{{ l.days_count }}d</span>
            </td>
            <td class="cell-muted cell-reason">{{ l.reason }}</td>
            <td>
              <span class="badge" :class="`badge-${l.status}`">
                {{ l.status }}
              </span>
            </td>
            <td>
              <div class="row-actions" v-if="l.status === 'pending'">
                <button class="action-btn action-approve" title="Approve" @click="actionLeave(l, 'approved')">
                  <span class="material-symbols-outlined">check</span>
                  Approve
                </button>
                <button class="action-btn action-reject" title="Reject" @click="actionLeave(l, 'rejected')">
                  <span class="material-symbols-outlined">close</span>
                  Reject
                </button>
              </div>
              <span v-else class="cell-muted no-action">-</span>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="table-footer">
        <span class="page-info">
          {{ filtered.length }} {{ filtered.length === 1 ? 'request' : 'requests' }}
        </span>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import { leavesAPI } from '../api/leaves'
import { usersAPI } from '../api/users'
import { toLocalDateStr } from '../utils/date'

const leaves = ref([])
const loading = ref(true)
const searchQuery = ref('')
const filterStatus = ref('')

async function fetchLeaves() {
  loading.value = true
  try {
    const res = await leavesAPI.getLeaves()
    leaves.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

// ── Mark Absent ──
const absentEmployees = ref([])
const absentOpen = ref(false)
const absentSaving = ref(false)
const absentError = ref('')
const absent = reactive({ employee_id: null, start_date: toLocalDateStr(), end_date: '', reason: '', unpaid: false })

async function fetchEmployeesForAbsent() {
  try {
    const res = await usersAPI.getUsers()
    absentEmployees.value = (res.data || [])
      .filter(u => u.role === 'employee' || u.role === 'project_manager')
      .sort((a, b) => a.name.localeCompare(b.name))
  } catch (e) { /* non-fatal */ }
}
function openAbsent() {
  Object.assign(absent, { employee_id: null, start_date: toLocalDateStr(), end_date: '', reason: '', unpaid: false })
  absentError.value = ''
  absentOpen.value = true
}
async function submitAbsent() {
  if (!absent.employee_id || !absent.start_date) return
  absentSaving.value = true
  absentError.value = ''
  try {
    await leavesAPI.markAbsent({
      employee_id: absent.employee_id,
      start_date: absent.start_date,
      end_date: absent.end_date || null,
      reason: absent.reason?.trim() || null,
      unpaid: absent.unpaid,
    })
    absentOpen.value = false
    await fetchLeaves()
  } catch (e) {
    absentError.value = e.response?.data?.detail || 'Could not mark absent.'
  } finally {
    absentSaving.value = false
  }
}

onMounted(() => { fetchLeaves(); fetchEmployeesForAbsent() })

const filtered = computed(() => {
  let list = [...leaves.value]
  list.sort((a, b) => new Date(b.start_date) - new Date(a.start_date))
  if (filterStatus.value) list = list.filter(l => l.status === filterStatus.value)
  const q = searchQuery.value.toLowerCase()
  if (q) list = list.filter(l =>
    (l.employee?.name || '').toLowerCase().includes(q) ||
    l.reason.toLowerCase().includes(q)
  )
  return list
})

async function actionLeave(leave, status) {
  try {
    await leavesAPI.actionLeave(leave.id, status)
    await fetchLeaves()
  } catch (e) {
    console.error(e)
  }
}

// Helpers
function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('en-IN')
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
.search-box { position: relative; }
.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-on-surface-variant);
  font-size: 18px;
  pointer-events: none;
}
.search-input {
  padding: 8px 12px 8px 36px;
  background: var(--color-surface-dim);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  outline: none;
  transition: border var(--transition);
  min-width: 260px;
}
.search-input:focus { border-color: var(--color-primary); background: var(--color-surface); }
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
.col-actions { width: 180px; }

.row-name { font-weight: 600; }
.cell-muted { color: var(--color-on-surface-variant); }
.cell-mono { font-variant-numeric: tabular-nums; }
.cell-reason {
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.no-action { display: block; text-align: center; }

/* ── Days Pill ── */
.days-pill {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  background: var(--color-outline-variant);
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 700;
  color: var(--color-on-surface-variant);
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
.badge-pending  { background: #fef3c7; color: #92400e; }
.badge-approved { background: #dcfce7; color: #166534; }
.badge-rejected { background: #fee2e2; color: #991b1b; }

/* ── Row Actions ── */
.row-actions { display: flex; gap: 6px; align-items: center; }
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all var(--transition);
}
.action-btn .material-symbols-outlined { font-size: 15px; }
.action-approve {
  background: var(--color-primary-light);
  color: var(--color-primary);
  border-color: var(--color-primary);
}
.action-approve:hover { background: var(--color-primary); color: #fff; }
.action-reject {
  background: #fef2f2;
  color: var(--color-error);
  border-color: #fca5a5;
}
.action-reject:hover { background: var(--color-error); color: #fff; }

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

@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: 10px; }
  .filter-bar { flex-direction: column; align-items: stretch; gap: 8px; }
  .filter-bar-left { flex-wrap: wrap; }
  .table-card { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .data-table { min-width: 620px; }
  .row-actions { flex-wrap: nowrap; }
}

/* Mark Absent */
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.btn-primary {
  display: inline-flex; align-items: center; gap: 6px; padding: 9px 16px;
  background: var(--color-primary); color: #fff; border: none; border-radius: var(--radius-lg, 10px);
  font-size: 13px; font-weight: 700; cursor: pointer;
}
.btn-primary:hover { filter: brightness(1.05); }
.btn-primary .material-symbols-outlined { font-size: 18px; }
.absent-body { display: flex; flex-direction: column; gap: 12px; }
.af { display: flex; flex-direction: column; gap: 4px; font-size: 12px; font-weight: 700; color: var(--color-on-surface-variant); }
.af input, .af select {
  padding: 9px 11px; border: 1px solid var(--color-outline); border-radius: var(--radius-md, 8px);
  font-size: 13px; font-weight: 500; background: var(--color-surface); color: var(--color-on-surface); outline: none;
}
.af input:focus, .af select:focus { border-color: var(--color-primary); }
.af-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.af-check { display: flex; align-items: flex-start; gap: 8px; font-size: 12px; color: var(--color-on-surface); cursor: pointer; }
.af-check input { margin-top: 2px; }
.af-note { font-size: 11px; color: var(--color-on-surface-variant); margin: 0; line-height: 1.5; }
.af-error { font-size: 12px; color: var(--color-error, #dc2626); margin: 0; }

/* Mark Absent modal container */
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
  max-width: 560px;
  width: 92%;
  max-height: 90vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.modal-sm { max-width: 420px; }
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px 24px 20px;
  border-bottom: 1px solid var(--color-outline);
}
.modal-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--color-on-surface);
  margin: 0 0 2px;
}
.modal-subtitle { font-size: 13px; color: var(--color-on-surface-variant); margin: 0; }
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
.modal-body { padding: 24px; flex: 1; }
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 24px;
  border-top: 1px solid var(--color-outline);
  background: #f8fafc;
  border-radius: 0 0 var(--radius-xl) var(--radius-xl);
}
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
.btn-submit:hover:not(:disabled) { background: #1f5c5d; }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
