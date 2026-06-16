<template>
  <AppLayout>
    <!-- Page Header -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">Salary Slips</h1>
        <p class="page-subtitle">Monthly pay = base salary + approved reimbursements − TDS. Slips generate automatically and are approved here.</p>
      </div>
      <div class="gen-group">
        <select v-model="genMonth" class="gen-select" title="Month to generate">
          <option value="">All eligible (auto)</option>
          <option v-for="m in genMonthOptions" :key="m" :value="m">{{ monthLabel(m) }}</option>
        </select>
        <button class="btn-primary" :disabled="generating" @click="handleGenerate">
          <span class="material-symbols-outlined" :class="{ 'spin-icon': generating }">{{ generating ? 'progress_activity' : 'autorenew' }}</span>
          {{ generating ? 'Generating…' : 'Generate Slips' }}
        </button>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="filter-bar">
      <div class="filter-bar-left">
        <select v-model="filterMonth" class="filter-select">
          <option value="">All Months</option>
          <option v-for="m in monthOptions" :key="m" :value="m">{{ monthLabel(m) }}</option>
        </select>
        <select v-model="filterEmployee" class="filter-select">
          <option value="">All Employees</option>
          <option v-for="emp in employees" :key="emp.id" :value="emp.id">{{ emp.name }}</option>
        </select>
        <select v-model="filterStatus" class="filter-select">
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
        </select>
      </div>
      <button
        v-if="filterMonth && pendingInMonth > 0"
        class="btn-approve-month"
        :disabled="approvingMonth"
        @click="handleApproveMonth"
      >
        <span class="material-symbols-outlined">done_all</span>
        Approve all {{ pendingInMonth }} pending in {{ monthLabel(filterMonth) }}
      </button>
    </div>

    <!-- Bulk Action Bar -->
    <transition name="bulk-slide">
      <div v-if="selected.length > 0" class="bulk-bar">
        <div class="bulk-info">
          <span class="material-symbols-outlined">check_box</span>
          <strong>{{ selected.length }}</strong> selected
          <button class="bulk-clear" @click="clearSelection">Clear</button>
        </div>
        <div class="bulk-actions">
          <div class="bulk-tds">
            <input
              v-model.number="bulkTds"
              type="number" min="0" max="100" step="0.5"
              class="bulk-tds-input"
              placeholder="TDS %"
            />
            <button class="bulk-btn-outline" :disabled="bulkBusy || bulkTds === null || bulkTds === ''" @click="handleBulkTds">
              Apply TDS %
            </button>
          </div>
          <button class="bulk-btn-approve" :disabled="bulkBusy" @click="handleBulkApprove">
            <span class="material-symbols-outlined">{{ bulkBusy ? 'progress_activity' : 'done_all' }}</span>
            Approve Selected
          </button>
        </div>
      </div>
    </transition>

    <!-- Table Card -->
    <div class="table-card">
      <table class="data-table">
        <thead>
          <tr>
            <th class="col-check">
              <input
                type="checkbox"
                class="row-check"
                :checked="allPendingSelected"
                :indeterminate.prop="someSelected"
                :disabled="pendingFiltered.length === 0"
                @change="toggleAll"
                title="Select all pending"
              />
            </th>
            <th>Employee</th>
            <th>Month</th>
            <th class="col-right">Base</th>
            <th class="col-right">Reimbursements</th>
            <th class="col-right">TDS</th>
            <th class="col-right">Net Pay</th>
            <th>Payout Date</th>
            <th>Status</th>
            <th class="col-actions">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="10" class="empty-cell">
              <div class="empty-state">
                <span class="material-symbols-outlined empty-icon">hourglass_empty</span>
                <p>Loading salary slips…</p>
              </div>
            </td>
          </tr>
          <tr v-else-if="filtered.length === 0">
            <td colspan="10" class="empty-cell">
              <div class="empty-state">
                <span class="material-symbols-outlined empty-icon">paid</span>
                <p>No salary slips yet. Click "Generate Slips" to create them for completed months.</p>
              </div>
            </td>
          </tr>
          <tr v-for="s in filtered" :key="s.id" class="data-row" :class="{ 'is-selected': isSelected(s.id) }" @click="openReview(s)">
            <td class="col-check" @click.stop>
              <input
                v-if="s.status === 'pending'"
                type="checkbox"
                class="row-check"
                :checked="isSelected(s.id)"
                @change="toggleOne(s.id)"
              />
              <span v-else class="material-symbols-outlined check-locked" title="Approved">lock</span>
            </td>
            <td><span class="row-name">{{ s.employee_name || `#${s.employee_id}` }}</span></td>
            <td class="cell-muted">{{ monthLabel(s.month) }}</td>
            <td class="col-right cell-mono">{{ formatCurrency(s.base_salary) }}</td>
            <td class="col-right cell-mono">
              <span :class="s.reimbursement_total > 0 ? 'reimb-pos' : 'cell-muted'">
                {{ s.reimbursement_total > 0 ? '+ ' + formatCurrency(s.reimbursement_total) : '—' }}
              </span>
            </td>
            <td class="col-right cell-mono tds-neg">− {{ formatCurrency(s.tds_amount) }}</td>
            <td class="col-right cell-mono cell-amount">{{ formatCurrency(s.net_total) }}</td>
            <td class="cell-mono cell-muted">{{ formatDate(s.payout_date) }}</td>
            <td>
              <span class="badge" :class="`badge-${s.status}`">{{ formatStatus(s.status) }}</span>
            </td>
            <td @click.stop>
              <div class="row-actions">
                <button class="icon-btn icon-btn-edit" title="Review" @click="openReview(s)">
                  <span class="material-symbols-outlined">visibility</span>
                </button>
                <button
                  v-if="s.status === 'pending'"
                  class="icon-btn icon-btn-approve"
                  title="Approve"
                  :disabled="actionLoading === s.id"
                  @click="quickApprove(s)"
                >
                  <span class="material-symbols-outlined">check</span>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="table-footer">
        <span class="page-info">
          {{ filtered.length }} {{ filtered.length === 1 ? 'slip' : 'slips' }}
          <template v-if="filtered.length"> · Net total {{ formatCurrency(filteredNetTotal) }}</template>
        </span>
      </div>
    </div>

    <!-- Review / Edit Modal -->
    <Teleport to="body">
      <div v-if="reviewSlip" class="modal-backdrop" @click.self="closeReview">
        <div class="modal">
          <div class="modal-header">
            <div>
              <h3 class="modal-title">Salary Slip — {{ reviewSlip.employee_name }}</h3>
              <p class="modal-subtitle">{{ monthLabel(reviewSlip.month) }}</p>
            </div>
            <button class="modal-close" @click="closeReview">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>

          <div class="modal-body">
            <!-- Payslip sheet -->
            <div class="slip-sheet">
              <div class="sheet-row">
                <span class="sheet-label">Base Salary</span>
                <span class="sheet-val">{{ formatCurrency(reviewSlip.base_salary) }}</span>
              </div>

              <!-- Reimbursement line items -->
              <div class="sheet-subsection" v-if="reviewSlip.reimbursements && reviewSlip.reimbursements.length">
                <div class="sheet-sub-label">Approved Reimbursements</div>
                <div v-for="r in reviewSlip.reimbursements" :key="r.id" class="sheet-reimb-row">
                  <span class="reimb-reason">{{ r.reason }}</span>
                  <span class="reimb-amt">+ {{ formatCurrency(r.amount) }}</span>
                </div>
              </div>
              <div class="sheet-row" v-else>
                <span class="sheet-label">Reimbursements</span>
                <span class="sheet-val cell-muted">None this month</span>
              </div>
              <div class="sheet-row sub">
                <span class="sheet-label">Reimbursements Total</span>
                <span class="sheet-val reimb-pos">+ {{ formatCurrency(reviewSlip.reimbursement_total) }}</span>
              </div>

              <!-- TDS -->
              <div class="sheet-row tds-row">
                <span class="sheet-label">
                  TDS
                  <span class="tds-inline" v-if="!isApproved">
                    @
                    <input
                      v-model.number="editForm.tds_percent"
                      type="number" min="0" max="100" step="0.5"
                      class="tds-input"
                      @input="recalc"
                    /> %
                  </span>
                  <span v-else>@ {{ reviewSlip.tds_percent }}%</span>
                </span>
                <span class="sheet-val tds-neg">− {{ formatCurrency(computedTds) }}</span>
              </div>

              <!-- Unpaid leave deduction -->
              <div class="sheet-row tds-row" v-if="reviewSlip.unpaid_leave_days > 0">
                <span class="sheet-label">Unpaid Leave ({{ reviewSlip.unpaid_leave_days }} day{{ reviewSlip.unpaid_leave_days !== 1 ? 's' : '' }})</span>
                <span class="sheet-val tds-neg">− {{ formatCurrency(reviewSlip.leave_deduction) }}</span>
              </div>

              <!-- Net -->
              <div class="sheet-row net-row">
                <span class="sheet-label">Net Pay</span>
                <span class="sheet-val net-val">{{ formatCurrency(computedNet) }}</span>
              </div>
            </div>

            <!-- Payout date -->
            <div class="payout-section">
              <label class="payout-label">Payout Date</label>
              <input
                v-model="editForm.payout_date"
                type="date"
                class="payout-input"
                :disabled="isApproved"
              />
              <p class="payout-hint" v-if="reviewSlip.payout_seventh_is_sunday && !isApproved">
                <span class="material-symbols-outlined">info</span>
                The 7th ({{ formatDate(reviewSlip.payout_seventh) }}) falls on a Sunday. Pick the working day:
                <button type="button" class="day-chip" @click="editForm.payout_date = reviewSlip.payout_before">
                  Friday ({{ formatDate(reviewSlip.payout_before) }})
                </button>
                <button type="button" class="day-chip" @click="editForm.payout_date = reviewSlip.payout_after">
                  Monday ({{ formatDate(reviewSlip.payout_after) }})
                </button>
              </p>
            </div>

            <div v-if="isApproved" class="approved-note">
              <span class="material-symbols-outlined">verified</span>
              Approved{{ reviewSlip.approved_at ? ' on ' + formatDate(reviewSlip.approved_at) : '' }}. This slip is locked.
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-cancel" @click="closeReview">Close</button>
            <button class="btn-submit-outline" :disabled="downloadingPdf" @click="downloadSlipPdf">
              <span class="material-symbols-outlined" style="font-size:16px;vertical-align:-3px;">download</span>
              {{ downloadingPdf ? 'Preparing…' : 'Download PDF' }}
            </button>
            <template v-if="!isApproved">
              <button class="btn-submit-outline" :disabled="saving" @click="saveChanges">
                {{ saving ? 'Saving…' : 'Save Changes' }}
              </button>
              <button class="btn-submit" :disabled="saving" @click="saveAndApprove">
                <span class="material-symbols-outlined">check_circle</span>
                Approve Slip
              </button>
            </template>
          </div>
        </div>
      </div>
    </Teleport>

    <ToastNotification v-if="toastMsg" :message="toastMsg" :type="toastType" @done="toastMsg = ''" />
  </AppLayout>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import ToastNotification from '../components/ToastNotification.vue'
