<template>
  <EmployeeLayout>
    <div class="leave-view">
      <div class="view-header">
        <h2 class="view-title">Leaves Management</h2>
      </div>

      <!-- KPI Cards -->
      <div class="kpi-grid">
        <div class="kpi-card highlight-card">
          <div class="kpi-label">Days Remaining</div>
          <div class="kpi-value">{{ leavesRemaining }}</div>
          <div class="kpi-subtext">Out of {{ leavesAllowed }} total</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Total Allowed</div>
          <div class="kpi-value">{{ leavesAllowed }}</div>
          <div class="kpi-subtext">Annual quota</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Total Used</div>
          <div class="kpi-value">{{ leavesUsed }}</div>
          <div class="kpi-subtext">Approved working days</div>
        </div>
      </div>

      <div class="content-grid">
        <!-- Left: Apply Form -->
        <div class="apply-panel">
          <h3 class="panel-title">Apply for Leave</h3>
          <form @submit.prevent="submitLeave" class="leave-form">
            <div class="form-row">
              <div class="form-group">
                <label>Start Date</label>
                <input type="date" v-model="form.start_date" required class="field-input" :min="todayDate">
              </div>
              <div class="form-group">
                <label>End Date</label>
                <input type="date" v-model="form.end_date" required class="field-input" :min="form.start_date || todayDate">
              </div>
            </div>

            <div class="calc-feedback" :class="{ 'text-error': hasInsufficientBalance }" v-if="calculatedDays > 0">
              <span class="material-symbols-outlined icon">calculate</span>
              <div class="feedback-text">
                <span v-if="hasInsufficientBalance">Insufficient balance</span>
                <span v-else>Duration calculation</span>
                <p>This request requires <strong>{{ calculatedDays }}</strong> working days.</p>
              </div>
            </div>

            <div class="form-group">
              <label>Reason *</label>
              <textarea v-model="form.reason" rows="3" required class="field-input" placeholder="Please provide a brief explanation..."></textarea>
            </div>

            <button type="submit" class="btn-submit" :disabled="submitting || hasInsufficientBalance || calculatedDays <= 0">
              {{ submitting ? 'Submitting Request...' : 'Submit Application' }}
            </button>
          </form>
        </div>

        <!-- Right: History -->
        <div class="history-panel">
          <h3 class="panel-title">Leave History</h3>
          
          <div v-if="loadingHistory" class="loading-state">
            <span class="material-symbols-outlined spinner">refresh</span>
            <p>Loading records...</p>
          </div>
          
          <div v-else-if="leaveHistory.length === 0" class="empty-state">
            <span class="material-symbols-outlined">event_busy</span>
            <p>No leave requests found in the system.</p>
          </div>
          
          <div v-else class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Date Range</th>
                  <th class="text-center">Days</th>
                  <th>Reason</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="leave in leaveHistory" :key="leave.id">
                  <td class="mono">{{ formatDateShort(leave.start_date) }} – {{ formatDateShort(leave.end_date) }}</td>
                  <td class="text-center mono">{{ countWorkingDays(leave.start_date, leave.end_date) }}</td>
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
  </EmployeeLayout>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import EmployeeLayout from '../../components/EmployeeLayout.vue'
import { countWorkingDays } from '../../stores/estimate'
import { usersAPI } from '../../api/users'
import { leavesAPI } from '../../api/leaves'

const currentUser = ref(null)
const leaveHistory = ref([])
const loadingHistory = ref(true)
const submitting = ref(false)

const todayDate = new Date().toISOString().split('T')[0]

const form = reactive({
  start_date: '',
  end_date: '',
  reason: ''
})

