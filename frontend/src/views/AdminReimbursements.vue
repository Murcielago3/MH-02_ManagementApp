<template>
  <AppLayout>
    <!-- Page Header -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">Reimbursements</h1>
        <p class="page-subtitle">Review and approve employee reimbursement claims</p>
      </div>
      <button class="btn-primary" @click="fetchAll">
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
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>
      <button v-if="hasActiveFilters" class="btn-clear-filters" @click="clearFilters" title="Clear all filters">
        <span class="material-symbols-outlined">filter_alt_off</span>
        Clear
      </button>
    </div>

    <!-- Grouped-by-employee card -->
    <div class="table-card">
      <div v-if="loading" class="empty-state">
        <span class="material-symbols-outlined empty-icon">hourglass_empty</span>
        <p>Loading reimbursements...</p>
      </div>
      <div v-else-if="groups.length === 0" class="empty-state">
        <span class="material-symbols-outlined empty-icon">receipt_long</span>
        <p>No reimbursement records found.</p>
      </div>

      <div v-else class="emp-groups">
        <div v-for="g in groups" :key="g.employee_id" class="emp-group">
          <!-- Master row: one employee, collapsed -->
          <div class="emp-row" :class="{ open: isOpen(g.employee_id) }" @click="toggle(g.employee_id)">
            <span class="material-symbols-outlined chevron" :class="{ open: isOpen(g.employee_id) }">chevron_right</span>
            <span class="emp-name row-link" @click.stop="goToEmployeeProfile(g.employee_id)">{{ g.name }}</span>
            <span class="emp-count">{{ g.items.length }} claim{{ g.items.length === 1 ? '' : 's' }}</span>
            <span v-if="g.pendingCount" class="badge badge-pending">{{ g.pendingCount }} pending</span>
            <span class="emp-spacer"></span>
            <span class="emp-total-label">Total</span>
            <span class="emp-total">{{ formatCurrency(g.total) }}</span>
          </div>

          <!-- Detail: all of this employee's claims -->
          <div v-if="isOpen(g.employee_id)" class="emp-detail">
            <table class="data-table detail-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th class="col-right">Amount</th>
                  <th>Reason</th>
                  <th>Proof</th>
                  <th>Status</th>
                  <th>Salary slip</th>
                  <th class="col-actions">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in g.items" :key="item.id" class="data-row" :class="{ 'is-rejected': item.status === 'rejected' }">
                  <td class="cell-mono">{{ formatDateShort(item.date) }}</td>
                  <td class="col-right cell-mono amount-cell">{{ formatCurrency(item.amount) }}</td>
                  <td class="reason-cell" :title="item.reason">{{ item.reason }}</td>
                  <td>
                    <a v-if="item.proof_url" :href="resolveUrl(item.proof_url)" target="_blank" class="proof-link">
                      <span class="material-symbols-outlined">attachment</span> View
                    </a>
                    <span v-else class="cell-muted">--</span>
                  </td>
                  <td>
                    <span class="badge" :class="`badge-${item.status}`">{{ formatStatus(item.status) }}</span>
                  </td>
                  <td>
                    <span v-if="item.status === 'approved' && item.month_added" class="payroll-badge">
                      {{ payrollLabel(item.month_added) }}
                    </span>
                    <span v-else-if="item.status === 'pending'" class="payroll-projected" :title="'Rolls into this slip once approved'">
                      {{ payrollLabel(projectedMonth(item)) }}
                    </span>
                    <span v-else class="cell-muted">--</span>
                  </td>
                  <td>
                    <div class="row-actions" v-if="item.status === 'pending'">
                      <button class="icon-btn icon-btn-approve" title="Approve" @click="handleAction(item.id, 'approved')" :disabled="actionLoading === item.id">
                        <span class="material-symbols-outlined">check</span>
                      </button>
                      <button class="icon-btn icon-btn-reject" title="Reject" @click="handleAction(item.id, 'rejected')" :disabled="actionLoading === item.id">
                        <span class="material-symbols-outlined">close</span>
                      </button>
                    </div>
                    <span v-else class="cell-muted">--</span>
                  </td>
                </tr>
              </tbody>
              <tfoot>
                <tr class="detail-total-row">
                  <td class="col-right" colspan="2">{{ formatCurrency(g.total) }}</td>
                  <td colspan="5" class="detail-total-note">
                    Total across {{ g.items.length }} claim{{ g.items.length === 1 ? '' : 's' }}
                    <template v-if="g.pendingCount"> · {{ formatCurrency(g.pendingTotal) }} still pending</template>
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </div>

      <div v-if="!loading && groups.length" class="table-footer">
        <span class="page-info">
          {{ totalCount }} {{ totalCount === 1 ? 'reimbursement' : 'reimbursements' }} across
          {{ groups.length }} {{ groups.length === 1 ? 'employee' : 'employees' }}
        </span>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import { reimbursementsAPI } from '../api/reimbursements'