import { salarySlipsAPI } from '../api/salarySlips'
import { usersAPI } from '../api/users'

const slips = ref([])
const employees = ref([])
const loading = ref(true)
const generating = ref(false)
const approvingMonth = ref(false)
const actionLoading = ref(null)

const filterMonth = ref('')
const filterEmployee = ref('')
const filterStatus = ref('')

const genMonth = ref('')

// ── Bulk selection ──
const selected = ref([])
const bulkTds = ref(null)
const bulkBusy = ref(false)

const reviewSlip = ref(null)
const saving = ref(false)
const downloadingPdf = ref(false)
const editForm = reactive({ tds_percent: 0, payout_date: '' })

const toastMsg = ref('')
const toastType = ref('success')
function toast(msg, type = 'success') { toastType.value = type; toastMsg.value = msg }

const inrFmt = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
function formatCurrency(v) { return inrFmt.format(Number(v) || 0) }

const monthNames = ['January','February','March','April','May','June','July','August','September','October','November','December']
function monthLabel(ms) {
  if (!ms) return ''
  const [y, m] = ms.split('-').map(Number)
  return `${monthNames[m - 1]} ${y}`
}
function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}
function formatStatus(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : '' }

async function fetchSlips() {
  loading.value = true
  try {
    const res = await salarySlipsAPI.getSlips()
    slips.value = res.data
  } catch (e) {
    toast('Failed to load salary slips', 'error')
  } finally {
    loading.value = false
  }
}