onMounted(async () => {
  await fetchUserData()
  await fetchLeaveHistory()
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

const leavesAllowed = computed(() => currentUser.value?.leaves_allowed || 0)

const leavesUsed = computed(() => {
  return leaveHistory.value
    .filter(l => l.status === 'approved')
    .reduce((total, l) => total + countWorkingDays(l.start_date, l.end_date), 0)
})

const leavesRemaining = computed(() => Math.max(0, leavesAllowed.value - leavesUsed.value))

const progressPercentage = computed(() => {
  if (leavesAllowed.value === 0) return 0
  return Math.min(100, (leavesRemaining.value / leavesAllowed.value) * 100)
})

const calculatedDays = computed(() => {
  if (!form.start_date || !form.end_date) return 0
  return countWorkingDays(form.start_date, form.end_date)
})

const hasInsufficientBalance = computed(() => calculatedDays.value > leavesRemaining.value)

const submitLeave = async () => {
  if (hasInsufficientBalance.value || calculatedDays.value <= 0) return

  submitting.value = true
  try {
    await leavesAPI.createLeave({
      start_date: form.start_date,
      end_date: form.end_date,
      reason: form.reason
    })
    alert('Leave applied successfully!')
    // Reset
    form.start_date = ''
    form.end_date = ''
    form.reason = ''
    await fetchLeaveHistory()
  } catch (err) {
    alert('Error applying for leave: ' + (err.response?.data?.detail || err.message))
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
  max-width: 1440px;
  margin: 0 auto;
}

.view-header {
  margin-bottom: 32px;
}

.view-title {
  font-family: 'Integral CF', sans-serif;
  font-size: 28px;
  font-weight: 700;
  color: var(--color-on-surface);
  margin: 0;
  letter-spacing: -0.02em;
}

/* KPIs */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}

@media (max-width: 1024px) {
  .kpi-grid { grid-template-columns: 1fr; }
}

.kpi-card {
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 24px;
  display: flex;
  flex-direction: column;
}

.kpi-card.highlight-card {
  border-color: var(--color-primary);
  background: var(--color-primary-container);
}

.kpi-label {
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
  letter-spacing: 0.05em;
  margin-bottom: 8px;
}

.kpi-card.highlight-card .kpi-label {
  color: var(--color-on-primary-container);
}

.kpi-value {
  font-family: 'Integral CF', sans-serif;
  font-size: 36px;
  font-weight: 700;
  color: var(--color-on-surface);
  line-height: 1;
  margin-bottom: 8px;
}

.kpi-card.highlight-card .kpi-value {
  color: var(--color-primary);
}

.kpi-subtext {
  font-size: 13px;
  color: var(--color-outline);
}

/* Layout */
.content-grid {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 32px;
}

@media (max-width: 1024px) {
  .content-grid { grid-template-columns: 1fr; }
}

.panel-title {
  font-family: 'Integral CF', sans-serif;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-on-surface);
  margin: 0 0 24px 0;
  letter-spacing: -0.01em;
}

/* Apply Panel */
.apply-panel {
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 24px;
  height: max-content;
}

.leave-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-on-surface-variant);
}

.field-input {
  width: 100%;
  height: 44px;
  padding: 0 12px;
  border-radius: 4px;
  border: 1px solid #cbd5e1;
  font-family: var(--font-body);
  font-size: 14px;
  background: var(--color-surface);
  outline: none;
  box-sizing: border-box;
  transition: all 0.2s;
}

textarea.field-input {
  height: auto;
  padding: 12px;
  resize: vertical;
}

.field-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(40, 116, 117, 0.1);
}

.calc-feedback {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: var(--color-surface-container);
  border-radius: 4px;
  border: 1px solid var(--color-outline-variant);
}
.calc-feedback.text-error {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #991b1b;
}

.calc-feedback .icon {
  font-size: 20px;
  margin-top: 2px;
  color: var(--color-on-surface-variant);
}
.calc-feedback.text-error .icon {
  color: #dc2626;
}

.feedback-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.feedback-text span {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
}
.calc-feedback.text-error .feedback-text span {
  color: #991b1b;
}
.feedback-text p {
  margin: 0;
  font-size: 14px;
  color: var(--color-on-surface);
}

.btn-submit {
  height: 44px;
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-family: var(--font-body);
  font-weight: 600;
  font-size: 14px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
  margin-top: 8px;
}
.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn-submit:hover:not(:disabled) {
  background: #1a4e4f;
}

/* History Panel */
.history-panel {
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 24px;
}

.loading-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 0;
  color: var(--color-on-surface-variant);
}

.loading-state p, .empty-state p {
  margin: 16px 0 0 0;
  font-size: 14px;
}

.empty-state .material-symbols-outlined {
  font-size: 40px;
  color: var(--color-outline);
}

.table-container {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
  border-bottom: 2px solid var(--color-outline-variant);
  letter-spacing: 0.05em;
}

.data-table td {
  padding: 16px;
  font-size: 14px;
  color: var(--color-on-surface);
  border-bottom: 1px solid var(--color-outline-variant);
}

.data-table th.text-center, .data-table td.text-center {
  text-align: center;
}

.mono {
  font-family: var(--font-body);
  font-variant-numeric: tabular-nums;
}

.reason-cell {
  max-width: 280px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 2px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.status-badge.pending { background: #fef3c7; color: #b45309; }
.status-badge.approved { background: #ecfdf5; color: #059669; }
.status-badge.rejected { background: #fef2f2; color: #dc2626; }

@keyframes spin { 100% { transform: rotate(360deg); } }
.spinner { animation: spin 1s linear infinite; font-size: 24px; }
</style>