import { usersAPI } from '../api/users'

const router = useRouter()

const reimbursements = ref([])
const employees = ref([])
const loading = ref(true)
const filterEmployee = ref('')
const filterStatus = ref('')
const actionLoading = ref(null)

async function fetchReimbursements() {
  loading.value = true
  try {
    const params = {}
    if (filterEmployee.value) params.employee_id = filterEmployee.value
    if (filterStatus.value) params.status = filterStatus.value
    const res = await reimbursementsAPI.getReimbursements(params)
    reimbursements.value = res.data.sort((a, b) => new Date(b.date) - new Date(a.date))
  } catch (e) {
    console.error('Failed to fetch reimbursements', e)
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

async function fetchAll() {
  await Promise.all([fetchReimbursements(), fetchEmployees()])
}

onMounted(() => fetchAll())

watch([filterEmployee, filterStatus], () => {
  fetchReimbursements()
})

const hasActiveFilters = computed(() => filterEmployee.value || filterStatus.value)

function clearFilters() {
  filterEmployee.value = ''
  filterStatus.value = ''
  fetchReimbursements()
}

// ── Group by employee ──
// One master row per employee; expand to see every claim + the running total.
const groups = computed(() => {
  const byEmp = new Map()
  for (const item of reimbursements.value) {
    if (!byEmp.has(item.employee_id)) byEmp.set(item.employee_id, [])
    byEmp.get(item.employee_id).push(item)
  }
  const out = []
  for (const [employee_id, items] of byEmp.entries()) {
    items.sort((a, b) => new Date(b.date) - new Date(a.date))
    const total = items.reduce((s, i) => s + Number(i.amount || 0), 0)
    const pending = items.filter(i => i.status === 'pending')
    out.push({
      employee_id,
      name: getUserName(employee_id),
      items,
      total,
      pendingCount: pending.length,
      pendingTotal: pending.reduce((s, i) => s + Number(i.amount || 0), 0),
    })
  }
  out.sort((a, b) => a.name.localeCompare(b.name))
  return out
})

const totalCount = computed(() => reimbursements.value.length)

// ── Expand / collapse ──
const expanded = ref({})
function isOpen(empId) { return !!expanded.value[empId] }
function toggle(empId) {
  expanded.value = { ...expanded.value, [empId]: !expanded.value[empId] }
}

function getUserName(empId) {
  const emp = employees.value.find(e => e.id === empId)
  return emp ? emp.name : `Employee #${empId}`
}

// The salary-slip month a pending claim will roll into once approved — the month
// it was submitted (created_at), falling back to the expense date.
function projectedMonth(item) {
  const basis = item.created_at || item.date
  return basis ? String(basis).slice(0, 7) : null
}

// "2026-06" -> "Jun 2026"
function payrollLabel(ym) {
  if (!ym) return '--'
  const [y, m] = ym.split('-')
  const d = new Date(Number(y), Number(m) - 1, 1)
  return d.toLocaleDateString('en-GB', { month: 'short', year: 'numeric' })
}

function formatDateShort(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatStatus(s) {
  if (!s) return ''
  return s.charAt(0).toUpperCase() + s.slice(1)
}

const inrFmt = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
function formatCurrency(val) { return inrFmt.format(val || 0) }

function resolveUrl(url) {
  return usersAPI.resolveFileUrl(url)
}

function goToEmployeeProfile(empId) {
  router.push(`/admin/employees/${empId}`)
}

async function handleAction(id, status) {
  actionLoading.value = id
  try {
    await reimbursementsAPI.actionReimbursement(id, status)
    // Refetch so the payroll month (computed server-side from the submission
    // month) is accurate rather than guessed on the client.
    await fetchReimbursements()
  } catch (e) {
    console.error('Failed to update reimbursement', e)
  } finally {
    actionLoading.value = null
  }
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
.col-right { text-align: right; }
.col-actions { width: 100px; }

.row-name { font-weight: 600; }
.row-link { color: var(--color-primary); cursor: pointer; }
.row-link:hover { text-decoration: underline; }
.cell-muted { color: var(--color-on-surface-variant); }
.cell-mono { font-variant-numeric: tabular-nums; }

.amount-cell {
  font-weight: 700;
  color: var(--color-primary);
}

.reason-cell {
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.proof-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--color-primary);
  text-decoration: none;
  font-size: 12px;
  font-weight: 600;
}
.proof-link:hover { text-decoration: underline; }
.proof-link .material-symbols-outlined { font-size: 15px; }

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

.payroll-badge {
  display: inline-block;
  padding: 3px 8px;
  background: rgba(40, 116, 117, 0.1);
  color: var(--color-primary);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.payroll-projected {
  display: inline-block;
  padding: 3px 8px;
  border: 1px dashed var(--color-outline);
  color: var(--color-on-surface-variant);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

/* ── Employee groups (master rows) ── */
.emp-groups { display: flex; flex-direction: column; }
.emp-group { border-bottom: 1px solid var(--color-outline); }
.emp-group:last-child { border-bottom: none; }
.emp-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  cursor: pointer;
  transition: background var(--transition);
}
.emp-row:hover { background: #fafbfc; }
.emp-row.open { background: #f8fafc; }
.chevron {
  font-size: 20px;
  color: var(--color-on-surface-variant);
  transition: transform var(--transition);
}
.chevron.open { transform: rotate(90deg); }
.emp-name { font-weight: 700; font-size: 14px; }
.emp-count {
  font-size: 12px;
  color: var(--color-on-surface-variant);
  font-weight: 600;
}
.emp-spacer { flex: 1; }
.emp-total-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-on-surface-variant);
  font-weight: 700;
}
.emp-total {
  font-variant-numeric: tabular-nums;
  font-weight: 800;
  font-size: 15px;
  color: var(--color-primary);
  min-width: 96px;
  text-align: right;
}

/* ── Detail (expanded) table ── */
.emp-detail { background: #fcfdfe; padding: 0 16px 12px 40px; }
.detail-table { background: var(--color-surface); border: 1px solid var(--color-outline); border-radius: var(--radius-lg); overflow: hidden; }
.detail-table thead { background: #f8fafc; }
.data-row.is-rejected td:not(.col-actions) { opacity: 0.55; }
.detail-total-row td {
  background: #f8fafc;
  border-top: 1px solid var(--color-outline);
  font-weight: 800;
  color: var(--color-primary);
  font-variant-numeric: tabular-nums;
}
.detail-total-note { font-weight: 600; color: var(--color-on-surface-variant); font-size: 12px; }

/* ── Row Actions ── */
.row-actions { display: flex; gap: 6px; align-items: center; }
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

@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: 10px; }
  .filter-bar { flex-direction: column; align-items: stretch; gap: 8px; }
  .filter-bar-left { flex-wrap: wrap; }
  .table-card { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .data-table { min-width: 700px; }
  .reason-cell { max-width: 140px; }
}
</style>