async function fetchEmployees() {
  try {
    const res = await usersAPI.getUsers()
    employees.value = res.data
  } catch (e) { /* ignore */ }
}

onMounted(() => { fetchSlips(); fetchEmployees() })

const filtered = computed(() => {
  let list = [...slips.value]
  if (filterMonth.value) list = list.filter(s => s.month === filterMonth.value)
  if (filterEmployee.value) list = list.filter(s => s.employee_id === Number(filterEmployee.value))
  if (filterStatus.value) list = list.filter(s => s.status === filterStatus.value)
  return list
})

const filteredNetTotal = computed(() => filtered.value.reduce((sum, s) => sum + (Number(s.net_total) || 0), 0))

const monthOptions = computed(() => {
  const set = new Set(slips.value.map(s => s.month))
  return [...set].sort().reverse()
})

const pendingInMonth = computed(() =>
  filterMonth.value ? slips.value.filter(s => s.month === filterMonth.value && s.status === 'pending').length : 0
)

// ── Bulk selection ──
const pendingFiltered = computed(() => filtered.value.filter(s => s.status === 'pending'))
const allPendingSelected = computed(() =>
  pendingFiltered.value.length > 0 && pendingFiltered.value.every(s => selected.value.includes(s.id))
)
const someSelected = computed(() => selected.value.length > 0 && !allPendingSelected.value)

