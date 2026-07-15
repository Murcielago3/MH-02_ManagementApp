<template>
  <EmployeeLayout>
    <div class="leave-view">

      <!-- KPI Cards -->
      <div class="kpi-grid">
        <div class="kpi-card highlight">
          <div class="kpi-icon-wrap">
            <span class="material-symbols-outlined">event_available</span>
          </div>
          <div class="kpi-body">
            <span class="kpi-value">{{ paidLeaveBalance }}</span>
            <span class="kpi-label">Paid Leave Balance</span>
            <span class="kpi-sub">+1.5 days added each month</span>
          </div>
        </div>
        <div class="kpi-card" :class="{ 'probation-card': onProbation }">
          <div class="kpi-icon-wrap" :class="{ warn: onProbation }">
            <span class="material-symbols-outlined">{{ onProbation ? 'hourglass_top' : 'verified' }}</span>
          </div>
          <div class="kpi-body">
            <span class="kpi-value" style="font-size:18px;">{{ onProbation ? 'On Probation' : 'Confirmed' }}</span>
            <span class="kpi-label">Status</span>
            <span class="kpi-sub">{{ onProbation ? `All leaves unpaid until ${probationEndLabel}` : 'Paid leaves apply' }}</span>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon-wrap warn">
            <span class="material-symbols-outlined">money_off</span>
          </div>
          <div class="kpi-body">
            <span class="kpi-value">{{ unpaidDaysTaken }}</span>
            <span class="kpi-label">Unpaid Days Taken</span>
            <span class="kpi-sub">Deducted from salary</span>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon-wrap">
            <span class="material-symbols-outlined">bolt</span>
          </div>
          <div class="kpi-body">
            <span class="kpi-value">{{ overtimeAvailable }}</span>
            <span class="kpi-label">Overtime Leave</span>
            <span class="kpi-sub">{{ overtimeSub }}</span>
          </div>
        </div>
      </div>

      <!-- Content grid -->
      <div class="content-grid">
        <!-- Apply panel -->
        <div class="panel apply-panel">
          <div class="panel-header">
            <h3 class="panel-title">Apply for Leave</h3>
            <span class="panel-hint">Backdated requests accepted up to 1 month.</span>
          </div>
          <div class="panel-body">
            <form @submit.prevent="submitLeave" class="leave-form">
              <div class="form-row">
                <div class="form-group">
                  <label>Start Date</label>
                  <input type="date" v-model="form.start_date" required class="field-input" :min="minLeaveDate" />
                </div>
                <div class="form-group">
                  <label>End Date</label>
                  <input type="date" v-model="form.end_date" required class="field-input" :min="form.start_date || minLeaveDate" />
                </div>
              </div>

              <div
                v-if="calculatedDays > 0"
                class="calc-feedback"
                :class="{ warn: estimatedUnpaid > 0 }"
              >
                <span class="material-symbols-outlined feedback-icon">
                  {{ estimatedUnpaid > 0 ? 'info' : 'calculate' }}
                </span>
                <div class="feedback-text">
                  <span class="feedback-title">
                    {{ estimatedUnpaid > 0 ? 'Some days will be unpaid' : 'Duration estimate' }}
                  </span>
                  <p>
                    This request covers <strong>{{ calculatedDays }}</strong> working day{{ calculatedDays !== 1 ? 's' : '' }}.
                    <template v-if="estimatedUnpaid > 0">
                      <br><strong>{{ estimatedPaid }}</strong> paid, <strong>{{ estimatedUnpaid }}</strong> unpaid
                      ({{ onProbation ? 'probation period' : 'balance exhausted' }}) — unpaid days are deducted from salary.
                    </template>
                  </p>
                </div>
              </div>

              <div class="form-group">
                <label>Reason <span class="required">*</span></label>
                <textarea
                  v-model="form.reason"
                  rows="4"
                  required
                  class="field-input"
                  placeholder="Please provide a brief explanation…"
                ></textarea>
              </div>

              <button
                type="submit"
                class="btn-submit"
                :disabled="submitting || calculatedDays <= 0"
              >
                <span v-if="submitting" class="material-symbols-outlined btn-spinner">refresh</span>
                {{ submitting ? 'Submitting…' : 'Submit Application' }}
              </button>
            </form>
          </div>
        </div>

        <!-- History panel -->
        <div class="panel history-panel">
          <div class="panel-header">
            <h3 class="panel-title">Leave History</h3>
            <span class="record-count" v-if="leaveHistory.length">{{ leaveHistory.length }} records</span>
          </div>
          <div class="panel-body no-pad">
            <div v-if="loadingHistory" class="loading-state">
              <span class="material-symbols-outlined spinner">refresh</span>
              <p>Loading records…</p>
            </div>
            <div v-else-if="leaveHistory.length === 0" class="empty-state">
              <span class="material-symbols-outlined">event_busy</span>
              <p>No leave requests found.</p>
            </div>
            <div v-else class="table-wrap">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Date Range</th>
                    <th class="center">Days</th>
                    <th class="center">Paid</th>
                    <th class="center">Unpaid</th>
                    <th>Reason</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="leave in leaveHistory" :key="leave.id">
                    <td class="mono">{{ formatDateShort(leave.start_date) }} – {{ formatDateShort(leave.end_date) }}</td>
                    <td class="center mono">{{ countWorkingDays(leave.start_date, leave.end_date) }}</td>
                    <td class="center mono">{{ leave.status === 'approved' ? leave.paid_days : '—' }}</td>
                    <td class="center mono">
                      <span :class="{ 'unpaid-flag': leave.status === 'approved' && leave.unpaid_days > 0 }">
                        {{ leave.status === 'approved' ? leave.unpaid_days : '—' }}
                      </span>
                    </td>
                    <td class="reason-cell" :title="leave.reason">{{ leave.reason || '—' }}</td>
                    <td>
                      <span class="status-badge" :class="leave.status">
                        {{ formatStatus(leave.status) }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Info notice -->
      <div class="info-notice">
        <span class="material-symbols-outlined">info</span>
        <p>Leave requests require manager approval. Contact HR if you need to adjust an approved leave.</p>
      </div>

    </div>
  </EmployeeLayout>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import EmployeeLayout from '../../components/EmployeeLayout.vue'
import { countWorkingDays } from '../../stores/estimate'
import { usersAPI } from '../../api/users'
import { leavesAPI } from '../../api/leaves'
import { notifySuccess } from '../../stores/notifier'

const currentUser = ref(null)
const leaveHistory = ref([])
const loadingHistory = ref(true)
const submitting = ref(false)
const overtime = ref({ available: 0, credits: [] })

const todayDate = new Date().toISOString().split('T')[0]

// Employees can backdate leaves up to one month — for emergencies or forgotten
// applications. Anything older has to be filed by an admin.
const minLeaveDate = (() => {
  const d = new Date()
  d.setMonth(d.getMonth() - 1)
  return d.toISOString().split('T')[0]
})()

const form = reactive({
  start_date: '',
  end_date: '',
  reason: ''
})

onMounted(async () => {
  await fetchUserData()
  await Promise.all([fetchLeaveHistory(), fetchOvertime()])
})

const fetchOvertime = async () => {
  try {
    overtime.value = (await leavesAPI.getMyOvertime()).data || { available: 0, credits: [] }
  } catch (e) {
    console.error(e)
  }
}

function fmtDate(s) {
  return s ? new Date(s).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) : ''
}
const overtimeAvailable = computed(() => Number(overtime.value?.available || 0))
// Backend returns credits soonest-expiry first.
const overtimeSub = computed(() => {
  const cs = overtime.value?.credits || []
  if (overtimeAvailable.value > 0 && cs.length) {
    return `Soonest expires ${fmtDate(cs[0].expires_on)}`
  }
  return '½ day per 11h+ day · 1 day per 13h+'
})