function isSelected(id) { return selected.value.includes(id) }
function toggleOne(id) {
  if (selected.value.includes(id)) selected.value = selected.value.filter(x => x !== id)
  else selected.value = [...selected.value, id]
}
function toggleAll() {
  if (allPendingSelected.value) selected.value = []
  else selected.value = pendingFiltered.value.map(s => s.id)
}
function clearSelection() { selected.value = [] }

// Clear selection when filters change (selected rows may no longer be visible)
watch([filterMonth, filterEmployee, filterStatus], clearSelection)

async function handleBulkApprove() {
  if (!selected.value.length) return
  bulkBusy.value = true
  try {
    const ids = [...selected.value]
    const res = await salarySlipsAPI.approveBulk(ids)
    slips.value.forEach(s => { if (ids.includes(s.id)) s.status = 'approved' })
    toast(`Approved ${res.data.approved} slip(s).`)
    clearSelection()
  } catch (e) {
    toast('Failed to approve selected slips', 'error')
  } finally {
    bulkBusy.value = false
  }
}

async function handleBulkTds() {
  if (!selected.value.length || bulkTds.value === null || bulkTds.value === '') return
  bulkBusy.value = true
  try {
    const ids = [...selected.value]
    const res = await salarySlipsAPI.bulkSetTds(ids, Number(bulkTds.value))
    toast(`Updated TDS on ${res.data.updated} slip(s).`)
    bulkTds.value = null
    await fetchSlips()
  } catch (e) {
    toast('Failed to update TDS', 'error')
  } finally {
    bulkBusy.value = false
  }
}

// Last 13 months as YYYY-MM, for the explicit-generate picker
const genMonthOptions = computed(() => {
  const out = []
  const d = new Date()
  for (let i = 0; i < 13; i++) {
    const y = d.getFullYear()
    const m = d.getMonth() - i
    const dt = new Date(y, m, 1)
    out.push(`${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}`)
  }
  return out
})