const fetchUserData = async () => {
  try {
    const res = await usersAPI.getMe()
    currentUser.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const fetchLeaveHistory = async () => {
  loadingHistory.value = true
  try {
    const res = await leavesAPI.getMyLeaves()
    // Sort descending by start date
    leaveHistory.value = res.data.sort((a, b) => new Date(b.start_date) - new Date(a.start_date))
  } catch (e) {
    console.error(e)
  } finally {
    loadingHistory.value = false
  }
}

const paidLeaveBalance = computed(() => Number(currentUser.value?.paid_leave_balance || 0))

const unpaidDaysTaken = computed(() => {
  return leaveHistory.value
    .filter(l => l.status === 'approved')
    .reduce((total, l) => total + (Number(l.unpaid_days) || 0), 0)
})

// Probation = 3 months from joining date
const probationEndDate = computed(() => {
  const j = currentUser.value?.joining_date
  if (!j) return null
  const d = new Date(j)
  d.setMonth(d.getMonth() + 3)
  return d
})
const onProbation = computed(() => probationEndDate.value && new Date() < probationEndDate.value)
const probationEndLabel = computed(() =>
  probationEndDate.value ? probationEndDate.value.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : ''
)

const calculatedDays = computed(() => {
  if (!form.start_date || !form.end_date) return 0
  return countWorkingDays(form.start_date, form.end_date)
})

// Estimated paid/unpaid split for the request being composed. Overtime credits
// pay even during probation; the regular balance only applies post-probation.
const estimatedPaid = computed(() => {
  const capacity = overtimeAvailable.value + (onProbation.value ? 0 : paidLeaveBalance.value)
  return Math.min(calculatedDays.value, Math.floor(capacity))
})
const estimatedUnpaid = computed(() => Math.max(0, calculatedDays.value - estimatedPaid.value))

const submitLeave = async () => {
  if (calculatedDays.value <= 0) return

  submitting.value = true
  try {
    await leavesAPI.createLeave({
      start_date: form.start_date,
      end_date: form.end_date,
      reason: form.reason
    })
    notifySuccess('Leave request submitted.')
    // Reset
    form.start_date = ''
    form.end_date = ''
    form.reason = ''
    await fetchLeaveHistory()
  } catch (err) {
    console.error(err)
  } finally {
    submitting.value = false
  }
}

// Formatters
const formatDateShort = (d) => {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
}

const formatStatus = (s) => {
  if (!s) return ''
  return s.charAt(0).toUpperCase() + s.slice(1)
}
</script>

<style scoped>
.leave-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ── KPI Grid ── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
@media (max-width: 768px) {
  .kpi-grid { grid-template-columns: 1fr; }
}

.kpi-card {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow-sm);
}
.kpi-card.highlight {
  background: var(--color-primary-light);
  border-color: var(--color-primary);
}

.kpi-icon-wrap {
  width: 44px; height: 44px;
  border-radius: var(--radius-md);
  background: var(--color-surface-dim);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.kpi-icon-wrap .material-symbols-outlined { font-size: 22px; color: var(--color-on-surface-variant); }
.kpi-card.highlight .kpi-icon-wrap {
  background: rgba(40,116,117,0.15);
}
.kpi-card.highlight .kpi-icon-wrap .material-symbols-outlined { color: var(--color-primary); }
.kpi-icon-wrap.warn .material-symbols-outlined { color: #d97706; }

.kpi-body { display: flex; flex-direction: column; gap: 2px; }
.kpi-value {
  font-family: var(--font-display);
  font-size: 28px; font-weight: 700; line-height: 1;
  color: var(--color-on-surface);
}
.kpi-card.highlight .kpi-value { color: var(--color-primary); }
.kpi-label {
  font-size: 13px; font-weight: 600;
  color: var(--color-on-surface);
}
.kpi-sub {
  font-size: 11px;
  color: var(--color-on-surface-variant);
}

/* ── Content Grid ── */
.content-grid {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 20px;
  align-items: start;
}
@media (max-width: 1024px) {
  .content-grid { grid-template-columns: 1fr; }
}

/* ── Panel ── */
.panel {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-outline);
  background: var(--color-surface-dim);
}
.panel-title {
  font-family: var(--font-display);
  font-size: 14px; font-weight: 700;
  color: var(--color-on-surface);
  margin: 0;
  text-transform: uppercase; letter-spacing: 0.06em;
}
.panel-hint {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-on-surface-variant);
  font-style: italic;
}
.record-count {
  font-size: 11px; font-weight: 600;
  color: var(--color-on-surface-variant);
  background: var(--color-background);
  border: 1px solid var(--color-outline);
  padding: 2px 8px;
  border-radius: var(--radius-full);
}
.panel-body { padding: 20px; }
.panel-body.no-pad { padding: 0; }

/* ── Leave form ── */
.leave-form { display: flex; flex-direction: column; gap: 16px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label {
  font-size: 12px; font-weight: 700;
  color: var(--color-on-surface-variant);
  text-transform: uppercase; letter-spacing: 0.04em;
}
.required { color: var(--color-error); }
.field-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-family: var(--font-body); font-size: 14px;
  color: var(--color-on-surface);
  background: var(--color-surface);
  box-sizing: border-box;
  transition: border-color var(--transition);
  outline: none;
}
textarea.field-input { resize: vertical; }
.field-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(40,116,117,.10);
}