async function handleGenerate() {
  generating.value = true
  try {
    const res = await salarySlipsAPI.generate(genMonth.value || null)
    const where = genMonth.value ? ` for ${monthLabel(genMonth.value)}` : ''
    toast(res.data.created > 0 ? `Generated ${res.data.created} new slip(s)${where}.` : `All slips are up to date${where}.`)
    if (genMonth.value) filterMonth.value = genMonth.value
    await fetchSlips()
  } catch (e) {
    toast('Failed to generate slips', 'error')
  } finally {
    generating.value = false
  }
}

async function handleApproveMonth() {
  approvingMonth.value = true
  try {
    const res = await salarySlipsAPI.approveMonth(filterMonth.value)
    toast(`Approved ${res.data.approved} slip(s) for ${monthLabel(filterMonth.value)}.`)
    await fetchSlips()
  } catch (e) {
    toast('Failed to approve slips', 'error')
  } finally {
    approvingMonth.value = false
  }
}

async function quickApprove(s) {
  actionLoading.value = s.id
  try {
    await salarySlipsAPI.approveSlip(s.id)
    const idx = slips.value.findIndex(x => x.id === s.id)
    if (idx !== -1) slips.value[idx].status = 'approved'
    selected.value = selected.value.filter(x => x !== s.id)
    toast('Slip approved.')
  } catch (e) {
    toast('Failed to approve slip', 'error')
  } finally {
    actionLoading.value = null
  }
}

async function openReview(s) {
  try {
    const res = await salarySlipsAPI.getSlip(s.id)
    reviewSlip.value = res.data
    editForm.tds_percent = res.data.tds_percent
    editForm.payout_date = res.data.payout_date
  } catch (e) {
    toast('Failed to load slip', 'error')
  }
}

function closeReview() { reviewSlip.value = null }

async function downloadSlipPdf() {
  if (!reviewSlip.value) return
  downloadingPdf.value = true
  try {
    const res = await salarySlipsAPI.downloadPdf(reviewSlip.value.id)
    const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `salary_slip_${reviewSlip.value.employee_name || reviewSlip.value.employee_id}_${reviewSlip.value.month}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    toast('Failed to download PDF', 'error')
  } finally {
    downloadingPdf.value = false
  }
}

const isApproved = computed(() => reviewSlip.value?.status === 'approved')

const computedTds = computed(() => {
  if (!reviewSlip.value) return 0
  return (Number(reviewSlip.value.base_salary) || 0) * (Number(editForm.tds_percent) || 0) / 100
})
const computedNet = computed(() => {
  if (!reviewSlip.value) return 0
  return (Number(reviewSlip.value.base_salary) || 0)
    - computedTds.value
    + (Number(reviewSlip.value.reimbursement_total) || 0)
    - (Number(reviewSlip.value.leave_deduction) || 0)
})
function recalc() { /* computeds react automatically */ }

async function persist() {
  const res = await salarySlipsAPI.updateSlip(reviewSlip.value.id, {
    tds_percent: Number(editForm.tds_percent) || 0,
    payout_date: editForm.payout_date || null,
  })
  return res.data
}

async function saveChanges() {
  saving.value = true
  try {
    const updated = await persist()
    syncRow(updated)
    reviewSlip.value = { ...reviewSlip.value, ...updated }
    toast('Slip updated.')
  } catch (e) {
    toast(e.response?.data?.detail || 'Failed to save', 'error')
  } finally {
    saving.value = false
  }
}

async function saveAndApprove() {
  saving.value = true
  try {
    await persist()
    const res = await salarySlipsAPI.approveSlip(reviewSlip.value.id)
    syncRow(res.data)
    toast('Slip approved.')
    reviewSlip.value = null
  } catch (e) {
    toast(e.response?.data?.detail || 'Failed to approve', 'error')
  } finally {
    saving.value = false
  }
}

function syncRow(updated) {
  const idx = slips.value.findIndex(x => x.id === updated.id)
  if (idx !== -1) slips.value[idx] = { ...slips.value[idx], ...updated }
}
</script>

<style scoped>
/* ── Page Header ── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 16px;
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
.page-subtitle { font-size: 13px; color: var(--color-on-surface-variant); margin: 0; max-width: 640px; }

.gen-group { display: flex; align-items: center; gap: 8px; }
.gen-select {
  padding: 9px 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  outline: none;
  cursor: pointer;
}
.gen-select:focus { border-color: var(--color-primary); }

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
  white-space: nowrap;
}
.btn-primary:hover:not(:disabled) { background: #1f5c5d; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
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
  gap: 12px;
}
.filter-bar-left { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.filter-select {
  padding: 8px 12px;
  background: var(--color-surface-dim);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  outline: none;
  cursor: pointer;
  transition: border var(--transition);
}
.filter-select:focus { border-color: var(--color-primary); background: var(--color-surface); }

.btn-approve-month {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: #ecfdf5;
  border: 1px solid #6ee7b7;
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 700;
  color: #047857;
  cursor: pointer;
  white-space: nowrap;
  transition: background var(--transition);
}
.btn-approve-month:hover:not(:disabled) { background: #d1fae5; }
.btn-approve-month:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-approve-month .material-symbols-outlined { font-size: 16px; }

/* ── Bulk Action Bar ── */
.bulk-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  background: var(--color-primary);
  border-radius: var(--radius-xl);
  padding: 12px 18px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-md);
}
.bulk-info {
  display: flex; align-items: center; gap: 8px;
  color: #fff; font-size: 14px; font-weight: 600;
}
.bulk-info .material-symbols-outlined { font-size: 20px; }
.bulk-clear {
  margin-left: 8px; padding: 4px 12px;
  background: rgba(255,255,255,0.18); color: #fff;
  border: none; border-radius: var(--radius-full);
  font-size: 12px; font-weight: 700; cursor: pointer;
  transition: background 0.15s;
}
.bulk-clear:hover { background: rgba(255,255,255,0.3); }
.bulk-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.bulk-tds { display: flex; align-items: center; gap: 6px; }
.bulk-tds-input {
  width: 90px; padding: 8px 10px;
  border: none; border-radius: var(--radius-md);
  font-size: 13px; font-variant-numeric: tabular-nums; outline: none;
}
.bulk-btn-outline {
  padding: 8px 14px; background: rgba(255,255,255,0.15); color: #fff;
  border: 1px solid rgba(255,255,255,0.5); border-radius: var(--radius-lg);
  font-size: 13px; font-weight: 600; cursor: pointer; transition: background 0.15s;
}
.bulk-btn-outline:hover:not(:disabled) { background: rgba(255,255,255,0.28); }
.bulk-btn-outline:disabled { opacity: 0.5; cursor: not-allowed; }
.bulk-btn-approve {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 18px; background: #fff; color: var(--color-primary);
  border: none; border-radius: var(--radius-lg);
  font-size: 13px; font-weight: 700; cursor: pointer; transition: opacity 0.15s;
}
.bulk-btn-approve:hover:not(:disabled) { opacity: 0.88; }
.bulk-btn-approve:disabled { opacity: 0.6; cursor: not-allowed; }
.bulk-btn-approve .material-symbols-outlined { font-size: 17px; }

.bulk-slide-enter-active, .bulk-slide-leave-active { transition: opacity 0.18s, transform 0.18s; }
.bulk-slide-enter-from, .bulk-slide-leave-to { opacity: 0; transform: translateY(-8px); }

/* ── Checkboxes ── */
.col-check { width: 44px; text-align: center; }
.row-check { width: 16px; height: 16px; accent-color: var(--color-primary); cursor: pointer; }
.check-locked { font-size: 15px; color: var(--color-outline); opacity: 0.6; }

/* ── Table Card ── */
.table-card {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}
.data-table { width: 100%; border-collapse: collapse; }
.data-table thead { background: #f8fafc; }
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
  white-space: nowrap;
}
.data-table td {
  padding: 12px 16px;
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}
.data-row { cursor: pointer; }
.data-row:last-child td { border-bottom: none; }
.data-row:hover { background: #fafbfc; }
.data-row.is-selected { background: var(--color-primary-light); }
.data-row.is-selected:hover { background: var(--color-primary-light); }
.col-right { text-align: right; }
.col-actions { width: 90px; text-align: center; }

.row-name { font-weight: 600; }
.cell-muted { color: var(--color-on-surface-variant); }
.cell-mono { font-variant-numeric: tabular-nums; }
.cell-amount { font-weight: 700; color: var(--color-primary); }
.reimb-pos { color: #047857; font-weight: 600; }
.tds-neg { color: #b45309; }

/* ── Badges ── */
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

/* ── Row Actions ── */
.row-actions { display: flex; justify-content: center; gap: 6px; }
.icon-btn {
  width: 30px; height: 30px;
  display: inline-flex; align-items: center; justify-content: center;
  background: none;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition);
}
.icon-btn .material-symbols-outlined { font-size: 16px; }
.icon-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.icon-btn-edit .material-symbols-outlined { color: var(--color-primary); }
.icon-btn-edit:hover { background: var(--color-primary-light); border-color: var(--color-primary); }
.icon-btn-approve .material-symbols-outlined { color: #16a34a; }
.icon-btn-approve:hover:not(:disabled) { background: #dcfce7; border-color: #86efac; }

/* ── Empty State ── */
.empty-cell { text-align: center; padding: 0; }
.empty-state {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 48px 16px; color: var(--color-on-surface-variant);
}
.empty-icon { font-size: 36px; opacity: 0.4; }
.empty-state p { margin: 0; font-size: 13px; max-width: 360px; }

/* ── Table Footer ── */
.table-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; background: #f8fafc; border-top: 1px solid var(--color-outline);
}
.page-info { font-family: var(--font-body); font-size: 13px; color: var(--color-on-surface-variant); }

/* ── Modal ── */
.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000; padding: 16px;
}
.modal {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.14);
  max-width: 520px; width: 100%;
  max-height: 92vh; overflow-y: auto;
  display: flex; flex-direction: column;
}
.modal-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: 24px 24px 20px; border-bottom: 1px solid var(--color-outline);
}
.modal-title { font-family: var(--font-display); font-size: 18px; font-weight: 700; color: var(--color-on-surface); margin: 0 0 2px; }
.modal-subtitle { font-size: 13px; color: var(--color-on-surface-variant); margin: 0; }
.modal-close {
  width: 32px; height: 32px;
  display: inline-flex; align-items: center; justify-content: center;
  background: none; border: 1px solid var(--color-outline);
  border-radius: var(--radius-md); cursor: pointer; flex-shrink: 0;
}
.modal-close:hover { background: var(--color-outline-variant); }
.modal-close .material-symbols-outlined { font-size: 18px; color: var(--color-on-surface-variant); }
.modal-body { padding: 24px; flex: 1; }

/* ── Payslip Sheet ── */
.slip-sheet {
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  overflow: hidden;
}
.sheet-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f1f5f9;
}
.sheet-row.sub { background: #fafbfc; padding: 9px 16px; }
.sheet-label { font-size: 13px; color: var(--color-on-surface); display: flex; align-items: center; gap: 6px; }
.sheet-val { font-size: 14px; font-weight: 600; color: var(--color-on-surface); font-variant-numeric: tabular-nums; }

.sheet-subsection { padding: 12px 16px; border-bottom: 1px solid #f1f5f9; background: #fafbfc; }
.sheet-sub-label {
  font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
  color: var(--color-on-surface-variant); margin-bottom: 8px;
}
.sheet-reimb-row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 13px; }
.reimb-reason { color: var(--color-on-surface-variant); }
.reimb-amt { color: #047857; font-weight: 600; font-variant-numeric: tabular-nums; }

.tds-row { background: #fffbeb; }
.tds-inline { display: inline-flex; align-items: center; gap: 4px; color: var(--color-on-surface-variant); font-size: 12px; }
.tds-input {
  width: 56px; padding: 4px 6px;
  border: 1px solid var(--color-outline); border-radius: var(--radius-md);
  font-size: 13px; text-align: center; font-variant-numeric: tabular-nums;
}
.tds-input:focus { outline: none; border-color: var(--color-primary); }

.net-row { background: var(--color-primary); border-bottom: none; }
.net-row .sheet-label { color: rgba(255,255,255,0.85); font-weight: 700; }
.net-val { color: #fff; font-size: 18px; font-weight: 800; }

/* ── Payout ── */
.payout-section { margin-top: 20px; }
.payout-label {
  display: block; font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--color-on-surface-variant); margin-bottom: 6px;
}
.payout-input {
  padding: 9px 12px; border: 1px solid var(--color-outline);
  border-radius: var(--radius-md); font-family: var(--font-body); font-size: 14px;
  color: var(--color-on-surface); background: #fff; outline: none;
}
.payout-input:focus { border-color: var(--color-primary); }
.payout-input:disabled { background: var(--color-surface-dim); cursor: not-allowed; }
.payout-hint {
  display: flex; align-items: center; flex-wrap: wrap; gap: 8px;
  margin: 10px 0 0; font-size: 12px; color: #92400e;
  background: #fffbeb; border: 1px solid #fde68a; border-radius: var(--radius-md); padding: 10px 12px;
}
.payout-hint .material-symbols-outlined { font-size: 16px; }
.day-chip {
  padding: 4px 10px; background: #fff; border: 1px solid #d97706; color: #b45309;
  border-radius: var(--radius-full); font-size: 12px; font-weight: 700; cursor: pointer;
}
.day-chip:hover { background: #fef3c7; }

.approved-note {
  display: flex; align-items: center; gap: 8px;
  margin-top: 18px; padding: 12px 14px;
  background: #ecfdf5; border: 1px solid #6ee7b7; border-radius: var(--radius-md);
  font-size: 13px; color: #047857;
}
.approved-note .material-symbols-outlined { font-size: 18px; }

/* ── Footer ── */
.modal-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 16px 24px; border-top: 1px solid var(--color-outline);
  background: #f8fafc; border-radius: 0 0 var(--radius-xl) var(--radius-xl);
}
.btn-cancel {
  padding: 8px 16px; background: var(--color-surface);
  border: 1px solid var(--color-outline); border-radius: var(--radius-lg);
  font-size: 13px; color: var(--color-on-surface-variant); cursor: pointer;
}
.btn-cancel:hover { background: var(--color-outline-variant); }
.btn-submit-outline {
  padding: 9px 16px; background: var(--color-surface);
  border: 1px solid var(--color-primary); border-radius: var(--radius-lg);
  font-size: 13px; font-weight: 600; color: var(--color-primary); cursor: pointer;
}
.btn-submit-outline:hover:not(:disabled) { background: var(--color-primary-light); }
.btn-submit-outline:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-submit {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 9px 18px; background: var(--color-primary); color: #fff;
  border: none; border-radius: var(--radius-lg);
  font-size: 13px; font-weight: 600; cursor: pointer; transition: background var(--transition);
}
.btn-submit:hover:not(:disabled) { background: #1f5c5d; }
.btn-submit:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-submit .material-symbols-outlined { font-size: 17px; }

/* ── Spinner ── */
.spin-icon { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: 10px; }
  .gen-group { flex-wrap: wrap; }
  .gen-select { flex: 1; min-width: 140px; }
  .filter-bar { flex-direction: column; align-items: stretch; gap: 8px; }
  .filter-bar-left { flex-wrap: wrap; }
  .table-card { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .data-table { min-width: 780px; }
  .bulk-bar { flex-direction: column; align-items: stretch; gap: 10px; }
  .bulk-actions { flex-wrap: wrap; }
  .modal { max-width: 100%; width: 100%; }
  .modal-backdrop { padding: 8px; }
  .push-setting-grid { grid-template-columns: 1fr; }
}
</style>