.calc-feedback {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 14px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: var(--radius-md);
}
.calc-feedback.error {
  background: #fef2f2;
  border-color: #fca5a5;
}
.calc-feedback.warn {
  background: #fffbeb;
  border-color: #fde68a;
}
.calc-feedback.warn .feedback-icon { color: #d97706; }
.calc-feedback.warn .feedback-title { color: #b45309; }
.kpi-card.probation-card { background: #fffbeb; border-color: #fde68a; }
.unpaid-flag { color: #b45309; font-weight: 700; }
.feedback-icon {
  font-size: 18px; flex-shrink: 0; margin-top: 1px;
  color: #16a34a;
}
.calc-feedback.error .feedback-icon { color: var(--color-error); }
.feedback-text { display: flex; flex-direction: column; gap: 3px; }
.feedback-title {
  font-size: 12px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.04em;
  color: #15803d;
}
.calc-feedback.error .feedback-title { color: #b91c1c; }
.feedback-text p { margin: 0; font-size: 13.5px; color: var(--color-on-surface); }

.btn-submit {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  height: 44px;
  background: var(--color-primary); color: #fff;
  font-family: var(--font-body); font-weight: 600; font-size: 14px;
  border: none; border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition);
}
.btn-submit:hover:not(:disabled) { background: #1a5657; }
.btn-submit:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-spinner { font-size: 18px; animation: spin 1s linear infinite; }

/* ── History table ── */
.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 11px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.05em;
  color: var(--color-on-surface-variant);
  border-bottom: 1px solid var(--color-outline);
  background: var(--color-surface-dim);
}
.data-table th.center, .data-table td.center { text-align: center; }
.data-table td {
  padding: 14px 16px;
  font-size: 13.5px;
  color: var(--color-on-surface);
  border-bottom: 1px solid var(--color-outline);
}
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: var(--color-surface-dim); }

.mono { font-variant-numeric: tabular-nums; }
.reason-cell {
  max-width: 260px; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis;
}

.status-badge {
  display: inline-block;
  padding: 3px 9px;
  border-radius: var(--radius-full);
  font-size: 11px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.04em;
}
.status-badge.pending { background: #fef3c7; color: #b45309; }
.status-badge.approved { background: #dcfce7; color: #15803d; }
.status-badge.rejected { background: #fee2e2; color: #dc2626; }

/* ── States ── */
.loading-state, .empty-state {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 56px 0;
  gap: 12px;
  color: var(--color-on-surface-variant);
}
.loading-state p, .empty-state p { margin: 0; font-size: 14px; }
.empty-state .material-symbols-outlined { font-size: 36px; color: var(--color-outline); }

/* ── Info notice ── */
.info-notice {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 14px 18px;
  background: var(--color-surface-dim);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
}
.info-notice .material-symbols-outlined { font-size: 18px; color: var(--color-primary); flex-shrink: 0; margin-top: 1px; }
.info-notice p { margin: 0; font-size: 13px; color: var(--color-on-surface-variant); line-height: 1.5; }

@keyframes spin { 100% { transform: rotate(360deg); } }
.spinner { font-size: 24px; animation: spin 1s linear infinite; color: var(--color-on-surface-variant); }

@media (max-width: 768px) {
  .kpi-grid { grid-template-columns: 1fr; }
  .content-grid { grid-template-columns: 1fr; }
  .form-row { grid-template-columns: 1fr; }
  .table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .data-table { min-width: 500px; }
}
</style>
